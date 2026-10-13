"""Run without Odoo: python -m unittest discover -s tests."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace

source = Path(__file__).resolve().parents[1] / 'mhj_account_reports/report/report_general_ledger.py'
module = ast.parse(source.read_text())
report = next(node for node in module.body if isinstance(node, ast.ClassDef))
methods = [node for node in report.body if isinstance(node, ast.FunctionDef) and node.name in (
    '_calculate_account_totals', '_get_initial_balances')]
namespace = {}
exec(compile(ast.Module(body=methods, type_ignores=[]), str(source), 'exec'), namespace)


class Currency:
    def __init__(self, identifier, name):
        self.id, self.name = identifier, name

    def is_zero(self, value):
        return abs(value) < 0.005


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.currencies = {1: Currency(1, 'EGP'), 2: Currency(2, 'USD')}
        self.context = {'show_currency': True, 'group_by_currency': True}
        currencies = SimpleNamespace(browse=self.currencies.__getitem__)
        self.env = type('Env', (), {
            'context': self.context,
            'company': SimpleNamespace(currency_id=self.currencies[1]),
            '__getitem__': lambda env, name: currencies,
        })()
        self.report = SimpleNamespace(env=self.env)
        self.account = SimpleNamespace(id=7, code='100', name='Cash')

    def line(self, debit, credit, amount, currency=2):
        return dict(debit=debit, credit=credit, amount_currency=amount,
                    currency_id=currency, balance=0)

    def totals(self, lines, display='all'):
        return namespace['_calculate_account_totals'](
            self.report, [self.account], {7: lines}, display)

    def test_opening_and_currency_credit_running_balance(self):
        lines = [self.line(5000, 0, 100), self.line(0, 1500, -30), self.line(200, 0, 200, 1)]
        result = self.totals(lines)[0]
        self.assertEqual(result['balance'], 3700)
        self.assertEqual(lines[1]['currency_credit'], 30)
        self.assertEqual(lines[1]['currency_balance'], 70)
        self.assertEqual(lines[1]['group_balance'], 3500)
        self.assertEqual(lines[2]['group_balance'], 200)
        self.assertEqual(len(result['currency_groups']), 2)

    def test_currency_residual_is_not_hidden(self):
        result = self.totals([self.line(100, 0, 10), self.line(0, 100, -8)], 'not_zero')
        self.assertEqual(result[0]['balance'], 0)
        self.assertEqual(result[0]['currency_groups'][0]['currency_balance'], 2)

    def test_opening_only_and_empty_accounts(self):
        result = self.totals([self.line(0, 500, -10)], 'movement')[0]
        self.assertEqual(result['balance'], -500)
        self.assertEqual(result['currency_groups'][0]['currency_balance'], -10)
        self.assertEqual(self.totals([], 'movement'), [])
        self.assertEqual(self.totals([])[0]['balance'], 0)

    def test_opening_query_preserves_filters_and_orm_joins(self):
        class MoveLine:
            def with_context(inner, context):
                self.assertEqual(context['date_from'], '2026-01-01')
                self.assertFalse(context['date_to'])
                self.assertTrue(context['initial_bal'])
                self.assertTrue(context['strict_range'])
                return inner

            def _query_get(inner):
                return ('account_move_line JOIN extra ON TRUE', 'account_move_line.date < %s', ['2026-01-01'])

        class Cursor:
            def execute(inner, sql, params):
                self.assertIn('JOIN extra ON TRUE', sql)
                self.assertIn('GROUP BY l.account_id, l.currency_id', sql)
                self.assertEqual(params, ('2026-01-01', (7,), '2026-01-01', '2026-01-01'))

            def dictfetchall(inner):
                return [dict(account_id=7, balance=500)]

        env = type('Env', (), {'context': dict(self.context, date_from='2026-01-01'),
                              'cr': Cursor(), '__getitem__': lambda env, name: MoveLine()})()
        lines = {7: []}
        namespace['_get_initial_balances'](SimpleNamespace(env=env), SimpleNamespace(ids=[7]), False, False, lines)
        self.assertEqual(lines[7][0]['balance'], 500)


if __name__ == '__main__':
    unittest.main()

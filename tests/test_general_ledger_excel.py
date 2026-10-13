"""Exercise the general ledger export layouts without an Odoo server."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace

source = Path(__file__).resolve().parents[1] / 'mhj_account_reports/report/report_excel.py'
module = ast.parse(source.read_text())
klass = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == 'GeneralLedgerXlsx')
method = next(node for node in klass.body if isinstance(node, ast.FunctionDef) and node.name == '_generate_general_ledger_xlsx')
namespace = {'XLSX_AVAILABLE': True}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), namespace)


class Sheet:
    def __init__(self):
        self.cells = {}
        self.merges = []

    def set_column(self, *args):
        pass

    def merge_range(self, *args):
        self.merges.append(args)

    def write(self, row, col, value, *_):
        self.cells[row, col] = value


class Workbook:
    def __init__(self):
        self.sheet = Sheet()

    def add_format(self, spec):
        return spec

    def add_worksheet(self, name):
        return self.sheet


class GeneralLedgerExcelTests(unittest.TestCase):
    def render(self, show_currency=False, group_by_currency=False):
        usd = SimpleNamespace(name='USD')
        egp = SimpleNamespace(name='EGP')
        opening = dict(ldate='2026-01-01', lcode='', partner_name='', move_name='Initial Balance',
                       lname='Initial Balance', debit=500, credit=0, balance=500, group_balance=500,
                       currency=usd, currency_debit=10, currency_credit=0, currency_balance=10,
                       is_initial_balance=True)
        sale = dict(ldate='2026-01-02', lcode='SAJ', partner_name='Customer', move_name='INV/1',
                    lname='Invoice', debit=0, credit=200, balance=300, group_balance=300,
                    currency=usd, currency_debit=0, currency_credit=4, currency_balance=6)
        egp_line = dict(ldate='2026-01-03', lcode='SAJ', partner_name='Customer', move_name='INV/2',
                        lname='Invoice', debit=100, credit=0, balance=400, group_balance=100,
                        currency=egp, currency_debit=100, currency_credit=0, currency_balance=100)
        lines = [opening, sale, egp_line]
        groups = [dict(currency=egp, move_lines=[egp_line], debit=100, credit=0, balance=100,
                       currency_debit=100, currency_credit=0, currency_balance=100),
                  dict(currency=usd, move_lines=[opening, sale], debit=500, credit=200, balance=300,
                       currency_debit=10, currency_credit=4, currency_balance=6)]
        data = {'form': {'show_currency': show_currency, 'group_by_currency': group_by_currency,
                         'initial_balance': True, 'target_move': 'posted'}}
        report_data = {'data': data['form'], 'Accounts': [dict(code='100', name='Cash',
                       debit=600, credit=200, balance=400, move_lines=lines, currency_groups=groups)]}
        report = SimpleNamespace(_get_report_values=lambda ids, data: report_data)
        env = type('Env', (), {'__getitem__': lambda self, name: report})()
        workbook = Workbook()
        namespace['_generate_general_ledger_xlsx'](SimpleNamespace(env=env), workbook,
                                                    data, SimpleNamespace(ids=[]))
        return workbook.sheet

    def test_company_currency_layout(self):
        sheet = self.render()
        self.assertEqual(sheet.merges[0][3], 7)
        self.assertFalse(any(col > 7 for row, col in sheet.cells))
        self.assertIn(400, [value for (row, col), value in sheet.cells.items() if col == 7])

    def test_optional_currency_columns(self):
        sheet = self.render(show_currency=True)
        self.assertEqual(sheet.merges[0][3], 11)
        self.assertIn('Currency Balance', sheet.cells.values())
        self.assertIn(6, [value for (row, col), value in sheet.cells.items() if col == 11])
        self.assertIn(4, [value for (row, col), value in sheet.cells.items() if col == 10])

    def test_grouped_currency_totals_and_balances(self):
        sheet = self.render(group_by_currency=True)
        self.assertIn('USD Total:', sheet.cells.values())
        self.assertIn('EGP Total:', sheet.cells.values())
        usd_rows = [row for (row, col), value in sheet.cells.items() if col == 4 and value == 'USD Total:']
        self.assertEqual(sheet.cells[usd_rows[0], 11], 6)
        egp_line_rows = [row for (row, col), value in sheet.cells.items() if col == 3 and value == 'INV/2']
        self.assertEqual(sheet.cells[egp_line_rows[0], 7], 100)


if __name__ == '__main__':
    unittest.main()

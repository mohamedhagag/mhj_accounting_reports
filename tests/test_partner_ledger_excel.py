"""Exercise both layouts without an Odoo server or XLSX dependency."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace

source = Path(__file__).resolve().parents[1] / 'mhj_account_reports/report/report_excel.py'
module = ast.parse(source.read_text())
klass = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == 'PartnerLedgerXlsx')
method = next(node for node in klass.body if isinstance(node, ast.FunctionDef) and node.name == '_generate_partner_ledger_xlsx')
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


class PartnerExcelTests(unittest.TestCase):
    def render(self, with_currency):
        currency = SimpleNamespace(name='USD')
        lines = [dict(date='2026-01-02', code='SAJ', a_name='Receivable', move_name='INV/1',
                      displayed_name='Invoice', debit=100.0, credit=0.0, progress=100.0,
                      currency_id=currency, amount_currency=25.0)]
        report_data = {
            'data': {'form': {'amount_currency': with_currency, 'target_move': 'posted'}},
            'docs': [SimpleNamespace(name='Customer')],
            'lines': lambda data, partner: lines,
            'sum_partner': lambda data, partner, field: 100.0 if field == 'debit' else 0.0,
        }
        report = SimpleNamespace(_get_report_values=lambda ids, data: report_data)
        env = type('Env', (), {'__getitem__': lambda self, name: report})()
        workbook = Workbook()
        namespace['_generate_partner_ledger_xlsx'](SimpleNamespace(env=env), workbook,
                                                    report_data['data'], SimpleNamespace(ids=[]))
        return workbook.sheet

    def test_currency_columns_show_signed_amount(self):
        sheet = self.render(True)
        self.assertEqual(sheet.merges[0][3], 9)
        self.assertIn('Amount in Currency', sheet.cells.values())
        self.assertIn('USD', sheet.cells.values())
        self.assertIn(25.0, [value for (row, col), value in sheet.cells.items() if col == 9])

    def test_currency_columns_hidden_when_option_off(self):
        sheet = self.render(False)
        self.assertEqual(sheet.merges[0][3], 7)
        self.assertNotIn('Amount in Currency', sheet.cells.values())
        self.assertFalse(any(col > 7 for row, col in sheet.cells))


if __name__ == '__main__':
    unittest.main()

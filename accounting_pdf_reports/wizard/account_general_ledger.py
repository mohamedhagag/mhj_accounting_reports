from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _name = "account.report.general.ledger"
    _inherit = "account.common.account.report"
    _description = "General Ledger Report"

    initial_balance = fields.Boolean(
        string='Include Initial Balances',
        help='If you selected date, this field allow you to add a row '
             'to display the amount of debit/credit/balance that precedes '
             'the filter you have set.'
    )
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by', required=True, default='sort_date'
    )
    journal_ids = fields.Many2many(
        'account.journal', 'account_report_general_ledger_journal_rel',
        'account_id', 'journal_id', string='Journals', required=True
    )

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        return records, data

    def _print_report(self, data):
        records, data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_general_ledger').with_context(landscape=True).report_action(records, data=data)

    def print_excel_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'initial_balance', 'sortby'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        records, data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_general_ledger_xlsx').report_action(records, data=data)

from odoo import fields, models, api


class AccountBalanceReport(models.TransientModel):
    _name = 'account.balance.report'
    _inherit = "account.common.account.report"
    _description = 'Trial Balance Report'

    journal_ids = fields.Many2many(
        'account.journal', 'account_balance_report_journal_rel',
        'account_id', 'journal_id',
        string='Journals', required=True, default=[]
    )
    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_trial_balance_analytic_rel', string='Analytic Accounts'
    )

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        return records, data

    def _print_report(self, data):
        records, data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_trial_balance').report_action(records, data=data)

    def print_excel_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'analytic_account_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        records, data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_trial_balance_xlsx').report_action(records, data=data)

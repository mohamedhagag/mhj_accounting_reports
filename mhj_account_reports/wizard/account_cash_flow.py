from odoo import models, api, fields
from datetime import date


class AccountCashFlowReport(models.TransientModel):
    _name = 'account.cash.flow.wizard'
    _inherit = "account.common.report"
    _description = 'Cash Flow Statement Report'

    date_from = fields.Date(
        string='Date From', required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1))
    )
    date_to = fields.Date(
        string='Date To', required=True,
        default=lambda self: fields.Date.to_string(date.today())
    )

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'company_id', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('mhj_account_reports.action_report_cash_flow').report_action(self, data=data)

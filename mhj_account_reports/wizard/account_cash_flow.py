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

    def _print_report(self, data):
        return self.env.ref('mhj_account_reports.action_report_cash_flow').report_action(self, data=data)

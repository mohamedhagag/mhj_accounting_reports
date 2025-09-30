from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"

    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on "
                                          "report if the currency differs from "
                                          "the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')
    initial_balance = fields.Boolean(
        string='Include Initial Balances',
        default=True,
        help='If you selected date, this field allow you to add a row '
             'to display the amount of debit/credit/balance that precedes '
             'the filter you have set.'
    )

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency,
                             'initial_balance': self.initial_balance})
        if self.initial_balance and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date to include Initial Balances"))
        return data

    def _print_report(self, data):
        data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_partnerledger').with_context(landscape=True).\
            report_action(self, data=data)

    def _print_excel_report(self, data):
        # Extend the base data with partner ledger specific fields
        data['form'].update(self.read(['result_selection', 'partner_ids', 'reconciled', 'amount_currency', 'initial_balance'])[0])
        data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_partnerledger_xlsx').report_action(self, data=data)

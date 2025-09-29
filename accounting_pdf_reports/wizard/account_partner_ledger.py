from odoo import fields, models, api, _


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"

    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on "
                                          "report if the currency differs from "
                                          "the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency})
        return data

    def _print_report(self, data):
        data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_partnerledger').with_context(landscape=True).\
            report_action(self, data=data)

    def print_excel_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'result_selection', 
                                 'partner_ids', 'reconciled', 'amount_currency'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        data = self._get_report_data(data)
        return self.env.ref('accounting_pdf_reports.action_report_partnerledger_xlsx').report_action(self, data=data)

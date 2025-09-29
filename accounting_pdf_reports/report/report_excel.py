from odoo import api, models, _
from odoo.exceptions import UserError

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    XLSX_AVAILABLE = True
except ImportError:
    ReportXlsx = object
    XLSX_AVAILABLE = False


class GeneralLedgerXlsx(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.general_ledger_xlsx'
    _description = 'General Ledger XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def create_xlsx_report(self, docids, data):
        """Main method called by Odoo's report_xlsx"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
        
        # Get documents (partners or objects)
        docs = self.env[data.get('model', 'res.partner')].browse(docids)
        return self.generate_xlsx_report(self.workbook, data, docs)

    def generate_xlsx_report(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))

        # Get report data using the existing report model
        report_obj = self.env['report.accounting_pdf_reports.report_general_ledger']
        report_data = report_obj._get_report_values(partners.ids, data)

        # Create worksheet
        worksheet = workbook.add_worksheet('General Ledger')

        # Define formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center',
            'bg_color': '#D3D3D3', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#E6E6FA', 'border': 1,
            'align': 'center', 'valign': 'vcenter'
        })
        account_format = workbook.add_format({
            'bold': True, 'bg_color': '#F0F8FF', 'border': 1,
            'font_size': 12
        })
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'align': 'right'
        })
        text_format = workbook.add_format({'border': 1, 'align': 'left'})

        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 20)  # Journal
        worksheet.set_column('C:C', 20)  # Partner
        worksheet.set_column('D:D', 30)  # Move
        worksheet.set_column('E:E', 40)  # Entry Label
        worksheet.set_column('F:F', 15)  # Debit
        worksheet.set_column('G:G', 15)  # Credit  
        worksheet.set_column('H:H', 15)  # Balance

        # Title
        worksheet.merge_range('A1:H1', 'General Ledger Report', title_format)

        # Report parameters
        row = 3
        form_data = report_data.get('data', {})
        date_from = form_data.get('date_from', '')
        date_to = form_data.get('date_to', '')
        target_move = form_data.get('target_move', 'posted')

        worksheet.write(row, 0, f'Date From: {date_from}', text_format)
        worksheet.write(row, 2, f'Date To: {date_to}', text_format)
        worksheet.write(row, 4, f'Target Moves: {target_move.title()}', text_format)
        row += 2

        # Process accounts
        accounts = report_data.get('Accounts', [])

        for account in accounts:
            # Account header
            account_name = f"{account.get('code', '')} - {account.get('name', '')}"
            worksheet.merge_range(row, 0, row, 7, account_name, account_format)
            row += 1

            # Column headers for move lines
            headers = ['Date', 'Journal', 'Partner', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Move lines
            move_lines = account.get('move_lines', [])
            account_debit = 0.0
            account_credit = 0.0

            for line in move_lines:
                worksheet.write(row, 0, line.get('ldate', ''), date_format)
                worksheet.write(row, 1, line.get('lcode', ''), text_format)
                worksheet.write(row, 2, line.get('partner_name', ''), text_format)
                worksheet.write(row, 3, line.get('move_name', ''), text_format)
                worksheet.write(row, 4, line.get('lname', ''), text_format)

                debit = line.get('debit', 0.0)
                credit = line.get('credit', 0.0)
                balance = line.get('balance', 0.0)

                worksheet.write(row, 5, debit, number_format)
                worksheet.write(row, 6, credit, number_format)
                worksheet.write(row, 7, balance, number_format)

                account_debit += debit
                account_credit += credit
                row += 1

            # Account totals
            total_format = workbook.add_format({
                'bold': True, 'bg_color': '#FFE4B5', 'border': 1,
                'num_format': '#,##0.00', 'align': 'right'
            })

            worksheet.write(row, 4, 'Account Total:', account_format)
            worksheet.write(row, 5, account_debit, total_format)
            worksheet.write(row, 6, account_credit, total_format)
            worksheet.write(row, 7, account_debit - account_credit, total_format)
            row += 2


class PartnerLedgerXlsx(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.partner_ledger_xlsx'
    _description = 'Partner Ledger XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def create_xlsx_report(self, docids, data):
        """Main method called by Odoo's report_xlsx"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
        
        # Get documents (partners or objects)
        docs = self.env[data.get('model', 'res.partner')].browse(docids)
        return self.generate_xlsx_report(self.workbook, data, docs)

    def generate_xlsx_report(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))

        # Get report data using the existing report model
        report_obj = self.env['report.accounting_pdf_reports.report_partnerledger']
        report_data = report_obj._get_report_values(partners.ids, data)

        # Create worksheet
        worksheet = workbook.add_worksheet('Partner Ledger')

        # Define formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center',
            'bg_color': '#D3D3D3', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#E6E6FA', 'border': 1,
            'align': 'center', 'valign': 'vcenter'
        })
        partner_format = workbook.add_format({
            'bold': True, 'bg_color': '#F0F8FF', 'border': 1,
            'font_size': 12
        })
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'align': 'right'
        })
        text_format = workbook.add_format({'border': 1, 'align': 'left'})

        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 15)  # Journal
        worksheet.set_column('C:C', 20)  # Account
        worksheet.set_column('D:D', 30)  # Move
        worksheet.set_column('E:E', 40)  # Entry Label
        worksheet.set_column('F:F', 15)  # Debit
        worksheet.set_column('G:G', 15)  # Credit  
        worksheet.set_column('H:H', 15)  # Balance
        worksheet.set_column('I:I', 15)  # Currency

        # Title
        worksheet.merge_range('A1:I1', 'Partner Ledger Report', title_format)

        # Report parameters
        row = 3
        form_data = report_data.get('data', {}).get('form', {})
        date_from = form_data.get('date_from', '')
        date_to = form_data.get('date_to', '')
        target_move = form_data.get('target_move', 'posted')

        worksheet.write(row, 0, f'Date From: {date_from}', text_format)
        worksheet.write(row, 2, f'Date To: {date_to}', text_format)
        worksheet.write(row, 4, f'Target Moves: {target_move.title()}', text_format)
        row += 2

        # Process partners
        partners = report_data.get('docs', [])
        lines_func = report_data.get('lines')
        sum_func = report_data.get('sum_partner')

        for partner in partners:
            # Partner header
            partner_name = partner.name or 'Unknown Partner'
            worksheet.merge_range(row, 0, row, 8, partner_name, partner_format)
            row += 1

            # Column headers for move lines
            headers = ['Date', 'Journal', 'Account', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Currency']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Get partner lines
            partner_lines = lines_func(report_data.get('data'), partner)
            partner_debit = sum_func(report_data.get('data'), partner, 'debit')
            partner_credit = sum_func(report_data.get('data'), partner, 'credit')

            for line in partner_lines:
                worksheet.write(row, 0, line.get('date', ''), date_format)
                worksheet.write(row, 1, line.get('code', ''), text_format)
                worksheet.write(row, 2, line.get('a_name', ''), text_format)
                worksheet.write(row, 3, line.get('move_name', ''), text_format)
                worksheet.write(row, 4, line.get('displayed_name', ''), text_format)

                debit = line.get('debit', 0.0)
                credit = line.get('credit', 0.0)
                balance = line.get('progress', 0.0)
                currency = line.get('currency_code', '')

                worksheet.write(row, 5, debit, number_format)
                worksheet.write(row, 6, credit, number_format)
                worksheet.write(row, 7, balance, number_format)
                worksheet.write(row, 8, currency, text_format)
                row += 1

            # Partner totals
            total_format = workbook.add_format({
                'bold': True, 'bg_color': '#FFE4B5', 'border': 1,
                'num_format': '#,##0.00', 'align': 'right'
            })

            worksheet.write(row, 4, 'Partner Total:', partner_format)
            worksheet.write(row, 5, partner_debit, total_format)
            worksheet.write(row, 6, partner_credit, total_format)
            worksheet.write(row, 7, partner_debit - partner_credit, total_format)
            row += 2


class TrialBalanceXlsx(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.trial_balance_xlsx'
    _description = 'Trial Balance XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def create_xlsx_report(self, docids, data):
        """Main method called by Odoo's report_xlsx"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
        
        # Get documents (partners or objects)
        docs = self.env[data.get('model', 'res.partner')].browse(docids)
        return self.generate_xlsx_report(self.workbook, data, docs)

    def generate_xlsx_report(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
            
        # Get report data using the existing report model
        report_obj = self.env['report.accounting_pdf_reports.report_trialbalance']
        report_data = report_obj._get_report_values(partners.ids, data)
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Trial Balance')
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center',
            'bg_color': '#D3D3D3', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#E6E6FA', 'border': 1,
            'align': 'center', 'valign': 'vcenter'
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'align': 'right'
        })
        text_format = workbook.add_format({'border': 1, 'align': 'left'})
        total_format = workbook.add_format({
            'bold': True, 'bg_color': '#FFE4B5', 'border': 1,
            'num_format': '#,##0.00', 'align': 'right'
        })
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Code
        worksheet.set_column('B:B', 40)  # Account Name
        worksheet.set_column('C:C', 15)  # Debit
        worksheet.set_column('D:D', 15)  # Credit  
        worksheet.set_column('E:E', 15)  # Balance
        
        # Title
        worksheet.merge_range('A1:E1', 'Trial Balance Report', title_format)
        
        # Report parameters
        row = 3
        form_data = report_data.get('data', {})
        date_from = form_data.get('date_from', '')
        date_to = form_data.get('date_to', '')
        target_move = form_data.get('target_move', 'posted')
        
        worksheet.write(row, 0, f'Date From: {date_from}', text_format)
        worksheet.write(row, 2, f'Date To: {date_to}', text_format)
        worksheet.write(row, 4, f'Target Moves: {target_move.title()}', text_format)
        row += 2
        
        # Column headers
        headers = ['Account Code', 'Account Name', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        row += 1
        
        # Process accounts
        accounts = report_data.get('Accounts', [])
        total_debit = 0.0
        total_credit = 0.0
        total_balance = 0.0
        
        for account in accounts:
            code = account.get('code', '')
            name = account.get('name', '')
            debit = account.get('debit', 0.0)
            credit = account.get('credit', 0.0)
            balance = account.get('balance', 0.0)
            
            worksheet.write(row, 0, code, text_format)
            worksheet.write(row, 1, name, text_format)
            worksheet.write(row, 2, debit, number_format)
            worksheet.write(row, 3, credit, number_format)
            worksheet.write(row, 4, balance, number_format)
            
            total_debit += debit
            total_credit += credit
            total_balance += balance
            row += 1
        
        # Total row
        worksheet.write(row, 0, '', text_format)
        worksheet.write(row, 1, 'TOTAL', total_format)
        worksheet.write(row, 2, total_debit, total_format)
        worksheet.write(row, 3, total_credit, total_format)
        worksheet.write(row, 4, total_balance, total_format)


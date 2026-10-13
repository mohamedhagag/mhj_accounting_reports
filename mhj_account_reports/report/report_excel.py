from odoo import api, models, _
from odoo.exceptions import UserError

try:
    from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract
    XLSX_AVAILABLE = True
except ImportError:
    ReportXlsx = object
    XLSX_AVAILABLE = False


class GeneralLedgerXlsx(models.AbstractModel):
    _name = 'report.mhj_account_reports.general_ledger_xlsx'
    _description = 'General Ledger XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def generate_xlsx_report(self, workbook, data, objects):
        """Main method called by Odoo's report_xlsx framework"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
        
        self._generate_general_ledger_xlsx(workbook, data, objects)

    def _generate_general_ledger_xlsx(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))

        # Get report data using the existing report model
        report_obj = self.env['report.mhj_account_reports.report_general_ledger']
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
        
        # Special format for initial balance lines
        init_balance_format = workbook.add_format({
            'bold': True, 'bg_color': '#FFF2CC', 'border': 1,
            'align': 'left', 'font_color': '#7F6000'
        })
        init_number_format = workbook.add_format({
            'bold': True, 'bg_color': '#FFF2CC', 'border': 1,
            'num_format': '#,##0.00', 'align': 'right', 'font_color': '#7F6000'
        })

        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 20)  # Journal
        worksheet.set_column('C:C', 20)  # Partner
        worksheet.set_column('D:D', 30)  # Move
        worksheet.set_column('E:E', 40)  # Entry Label
        worksheet.set_column('F:F', 15)  # Debit
        worksheet.set_column('G:G', 15)  # Credit  
        worksheet.set_column('H:H', 15)  # Balance

        # Report parameters
        row = 3
        form_data = report_data.get('data', {})
        group_by_currency = bool(form_data.get('group_by_currency'))
        show_currency = bool(form_data.get('show_currency') or group_by_currency)
        last_col = 11 if show_currency else 7
        if show_currency:
            worksheet.set_column('I:I', 15)  # Currency
            worksheet.set_column('J:L', 20)  # Currency amounts

        worksheet.merge_range(0, 0, 0, last_col, 'General Ledger Report', title_format)

        date_from = form_data.get('date_from', '')
        date_to = form_data.get('date_to', '')
        target_move = form_data.get('target_move', 'posted')
        initial_balance = form_data.get('initial_balance', False)

        worksheet.write(row, 0, f'Date From: {date_from}', text_format)
        worksheet.write(row, 2, f'Date To: {date_to}', text_format)
        worksheet.write(row, 4, f'Target Moves: {target_move.title()}', text_format)
        row += 1
        worksheet.write(row, 0, f'Include Initial Balance: {"Yes" if initial_balance else "No"}', text_format)
        if show_currency:
            worksheet.write(row, 2, 'Show Currency: Yes', text_format)
        if group_by_currency:
            worksheet.write(row, 4, 'Group by Currency: Yes', text_format)
        row += 2

        # Process accounts
        accounts = report_data.get('Accounts', [])

        for account in accounts:
            # Account header
            account_name = f"{account.get('code', '')} - {account.get('name', '')}"
            worksheet.merge_range(row, 0, row, last_col, account_name, account_format)
            row += 1

            # Column headers for move lines
            headers = ['Date', 'Journal', 'Partner', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance']
            if show_currency:
                headers += ['Currency', 'Currency Debit', 'Currency Credit', 'Currency Balance']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Move lines
            groups = (account.get('currency_groups', []) if group_by_currency else
                      [{'move_lines': account.get('move_lines', [])}])
            for group in groups:
                for line in group['move_lines']:
                    # Keep the opening row distinct within its currency group.
                    is_initial_balance = line.get('is_initial_balance', False)
                
                    line_text_format = init_balance_format if is_initial_balance else text_format
                    line_number_format = init_number_format if is_initial_balance else number_format
                    line_date_format = init_balance_format if is_initial_balance else date_format
                
                    worksheet.write(row, 0, line.get('ldate', ''), line_date_format)
                    worksheet.write(row, 1, line.get('lcode', ''), line_text_format)
                    worksheet.write(row, 2, line.get('partner_name', ''), line_text_format)
                    worksheet.write(row, 3, line.get('move_name', ''), line_text_format)
                    worksheet.write(row, 4, line.get('lname', ''), line_text_format)

                    debit = line.get('debit', 0.0)
                    credit = line.get('credit', 0.0)
                    balance = (line.get('group_balance', line.get('balance', 0.0))
                               if group_by_currency else line.get('balance', 0.0))

                    worksheet.write(row, 5, debit, line_number_format)
                    worksheet.write(row, 6, credit, line_number_format)
                    worksheet.write(row, 7, balance, line_number_format)
                    if show_currency:
                        worksheet.write(row, 8, line['currency'].name, line_text_format)
                        for col, key in ((9, 'currency_debit'), (10, 'currency_credit'),
                                         (11, 'currency_balance')):
                            worksheet.write(row, col, line[key], line_number_format)

                    row += 1

                if group_by_currency:
                    row = self._write_currency_totals(
                        worksheet, row, (group,), account_format, number_format)

            if show_currency and not group_by_currency:
                row = self._write_currency_totals(
                    worksheet, row, account.get('currency_groups', []),
                    account_format, number_format)

            # Account totals
            total_format = workbook.add_format({
                'bold': True, 'bg_color': '#FFE4B5', 'border': 1,
                'num_format': '#,##0.00', 'align': 'right'
            })

            worksheet.write(row, 4, 'Account Total:', account_format)
            worksheet.write(row, 5, account['debit'], total_format)
            worksheet.write(row, 6, account['credit'], total_format)
            worksheet.write(row, 7, account['balance'], total_format)
            row += 2

    def _write_currency_totals(self, worksheet, row, groups, label_format, number_format):
        """Write separate totals: amounts in different currencies cannot be added."""
        for group in groups:
            currency = group['currency']
            worksheet.write(row, 4, f'{currency.name} Total:', label_format)
            for col, key in ((5, 'debit'), (6, 'credit'), (7, 'balance'),
                             (9, 'currency_debit'), (10, 'currency_credit'),
                             (11, 'currency_balance')):
                worksheet.write(row, col, group[key], number_format)
            worksheet.write(row, 8, currency.name, label_format)
            row += 1
        return row


class PartnerLedgerXlsx(models.AbstractModel):
    _name = 'report.mhj_account_reports.partner_ledger_xlsx'
    _description = 'Partner Ledger XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []

    def generate_xlsx_report(self, workbook, data, objects):
        """Main method called by Odoo's report_xlsx framework"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))

        self._generate_partner_ledger_xlsx(workbook, data, objects)

    def _generate_partner_ledger_xlsx(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))

        # Get report data using the existing report model
        report_obj = self.env['report.mhj_account_reports.report_partnerledger']
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

        # Special format for initial balance lines
        init_balance_format = workbook.add_format({
            'bold': True, 'bg_color': '#FFF2CC', 'border': 1,
            'align': 'left', 'font_color': '#7F6000'
        })
        init_number_format = workbook.add_format({
            'bold': True, 'bg_color': '#FFF2CC', 'border': 1,
            'num_format': '#,##0.00', 'align': 'right', 'font_color': '#7F6000'
        })

        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 15)  # Journal
        worksheet.set_column('C:C', 20)  # Account
        worksheet.set_column('D:D', 30)  # Move
        worksheet.set_column('E:E', 40)  # Entry Label
        worksheet.set_column('F:F', 15)  # Debit
        worksheet.set_column('G:G', 15)  # Credit  
        worksheet.set_column('H:H', 15)  # Balance
        show_currency = bool(data.get('form', {}).get('amount_currency'))
        if show_currency:
            worksheet.set_column('I:I', 15)  # Currency
            worksheet.set_column('J:J', 20)  # Amount in Currency

        # Title
        last_col = 9 if show_currency else 7
        worksheet.merge_range(0, 0, 0, last_col, 'Partner Ledger Report', title_format)

        # Report parameters
        row = 3
        form_data = report_data.get('data', {}).get('form', {})
        date_from = form_data.get('date_from', '')
        date_to = form_data.get('date_to', '')
        target_move = form_data.get('target_move', 'posted')
        initial_balance = form_data.get('initial_balance', False)

        worksheet.write(row, 0, f'Date From: {date_from}', text_format)
        worksheet.write(row, 2, f'Date To: {date_to}', text_format)
        worksheet.write(row, 4, f'Target Moves: {target_move.title()}', text_format)
        row += 1
        worksheet.write(row, 0, f'Include Initial Balance: {"Yes" if initial_balance else "No"}', text_format)
        if show_currency:
            worksheet.write(row, 2, 'With Currency: Yes', text_format)
        row += 2

        # Process partners
        partners = report_data.get('docs', [])
        lines_func = report_data.get('lines')
        sum_func = report_data.get('sum_partner')
        get_initial_balance_safe = report_data.get('get_partner_initial_balance')

        for partner in partners:
            # Partner header
            partner_name = partner.name or 'Unknown Partner'
            worksheet.merge_range(row, 0, row, last_col, partner_name, partner_format)
            row += 1

            # Column headers for move lines
            headers = ['Date', 'Journal', 'Account', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance']
            if show_currency:
                headers += ['Currency', 'Amount in Currency']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Get partner lines
            partner_lines = lines_func(report_data.get('data'), partner)
            partner_debit = sum_func(report_data.get('data'), partner, 'debit')
            partner_credit = sum_func(report_data.get('data'), partner, 'credit')

            for line in partner_lines:
                # Check if this is an initial balance line
                is_initial_balance = line.get('name', '') == 'Initial Balance' or line.get('displayed_name', '') == 'Initial Balance'

                # Use special formatting for initial balance lines
                line_text_format = init_balance_format if is_initial_balance else text_format
                line_number_format = init_number_format if is_initial_balance else number_format
                line_date_format = init_balance_format if is_initial_balance else date_format

                worksheet.write(row, 0, line.get('date', ''), line_date_format)
                worksheet.write(row, 1, line.get('code', ''), line_text_format)
                worksheet.write(row, 2, line.get('a_name', ''), line_text_format)
                worksheet.write(row, 3, line.get('move_name', ''), line_text_format)
                worksheet.write(row, 4, line.get('displayed_name', ''), line_text_format)

                debit = line.get('debit', 0.0)
                credit = line.get('credit', 0.0)
                balance = line.get('progress', 0.0)

                worksheet.write(row, 5, debit, line_number_format)
                worksheet.write(row, 6, credit, line_number_format)
                worksheet.write(row, 7, balance, line_number_format)
                if show_currency:
                    currency = line.get('currency_id')
                    worksheet.write(row, 8, currency.name if currency else '', line_text_format)
                    if currency and not is_initial_balance:
                        worksheet.write(row, 9, line.get('amount_currency') or 0.0, line_number_format)
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
    _name = 'report.mhj_account_reports.trial_balance_xlsx'
    _description = 'Trial Balance XLSX Report'
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def generate_xlsx_report(self, workbook, data, objects):
        """Main method called by Odoo's report_xlsx framework"""
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
        
        self._generate_trial_balance_xlsx(workbook, data, objects)

    def _generate_trial_balance_xlsx(self, workbook, data, partners):
        if not XLSX_AVAILABLE:
            raise UserError(_("Excel export requires the 'report_xlsx' module to be installed. "
                            "Please install the 'report_xlsx' module and restart Odoo."))
            
        # Get report data using the existing report model
        report_obj = self.env['report.mhj_account_reports.report_trialbalance']
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

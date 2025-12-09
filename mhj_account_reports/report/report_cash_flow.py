import time
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportCashFlow(models.AbstractModel):
    """Cash Flow Statement Report - Standard Accounting Format.
    
    Follows the standard three-section structure:
    1. OPERATING ACTIVITIES - Cash from core business operations
    2. INVESTING ACTIVITIES - Cash from investment/capital activities
    3. FINANCING ACTIVITIES - Cash from debt and equity
    
    Uses balance change method to calculate cash flows from changes in account balances.
    """
    _name = 'report.mhj_account_reports.report_cash_flow'
    _description = 'Cash Flow Report'

    def _get_cash_balance(self, date, operator):
        """Get cash account balance at a specific date using SQL."""
        if not date:
            return 0.0
        
        query = f"""
            SELECT COALESCE(SUM(aml.debit - aml.credit), 0) as balance
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.date {operator} %(date)s
                AND aml.company_id = %(company_id)s
                AND aml.parent_state != 'cancel'
                AND aa.account_type = 'asset_cash'
        """
        
        params = {
            'date': date,
            'company_id': self.env.company.id,
        }
        
        try:
            self.env.cr.execute(query, params)
            return self.env.cr.fetchone()[0] or 0.0
        except Exception as e:
            _logger.warning(f"Could not fetch cash balance: {str(e)}")
            return 0.0

    def _get_balance_for_account_types_sql(self, date, operator, account_types, company_id):
        """Get total balance for account types at a specific date using SQL."""
        if not date or not account_types:
            return 0.0
        
        account_types_tuple = tuple(account_types)
        
        query = f"""
            SELECT COALESCE(SUM(aml.debit - aml.credit), 0) as balance
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.date {operator} %(date)s
                AND aml.company_id = %(company_id)s
                AND aml.parent_state != 'cancel'
                AND aa.account_type IN %(account_types)s
        """
        
        params = {
            'date': date,
            'company_id': company_id,
            'account_types': account_types_tuple
        }
        
        try:
            self.env.cr.execute(query, params)
            return self.env.cr.fetchone()[0] or 0.0
        except Exception as e:
            _logger.warning(f"Could not fetch balance for account types: {str(e)}")
            return 0.0

    def _get_balance_change(self, date_from, date_to, account_types, company_id):
        """Calculate balance change for account types between periods."""
        beginning_balance = self._get_balance_for_account_types_sql(
            date_from, '<', account_types, company_id
        )
        ending_balance = self._get_balance_for_account_types_sql(
            date_to, '<=', account_types, company_id
        )
        return ending_balance - beginning_balance

    def _get_operating_activities(self, date_from, date_to, company_id):
        """Calculate operating cash flows from working capital changes."""
        activities = {}
        
        # Changes in accounts receivable
        receivables_change = self._get_balance_change(
            date_from, date_to, ['asset_receivable'], company_id
        )
        if receivables_change != 0:
            activities['(Increase)/Decrease in Accounts Receivable'] = -receivables_change
        
        # Changes in inventory (current assets excluding receivables)
        inventory_change = self._get_balance_change(
            date_from, date_to, ['asset_current'], company_id
        )
        if inventory_change != 0 and inventory_change != receivables_change:
            activities['(Increase)/Decrease in Inventory'] = -inventory_change
        
        # Changes in accounts payable
        payables_change = self._get_balance_change(
            date_from, date_to, ['liability_payable'], company_id
        )
        if payables_change != 0:
            activities['Increase/(Decrease) in Accounts Payable'] = payables_change
        
        # Other operating current liabilities (accrued expenses)
        current_liab_change = self._get_balance_change(
            date_from, date_to, ['liability_current'], company_id
        )
        other_liab_change = current_liab_change - payables_change if payables_change != 0 else current_liab_change
        if other_liab_change != 0:
            activities['Increase/(Decrease) in Accrued Expenses'] = other_liab_change
        
        return activities

    def _get_investing_activities(self, date_from, date_to, company_id):
        """Calculate investing cash flows from fixed asset changes."""
        activities = {}
        
        # Fixed assets changes (Property, Plant & Equipment)
        fixed_assets_change = self._get_balance_change(
            date_from, date_to, ['asset_fixed'], company_id
        )
        if fixed_assets_change != 0:
            activities['(Purchase) of Property, Plant & Equipment'] = -fixed_assets_change
        
        # Investments and other non-current assets
        intangible_change = self._get_balance_change(
            date_from, date_to, ['asset_non_current'], company_id
        )
        if intangible_change != 0 and intangible_change != fixed_assets_change:
            activities['(Purchase)/Sale of Investments & Intangibles'] = -intangible_change
        
        return activities

    def _get_financing_activities(self, date_from, date_to, company_id):
        """Calculate financing cash flows from debt and equity changes."""
        activities = {}
        
        # Long-term debt changes
        lt_debt_change = self._get_balance_change(
            date_from, date_to, ['liability_non_current'], company_id
        )
        if lt_debt_change != 0:
            activities['(Proceeds from)/Repayment of Long-term Debt'] = lt_debt_change
        
        # Short-term borrowings (current portion minus payables)
        st_borrowing_change = self._get_balance_change(
            date_from, date_to, ['liability_current'], company_id
        )
        payables_change = self._get_balance_change(
            date_from, date_to, ['liability_payable'], company_id
        )
        adjusted_st_change = st_borrowing_change - payables_change if payables_change != 0 else st_borrowing_change
        if adjusted_st_change != 0:
            activities['(Proceeds from)/Repayment of Short-term Borrowings'] = adjusted_st_change
        
        # Equity changes (capital contributions, retained earnings, etc.)
        equity_change = self._get_balance_change(
            date_from, date_to, ['equity'], company_id
        )
        if equity_change != 0:
            activities['Capital Contributions/(Distributions)'] = equity_change
        
        return activities

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate cash flow report data."""
        if not data or not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        company = self.env.company
        currency = company.currency_id
        date_from = data['form'].get('date_from')
        date_to = data['form'].get('date_to')
        
        # Get cash balances
        beginning_cash = self._get_cash_balance(date_from, '<')
        ending_cash = self._get_cash_balance(date_to, '<=')
        actual_net_change = ending_cash - beginning_cash
        
        # Get activities
        operating = self._get_operating_activities(date_from, date_to, company.id)
        investing = self._get_investing_activities(date_from, date_to, company.id)
        financing = self._get_financing_activities(date_from, date_to, company.id)
        
        # Calculate net totals
        net_operating = sum(operating.values())
        net_investing = sum(investing.values())
        net_financing = sum(financing.values())
        classified_total = net_operating + net_investing + net_financing
        
        # Calculate unclassified
        net_unclassified = actual_net_change - classified_total
        
        return {
            'doc_ids': docids,
            'doc_model': data.get('model', 'account.cash.flow.wizard'),
            'docs': self.env[data.get('model', 'account.cash.flow.wizard')].browse(docids),
            'data': data['form'],
            'company': company,
            'currency': currency,
            'date_from': date_from,
            'date_to': date_to,
            'operating_activities': operating,
            'net_operating': net_operating,
            'investing_activities': investing,
            'net_investing': net_investing,
            'financing_activities': financing,
            'net_financing': net_financing,
            'unclassified': net_unclassified,
            'beginning_cash': beginning_cash,
            'ending_cash': ending_cash,
            'actual_net_change': actual_net_change,
        }

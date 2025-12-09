# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class AccountingReportsController(http.Controller):
    """Controller for interactive accounting reports."""

    @http.route('/mhj/accounting_reports/get_data', type='json', auth='user')
    def get_report_data(self, report_type, filters):
        """Get report data based on report type."""
        try:
            _logger.info(f"Generating {report_type} report with filters: {filters}")
            
            if report_type == 'trial_balance':
                result = self._get_trial_balance_data(filters)
                _logger.info(f"Trial Balance report data: accounts count = {len(result.get('accounts', []))}")
                return result
            elif report_type == 'general_ledger':
                return self._get_general_ledger_data(filters)
            elif report_type == 'partner_ledger':
                return self._get_partner_ledger_data(filters)
            elif report_type == 'cash_flow':
                return self._get_cash_flow_data(filters)
            else:
                return {'error': 'Invalid report type'}
                
        except Exception as e:
            _logger.error(f"Error in get_report_data: {str(e)}", exc_info=True)
            return {'error': str(e)}

    @http.route('/mhj/accounting_reports/get_filter_data', type='json', auth='user')
    def get_filter_data(self):
        """Get data for filter dropdowns."""
        try:
            company = request.env.company
            
            # Get accounts
            accounts = request.env['account.account'].search([
                ('company_ids', 'in', [company.id]),
                ('deprecated', '=', False)
            ], order='code')
            
            # Get journals
            journals = request.env['account.journal'].search([
                ('company_id', '=', company.id)
            ], order='name')
            
            # Get partners with account moves
            partners = request.env['res.partner'].search([
                ('id', 'in', request.env['account.move.line'].search([]).mapped('partner_id').ids)
            ], order='name', limit=500)  # Limit for performance
            
            # Get analytic accounts
            analytic_accounts = request.env['account.analytic.account'].search([
                ('company_id', 'in', [False, company.id])
            ], order='name')
            
            return {
                'accounts': [{'id': a.id, 'code': a.code, 'name': a.name} for a in accounts],
                'journals': [{'id': j.id, 'code': j.code, 'name': j.name} for j in journals],
                'partners': [{'id': p.id, 'name': p.name} for p in partners],
                'analytic_accounts': [{'id': a.id, 'name': a.name} for a in analytic_accounts],
                'company': {'id': company.id, 'name': company.name, 'currency': company.currency_id.symbol},
            }
        except Exception as e:
            _logger.error(f"Error in get_filter_data: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _get_trial_balance_data(self, filters):
        """Get Trial Balance report data using existing report model."""
        _logger.info(f"_get_trial_balance_data called with filters: {filters}")
        report_model = request.env['report.mhj_account_reports.report_trialbalance']
        
        # Build proper context like the wizard does
        used_context = {
            'journal_ids': filters.get('journal_ids') or False,
            'state': filters.get('state', 'posted'),
            'date_from': filters.get('date_from') or False,
            'date_to': filters.get('date_to') or False,
            'strict_range': True if filters.get('date_from') else False,
            'company_id': request.env.company.id,
        }
        
        # Build data structure expected by existing _get_report_values
        data = {
            'form': {
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'target_move': filters.get('state', 'posted'),
                'display_account': filters.get('display_account', 'all'),
                'journal_ids': filters.get('journal_ids', []),
                'account_ids': filters.get('account_ids', []),
                'analytic_account_ids': filters.get('analytic_account_ids', []),
                'used_context': used_context,
                'company_id': [request.env.company.id, request.env.company.name],
            },
            'model': 'account.account',
            'ids': [],
        }
        
        # Set context with all the filter values
        _logger.info(f"Setting context: {used_context}")
        ctx = dict(request.env.context, **used_context)
        ctx['account_ids'] = filters.get('account_ids', [])
        ctx['partner_ids'] = filters.get('partner_ids', [])
        ctx['analytic_account_ids'] = filters.get('analytic_account_ids', [])
        # Add active_model and active_ids (required by report model)
        ctx['active_model'] = 'account.account'
        ctx['active_ids'] = []
        
        _logger.info(f"Calling report _get_report_values with context: {ctx}")
        # Call existing report method with proper context
        result = report_model.with_context(ctx)._get_report_values([], data)
        
        _logger.info(f"Report returned: {len(result.get('Accounts', []))} accounts")
        
        # Transform data for JSON/JavaScript consumption
        accounts_data = []
        total_initial_debit = 0.0
        total_initial_credit = 0.0
        total_debit = 0.0
        total_credit = 0.0
        total_end_debit = 0.0
        total_end_credit = 0.0
        
        for account in result.get('Accounts', []):
            accounts_data.append({
                'id': account.get('id'),
                'code': account.get('code'),
                'name': account.get('name'),
                'initial_debit': account.get('initial_debit', 0.0),
                'initial_credit': account.get('initial_credit', 0.0),
                'initial_balance': account.get('initial_balance', 0.0),
                'debit': account.get('debit', 0.0),
                'credit': account.get('credit', 0.0),
                'balance': account.get('balance', 0.0),
                'end_debit': account.get('end_debit', 0.0),
                'end_credit': account.get('end_credit', 0.0),
                'end_balance': account.get('end_balance', 0.0),
            })
            
            total_initial_debit += account.get('initial_debit', 0.0)
            total_initial_credit += account.get('initial_credit', 0.0)
            total_debit += account.get('debit', 0.0)
            total_credit += account.get('credit', 0.0)
            total_end_debit += account.get('end_debit', 0.0)
            total_end_credit += account.get('end_credit', 0.0)
        
        response = {
            'accounts': accounts_data,
            'totals': {
                'initial_debit': total_initial_debit,
                'initial_credit': total_initial_credit,
                'period_debit': total_debit,
                'period_credit': total_credit,
                'ending_debit': total_end_debit,
                'ending_credit': total_end_credit,
            },
            'company': request.env.company.name,
            'currency_symbol': request.env.company.currency_id.symbol,
            'date_from': filters.get('date_from'),
            'date_to': filters.get('date_to'),
        }
        _logger.info(f"Returning response with {len(accounts_data)} accounts")
        return response

    def _get_general_ledger_data(self, filters):
        """Get General Ledger report data - placeholder for future implementation."""
        return {'error': 'General Ledger interactive report not yet implemented'}

    def _get_partner_ledger_data(self, filters):
        """Get Partner Ledger report data - placeholder for future implementation."""
        return {'error': 'Partner Ledger interactive report not yet implemented'}

    def _get_cash_flow_data(self, filters):
        """Get Cash Flow report data - placeholder for future implementation."""
        return {'error': 'Cash Flow interactive report not yet implemented'}

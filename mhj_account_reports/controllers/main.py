# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class AccountingReportsController(http.Controller):
    """Controller for interactive accounting reports."""

    def _build_used_context(self, filters):
        """Mirror wizard context so date_from/initial balance logic matches PDF reports."""
        return {
            'journal_ids': filters.get('journal_ids') or False,
            'state': filters.get('state', 'posted'),
            'date_from': filters.get('date_from') or False,
            'date_to': filters.get('date_to') or False,
            'strict_range': True if filters.get('date_from') else False,
            'company_id': request.env.company.id,
            'lang': request.env.lang,
        }

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
            elif report_type == 'balance_sheet':
                return self._get_balance_sheet_data(filters)
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
            
            # Build filter data ensuring all records have valid IDs
            accounts_data = [{'id': a.id, 'code': a.code or '', 'name': a.name or ''} for a in accounts if a.id]
            journals_data = [{'id': j.id, 'code': j.code or '', 'name': j.name or ''} for j in journals if j.id]
            partners_data = [{'id': p.id, 'name': p.name or ''} for p in partners if p.id]
            analytics_data = [{'id': a.id, 'name': a.name or ''} for a in analytic_accounts if a.id]
            
            _logger.info(f"Filter data: {len(accounts_data)} accounts, {len(journals_data)} journals, {len(partners_data)} partners, {len(analytics_data)} analytics")
            
            return {
                'accounts': accounts_data,
                'journals': journals_data,
                'partners': partners_data,
                'analytic_accounts': analytics_data,
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
        
        # Select accounts based on filter (fallback to all)
        account_ids = filters.get('account_ids') or []
        if account_ids:
            accounts = request.env['account.account'].browse(account_ids)
        else:
            accounts = request.env['account.account'].search([])
        _logger.info(f"Found {len(accounts)} accounts to process (filtered={bool(account_ids)})")
        
        # Build data structure expected by existing _get_report_values
        data = {
            'form': {
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'target_move': filters.get('state', 'posted'),
                'display_account': filters.get('display_account', 'all'),
                'journal_ids': filters.get('journal_ids', []),
                'account_ids': account_ids,
                'analytic_account_ids': filters.get('analytic_account_ids', []),
                'used_context': used_context,
                'company_id': [request.env.company.id, request.env.company.name],
            },
            'model': 'account.account',
            'ids': accounts.ids,
        }
        
        # Set context with all the filter values
        _logger.info(f"Setting context: {used_context}")
        ctx = dict(request.env.context, **used_context)
        # Ensure all filter IDs are in context for _query_get
        if filters.get('account_ids'):
            ctx['account_ids'] = filters.get('account_ids')
        if filters.get('partner_ids'):
            ctx['partner_ids'] = filters.get('partner_ids')
        if filters.get('analytic_account_ids'):
            ctx['analytic_account_ids'] = filters.get('analytic_account_ids')
        # Add active_model and active_ids (required by report model)
        ctx['active_model'] = 'account.account'
        ctx['active_ids'] = accounts.ids  # Pass selected/all account IDs
        
        _logger.info(f"Calling report _get_report_values with {len(accounts)} accounts")
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
            # Skip accounts based on display_account filter
            display_account = filters.get('display_account', 'all')
            has_moves = account.get('debit', 0.0) != 0 or account.get('credit', 0.0) != 0 or account.get('balance', 0.0) != 0
            
            if display_account == 'movement' and not has_moves:
                continue
            elif display_account == 'not_zero':
                currency = request.env.company.currency_id
                if currency.is_zero(account.get('balance', 0.0)):
                    continue
                
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
        """Get General Ledger report data using existing report model."""
        _logger.info(f"_get_general_ledger_data called with filters: {filters}")
        report_model = request.env['report.mhj_account_reports.report_general_ledger']

        # Context similar to wizard
        used_context = self._build_used_context(filters)

        # Accounts: respect selection if provided
        account_ids = filters.get('account_ids') or []
        if account_ids:
            accounts = request.env['account.account'].browse(account_ids)
        else:
            accounts = request.env['account.account'].search([])
        _logger.info(f"GL accounts to process: {len(accounts)} (filtered={bool(account_ids)})")

        # Form payload mirroring wizard fields
        data = {
            'form': {
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'target_move': filters.get('state', 'posted'),
                'display_account': filters.get('display_account', 'all'),
                'journal_ids': filters.get('journal_ids', []),
                'account_ids': account_ids,
                'analytic_account_ids': filters.get('analytic_account_ids', []),
                'partner_ids': filters.get('partner_ids', []),
                'initial_balance': filters.get('initial_balance', True),
                'sortby': filters.get('sortby', 'sort_date'),
                'used_context': used_context,
                'company_id': [request.env.company.id, request.env.company.name],
            },
            'model': 'account.account',
            'ids': accounts.ids,
        }

        ctx = dict(request.env.context, **used_context)
        ctx['account_ids'] = account_ids
        ctx['partner_ids'] = filters.get('partner_ids', [])
        ctx['analytic_account_ids'] = filters.get('analytic_account_ids', [])
        ctx['active_model'] = 'account.account'
        ctx['active_ids'] = accounts.ids
        # Ensure all filters are in context for _query_get
        if filters.get('account_ids'):
            ctx['account_ids'] = filters.get('account_ids')

        _logger.info("Calling GL _get_report_values")
        result = report_model.with_context(ctx)._get_report_values([], data)

        accounts_data = result.get('Accounts', [])
        # Filter based on display_account option
        display_account = filters.get('display_account', 'all')
        if display_account == 'movement':
            accounts_data = [a for a in accounts_data if a.get('move_lines') or a.get('debit', 0.0) != 0 or a.get('credit', 0.0) != 0]
        elif display_account == 'not_zero':
            currency = request.env.company.currency_id
            accounts_data = [a for a in accounts_data if not currency.is_zero(a.get('balance', 0.0))]
        
        total_debit = sum(a.get('debit', 0.0) for a in accounts_data)
        total_credit = sum(a.get('credit', 0.0) for a in accounts_data)
        total_balance = sum(a.get('balance', 0.0) for a in accounts_data)

        response = {
            'accounts': accounts_data,
            'totals': {
                'debit': total_debit,
                'credit': total_credit,
                'balance': total_balance,
            },
            'company': request.env.company.name,
            'currency_symbol': request.env.company.currency_id.symbol,
            'date_from': filters.get('date_from'),
            'date_to': filters.get('date_to'),
        }
        _logger.info(f"GL response accounts={len(accounts_data)}")
        return response

    def _get_partner_ledger_data(self, filters):
        """Get Partner Ledger report data using existing report model."""
        _logger.info(f"_get_partner_ledger_data called with filters: {filters}")
        report_model = request.env['report.mhj_account_reports.report_partnerledger']

        used_context = self._build_used_context(filters)

        partner_ids = filters.get('partner_ids') or []
        if partner_ids:
            partners = request.env['res.partner'].browse(partner_ids)
        else:
            partners = request.env['res.partner'].search([])

        data = {
            'form': {
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'target_move': filters.get('state', 'posted'),
                'result_selection': filters.get('result_selection', 'customer'),
                'partner_ids': partner_ids,
                'journal_ids': filters.get('journal_ids', []),
                'reconciled': filters.get('reconciled', False),
                'amount_currency': filters.get('amount_currency', False),
                'initial_balance': filters.get('initial_balance', True),
                'used_context': used_context,
                'company_id': [request.env.company.id, request.env.company.name],
            },
            'model': 'res.partner',
            'ids': partners.ids,
        }

        ctx = dict(request.env.context, **used_context)
        ctx['partner_ids'] = partner_ids
        ctx['analytic_account_ids'] = filters.get('analytic_account_ids', [])
        ctx['account_ids'] = filters.get('account_ids', [])
        ctx['active_model'] = 'res.partner'
        ctx['active_ids'] = partners.ids

        # Let report build computed settings (account types, move_state)
        report_result = report_model.with_context(ctx)._get_report_values([], data)

        # Use partner list as determined by report (ensures only partners with activity are included)
        if report_result and report_result.get('doc_ids'):
            partner_ids = report_result.get('doc_ids')
            partners = request.env['res.partner'].browse(partner_ids)
        elif report_result and report_result.get('docs'):
            partners = report_result.get('docs')
            partner_ids = partners.ids

        # Keep payload/context in sync with resolved partners
        data['ids'] = partner_ids
        data['form']['partner_ids'] = partner_ids
        ctx['active_ids'] = partner_ids

        # Re-call _get_report_values with synced data to ensure data['computed'] is populated
        report_result = report_model.with_context(ctx)._get_report_values([], data)
        _logger.info(f"Partner ledger partners: {len(partners)} (filtered={bool(filters.get('partner_ids'))}), computed keys={list(data.get('computed', {}).keys())}")

        partner_rows = []
        for partner in partners:
            lines = report_model.with_context(ctx)._lines(data, partner)
            # Reuse report helpers so interactive totals match PDF
            init_bal = report_model.get_partner_initial_balance_safe(
                data, partner, data['form'].get('date_from')
            ) or {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
            total_debit = report_model._sum_partner(data, partner, 'debit')
            total_credit = report_model._sum_partner(data, partner, 'credit')
            total_balance = report_model._sum_partner(data, partner, 'debit - credit')

            partner_rows.append({
                'id': partner.id,
                'name': partner.name,
                'ref': partner.ref,
                'initial_balance': init_bal,
                'lines': lines,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': total_balance,
            })

        response = {
            'partners': partner_rows,
            'company': request.env.company.name,
            'currency_symbol': request.env.company.currency_id.symbol,
            'date_from': filters.get('date_from'),
            'date_to': filters.get('date_to'),
        }
        _logger.info(f"Partner ledger response partners={len(partner_rows)}")
        return response

    def _get_cash_flow_data(self, filters):
        """Get Cash Flow report data using existing report model."""
        _logger.info(f"_get_cash_flow_data called with filters: {filters}")
        report_model = request.env['report.mhj_account_reports.report_cash_flow']

        used_context = {
            'state': filters.get('state', 'posted'),
            'date_from': filters.get('date_from') or False,
            'date_to': filters.get('date_to') or False,
            'strict_range': True if filters.get('date_from') else False,
            'company_id': request.env.company.id,
        }

        data = {
            'form': {
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'target_move': filters.get('state', 'posted'),
                'used_context': used_context,
                'company_id': [request.env.company.id, request.env.company.name],
            },
            'model': 'account.cash.flow.wizard',
            'ids': [],
        }

        ctx = dict(request.env.context, **used_context)
        ctx['active_model'] = 'account.cash.flow.wizard'
        ctx['active_ids'] = []

        result = report_model.with_context(ctx)._get_report_values([], data)

        response = {
            'company': result.get('company').name if result.get('company') else request.env.company.name,
            'currency_symbol': result.get('currency').symbol if result.get('currency') else request.env.company.currency_id.symbol,
            'date_from': filters.get('date_from'),
            'date_to': filters.get('date_to'),
            'operating': result.get('operating_activities', {}),
            'net_operating': result.get('net_operating'),
            'investing': result.get('investing_activities', {}),
            'net_investing': result.get('net_investing'),
            'financing': result.get('financing_activities', {}),
            'net_financing': result.get('net_financing'),
            'unclassified': result.get('unclassified'),
            'beginning_cash': result.get('beginning_cash'),
            'ending_cash': result.get('ending_cash'),
            'actual_net_change': result.get('actual_net_change'),
        }
        _logger.info("Cash flow response ready")
        return response

    def _get_balance_sheet_data(self, filters):
        """Get Balance Sheet data using existing financial report model."""
        _logger.info(f"_get_balance_sheet_data called with filters: {filters}")
        report_model = request.env['report.mhj_account_reports.report_financial']

        # Locate the Balance Sheet financial report definition
        balance_sheet = request.env.ref('mhj_account_reports.account_financial_report_balancesheet0', raise_if_not_found=False)
        if not balance_sheet:
            balance_sheet = request.env['account.financial.report'].search([('name', 'ilike', 'Balance Sheet'), ('parent_id', '=', False)], limit=1)
        if not balance_sheet:
            return {'error': 'Balance Sheet definition not found'}

        used_context = {
            'journal_ids': filters.get('journal_ids') or False,
            'state': filters.get('state', 'posted'),
            'date_from': filters.get('date_from') or False,
            'date_to': filters.get('date_to') or False,
            'strict_range': True if filters.get('date_from') else False,
            'company_id': request.env.company.id,
        }

        data = {
            'form': {
                'account_report_id': [balance_sheet.id, balance_sheet.name],
                'enable_filter': False,
                'label_filter': '',
                'debit_credit': False,
                'filter_cmp': 'filter_no',
                'date_from_cmp': False,
                'date_to_cmp': False,
                'comparison_context': {},
                'target_move': filters.get('state', 'posted'),
                'date_from': filters.get('date_from'),
                'date_to': filters.get('date_to'),
                'journal_ids': filters.get('journal_ids', []),
                'used_context': used_context,
            },
            'model': 'account.financial.report',
            'ids': [balance_sheet.id],
        }

        ctx = dict(request.env.context, **used_context)
        ctx['active_model'] = 'account.financial.report'
        ctx['active_id'] = balance_sheet.id
        ctx['active_ids'] = [balance_sheet.id]

        result = report_model.with_context(ctx)._get_report_values([], data)
        lines = result.get('get_account_lines', []) if result else []

        response = {
            'lines': lines,
            'company': request.env.company.name,
            'currency_symbol': request.env.company.currency_id.symbol,
            'date_from': filters.get('date_from'),
            'date_to': filters.get('date_to'),
        }
        _logger.info(f"Balance sheet lines: {len(lines)}")
        return response

import time
import gc
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.mhj_account_reports.report_trialbalance'
    _description = 'Trial Balance Report'

    def _get_initial_balance(self, accounts, date_from):
        """
        Get initial balance (before date_from) for accounts
        """
        if not date_from:
            return {}
        
        BATCH_SIZE = 5000
        account_batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
        initial_result = {}
        
        # Get balance before date_from
        ctx = dict(self.env.context)
        ctx['date_to'] = date_from
        ctx['date_from'] = False
        ctx['initial_bal'] = True
        
        tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        
        for batch_accounts in account_batches:
            request = """SELECT account_id AS id,
                               COALESCE(SUM(debit), 0.0) AS initial_debit,
                               COALESCE(SUM(credit), 0.0) AS initial_credit,
                               COALESCE(SUM(debit) - SUM(credit), 0.0) AS initial_balance
                        FROM """ + tables + """
                        WHERE account_id IN %s AND date < %s """ + filters + """
                        GROUP BY account_id"""
            
            params = (tuple(batch_accounts.ids), date_from) + tuple(where_params)
            self.env.cr.execute(request, params)
            
            for row in self.env.cr.dictfetchall():
                initial_result[row.pop('id')] = row
            
            gc.collect()
        
        return initial_result

    def _get_accounts(self, accounts, display_account, date_from=None):
        """ 
        Optimized computation with 6 columns: initial debit/credit, current debit/credit, ending debit/credit
        Uses batching and optimized SQL to handle millions of journal items.
        """
        BATCH_SIZE = 5000  # Process accounts in batches
        
        # Get initial balances if date_from is set
        initial_balances = self._get_initial_balance(accounts, date_from) if date_from else {}
        
        # Split accounts into batches
        account_batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
        account_result = {}
        
        # Prepare optimized sql query for current period
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
            
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        
        # Process each batch to avoid memory issues
        for batch_accounts in account_batches:
            # Optimized query with explicit indexes and proper aggregation
            request = """SELECT account_id AS id, 
                               COALESCE(SUM(debit), 0.0) AS debit, 
                               COALESCE(SUM(credit), 0.0) AS credit, 
                               COALESCE(SUM(debit) - SUM(credit), 0.0) AS balance
                        FROM """ + tables + """
                        WHERE account_id IN %s """ + filters + """
                        GROUP BY account_id"""
                        
            params = (tuple(batch_accounts.ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            
            # Store results from this batch
            for row in self.env.cr.dictfetchall():
                account_result[row.pop('id')] = row
            
            # Force garbage collection after processing each batch
            gc.collect()
        
        # Build final result with display filtering and 6 columns
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['initial_debit', 'initial_credit', 'initial_balance',
                                            'debit', 'credit', 'balance',
                                            'end_debit', 'end_credit', 'end_balance'])
            currency = account.currency_id or self.env.company.currency_id
            res['code'] = account.code
            res['name'] = account.name
            
            # Initial balances
            if account.id in initial_balances:
                init_data = initial_balances[account.id]
                res['initial_debit'] = init_data.get('initial_debit', 0.0)
                res['initial_credit'] = init_data.get('initial_credit', 0.0)
                res['initial_balance'] = init_data.get('initial_balance', 0.0)
            
            # Current period movements
            if account.id in account_result:
                account_data = account_result[account.id]
                res['debit'] = account_data.get('debit', 0.0)
                res['credit'] = account_data.get('credit', 0.0) 
                res['balance'] = account_data.get('balance', 0.0)
            
            # Ending balances (initial + current)
            res['end_debit'] = res['initial_debit'] + res['debit']
            res['end_credit'] = res['initial_credit'] + res['credit']
            res['end_balance'] = res['initial_balance'] + res['balance']
            
            # Apply display filters efficiently
            should_include = False
            if display_account == 'all':
                should_include = True
            elif display_account == 'not_zero':
                should_include = not currency.is_zero(res['end_balance'])
            elif display_account == 'movement':
                should_include = (not currency.is_zero(res['debit']) or 
                                not currency.is_zero(res['credit']))
            
            if should_include:
                account_res.append(res)
                
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if model == 'account.account' else self.env['account.account'].search([])
        context = data['form'].get('used_context')
        date_from = data['form'].get('date_from')
        analytic_accounts = []
        if data['form'].get('analytic_account_ids'):
            analytic_account_ids = self.env['account.analytic.account'].browse(data['form'].get('analytic_account_ids'))
            context['analytic_account_ids'] = analytic_account_ids
            analytic_accounts = [account.name for account in analytic_account_ids]
        account_res = self.with_context(context)._get_accounts(accounts, display_account, date_from)
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'print_journal': codes,
            'analytic_accounts': analytic_accounts,
            'time': time,
            'Accounts': account_res,
        }

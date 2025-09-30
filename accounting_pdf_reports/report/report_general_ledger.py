import time
import gc
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class ReportGeneralLedger(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_general_ledger'
    _description = 'General Ledger Report'

    def _start_memory_monitoring(self):
        """Start memory monitoring - optional implementation"""
        try:
            memory_mixin = self.env['account.report.memory.mixin']
            if hasattr(memory_mixin, '_start_memory_monitoring'):
                memory_mixin._start_memory_monitoring()
        except Exception:
            pass  # Memory monitoring is optional
    
    def _check_memory_usage(self, context_msg="", force_gc=False):
        """Check memory usage - optional implementation"""
        try:
            memory_mixin = self.env['account.report.memory.mixin']
            if hasattr(memory_mixin, '_check_memory_usage'):
                return memory_mixin._check_memory_usage(context_msg, force_gc)
        except Exception:
            pass  # Memory monitoring is optional
        return 0
    
    def _log_memory_summary(self):
        """Log memory summary - optional implementation"""
        try:
            memory_mixin = self.env['account.report.memory.mixin']
            if hasattr(memory_mixin, '_log_memory_summary'):
                memory_mixin._log_memory_summary()
        except Exception:
            pass  # Memory monitoring is optional

    def _get_account_move_entry(self, accounts, analytic_account_ids,
                                partner_ids, init_balance,
                                sortby, display_account):
        """
        Optimized version for handling millions of journal items.
        Uses batching and pagination to avoid memory issues.
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        
        # Configuration for batch processing
        BATCH_SIZE = 10000  # Process accounts in batches
        MOVE_LINE_LIMIT = 50000  # Limit move lines per account for memory
        
        # Split accounts into batches to avoid memory issues
        account_batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
        account_res = []
        
        for batch_accounts in account_batches:
            batch_result = self._process_account_batch(
                batch_accounts, analytic_account_ids, partner_ids, 
                init_balance, sortby, display_account, MOVE_LINE_LIMIT
            )
            account_res.extend(batch_result)
            
            # Force garbage collection after each batch
            gc.collect()
            
        return account_res
    
    def _process_account_batch(self, accounts, analytic_account_ids, partner_ids, 
                              init_balance, sortby, display_account, move_line_limit):
        """
        Process a batch of accounts with optimized SQL queries
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        
        # Get initial balances with optimized query
        if init_balance:
            self._get_initial_balances(accounts, analytic_account_ids, partner_ids, move_lines)
        
        # Get move lines with pagination and optimized indexes
        self._get_paginated_move_lines(accounts, analytic_account_ids, partner_ids, 
                                     sortby, move_lines, move_line_limit)
        
        # Calculate account totals efficiently
        return self._calculate_account_totals(accounts, move_lines, display_account)
    
    def _get_initial_balances(self, accounts, analytic_account_ids, partner_ids, move_lines):
        """
        Get initial balances with optimized SQL - calculates balance before date_from
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        
        # Only calculate initial balance if there's a start date
        date_from = self.env.context.get('date_from')
        if not date_from:
            return
        
        context = dict(self.env.context)
        # Set date_to to day before date_from to get balance up to that point
        context['date_to'] = date_from
        context['date_from'] = False  # Get all entries before date_from
        context['initial_bal'] = True
        
        if analytic_account_ids:
            context['analytic_account_ids'] = analytic_account_ids
        if partner_ids:
            context['partner_ids'] = partner_ids
            
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(context)._query_get()
        init_wheres = [""]
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        
        # Optimized initial balance query - only show accounts with non-zero balances
        sql = """SELECT 0 AS lid, l.account_id AS account_id, %s AS ldate,
            '' AS lcode, 0.0 AS amount_currency, '' AS analytic_account_id, 
            '' AS lref, 'Initial Balance' AS lname, 
            CASE WHEN COALESCE(SUM(l.debit - l.credit),0) > 0 
                 THEN COALESCE(SUM(l.debit - l.credit),0) 
                 ELSE 0.0 END AS debit,
            CASE WHEN COALESCE(SUM(l.debit - l.credit),0) < 0 
                 THEN ABS(COALESCE(SUM(l.debit - l.credit),0)) 
                 ELSE 0.0 END AS credit,
            COALESCE(SUM(l.debit - l.credit), 0) as balance, 
            '' AS lpartner_id, 'Initial Balance' AS move_name, '' AS move_id, '' AS currency_code,
            NULL AS currency_id, '' AS invoice_id, '' AS invoice_type, 
            '' AS invoice_number, '' AS partner_name
            FROM account_move_line l
            LEFT JOIN account_move m ON (l.move_id=m.id)
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
            WHERE l.account_id IN %s AND l.date < %s """ + filters + """
            GROUP BY l.account_id 
            HAVING COALESCE(SUM(l.debit - l.credit), 0) != 0"""
            
        params = (date_from, tuple(accounts.ids), date_from) + tuple(init_where_params)
        cr.execute(sql, params)
        
        for row in cr.dictfetchall():
            move_lines[row.pop('account_id')].append(row)
    
    def _get_paginated_move_lines(self, accounts, analytic_account_ids, partner_ids, 
                                 sortby, move_lines, move_line_limit):
        """
        Get move lines with pagination to handle large datasets
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        
        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'
        
        context = dict(self.env.context)
        if analytic_account_ids:
            context['analytic_account_ids'] = analytic_account_ids
        if partner_ids:
            context['partner_ids'] = partner_ids
            
        tables, where_clause, where_params = MoveLine.with_context(context)._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        
        # Process each account separately to control memory usage
        for account in accounts:
            offset = 0
            running_balance = 0
            
            # Get running balance from initial balance
            for init_line in move_lines.get(account.id, []):
                running_balance += init_line['debit'] - init_line['credit']
            
            while True:
                # Optimized query with LIMIT/OFFSET for pagination
                sql = """SELECT l.id AS lid, l.account_id AS account_id, 
                    l.date AS ldate, j.code AS lcode, l.currency_id, 
                    l.amount_currency, '' AS analytic_account_id,
                    l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, 
                    COALESCE(l.credit,0) AS credit, m.name AS move_name, 
                    c.symbol AS currency_code, p.name AS partner_name
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    JOIN account_account acc ON (l.account_id = acc.id)
                    WHERE l.account_id = %s """ + filters + \
                    " ORDER BY " + sql_sort + " LIMIT %s OFFSET %s"
                
                params = (account.id,) + tuple(where_params) + (move_line_limit, offset)
                cr.execute(sql, params)
                
                batch_rows = cr.dictfetchall()
                if not batch_rows:
                    break
                
                # Calculate running balance for this batch
                for row in batch_rows:
                    running_balance += row['debit'] - row['credit']
                    row['balance'] = running_balance
                    move_lines[row.pop('account_id')].append(row)
                
                offset += len(batch_rows)
                
                # Break if we got less than limit (end of data)
                if len(batch_rows) < move_line_limit:
                    break
    
    def _calculate_account_totals(self, accounts, move_lines, display_account):
        """
        Calculate account totals efficiently
        """
        account_res = []
        
        for account in accounts:
            currency = account.currency_id or self.env.company.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            
            account_move_lines = move_lines.get(account.id, [])
            res['move_lines'] = account_move_lines
            
            # Calculate totals efficiently
            for line in account_move_lines:
                res['debit'] += line['debit']
                res['credit'] += line['credit']
            
            # Set final balance from last line or calculate if no lines
            if account_move_lines:
                res['balance'] = account_move_lines[-1].get('balance', 0.0)
            else:
                res['balance'] = 0.0
            
            # Apply display filters
            if display_account == 'all':
                account_res.append(res)
            elif display_account == 'movement' and account_move_lines:
                account_res.append(res)
            elif display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
            
        # Start memory monitoring
        self._start_memory_monitoring()
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        analytic_account_ids = False
        if data['form'].get('analytic_account_ids', False):
            analytic_account_ids = self.env['account.analytic.account'].search(
                [('id', 'in', data['form']['analytic_account_ids'])])
        partner_ids = False
        if data['form'].get('partner_ids', False):
            partner_ids = self.env['res.partner'].search(
                [('id', 'in', data['form']['partner_ids'])])
        if model == 'account.account':
            accounts = docs
        else:
            domain = []
            if data['form'].get('account_ids', False):
                domain.append(('id', 'in', data['form']['account_ids']))
            accounts = self.env['account.account'].search(domain)
        self._check_memory_usage("Before processing accounts")
        
        accounts_res = self.with_context(
            data['form'].get('used_context', {}))._get_account_move_entry(
            accounts,
            analytic_account_ids,
            partner_ids,
            init_balance, sortby, display_account)
            
        self._check_memory_usage("After processing accounts", force_gc=True)
        self._log_memory_summary()
        
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            'accounts': accounts,
            'partner_ids': partner_ids,
            'analytic_account_ids': analytic_account_ids,
        }

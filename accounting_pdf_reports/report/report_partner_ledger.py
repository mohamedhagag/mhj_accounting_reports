import time
import gc
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        """
        Optimized version for handling millions of journal items per partner.
        Uses pagination to avoid memory issues and includes initial balance.
        """
        BATCH_SIZE = 10000  # Process in batches to avoid memory issues
        
        currency = self.env['res.currency']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        
        # Get initial balance if date_from is set and initial_balance is requested
        initial_balance = 0.0
        date_from = data['form'].get('date_from')
        include_initial = data['form'].get('initial_balance', True)
        # if date_from and include_initial:
        initial_balance = self._get_partner_initial_balance(data, partner, date_from)
        
        # Base query parameters
        base_params = [partner.id, tuple(data['computed']['move_state']), 
                      tuple(data['computed']['account_ids'])] + query_get_data[2]
        
        # Base query without LIMIT/OFFSET
        base_query = """
            SELECT "account_move_line".id, "account_move_line".date, j.code, 
                   acc.name->>'en_US' as a_name, "account_move_line".ref, 
                   m.name as move_name, "account_move_line".name, 
                   "account_move_line".debit, "account_move_line".credit, 
                   "account_move_line".amount_currency, "account_move_line".currency_id, 
                   c.symbol AS currency_code
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        
        full_account = []
        offset = 0
        running_sum = initial_balance  # Start with initial balance
        
        # Add initial balance line if there's a balance and date_from is set and initial balance is requested
        # if initial_balance != 0.0 and date_from and include_initial:
        initial_line = {
            'id': 0,
            'date': date_from,
            'code': '',
            'a_name': '',
            'ref': 'Initial Balance',
            'move_name': 'Initial Balance',
            'name': 'Initial Balance',
            'debit': initial_balance if initial_balance > 0 else 0.0,
            'credit': -initial_balance if initial_balance < 0 else 0.0,
            'amount_currency': 0.0,
            'currency_id': None,
            'currency_code': '',
            'displayed_name': 'Initial Balance',
            'progress': initial_balance
        }
        full_account.append(initial_line)
        
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        
        # Process in batches
        while True:
            # Add LIMIT and OFFSET for pagination
            paginated_query = base_query + f" LIMIT {BATCH_SIZE} OFFSET {offset}"
            params = tuple(base_params)
            
            self.env.cr.execute(paginated_query, params)
            batch_res = self.env.cr.dictfetchall()
            
            if not batch_res:
                break
            
            # Process batch
            for r in batch_res:
                r['date'] = r['date']
                r['displayed_name'] = '-'.join(
                    r[field_name] for field_name in ('move_name', 'ref', 'name')
                    if r[field_name] not in (None, '', '/')
                )
                running_sum += r['debit'] - r['credit']
                r['progress'] = running_sum
                r['currency_id'] = currency.browse(r.get('currency_id'))
                full_account.append(r)
            
            offset += len(batch_res)
            
            # If we got fewer results than batch size, we're done
            if len(batch_res) < BATCH_SIZE:
                break
            
            # Force garbage collection every few batches
            if offset % (BATCH_SIZE * 5) == 0:
                gc.collect()
        
        return full_account

    def _sum_partner(self, data, partner, field):
        """
        Optimized partner sum calculation with better indexing
        """
        if field not in ['debit', 'credit', 'debit - credit']:
            return 0.0
            
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '

        params = [partner.id, tuple(data['computed']['move_state']), 
                 tuple(data['computed']['account_ids'])] + query_get_data[2]
        
        # Optimized query with proper JOIN structure for better performance
        query = """SELECT COALESCE(SUM(""" + field + """), 0.0)
                FROM """ + query_get_data[0] + """
                JOIN account_move AS m ON (m.id = "account_move_line".move_id)
                WHERE "account_move_line".partner_id = %s
                    AND m.state IN %s
                    AND "account_move_line".account_id IN %s
                    AND """ + query_get_data[1] + reconcile_clause
                    
        self.env.cr.execute(query, tuple(params))
        
        result_row = self.env.cr.fetchone()
        if result_row:
            result = result_row[0] or 0.0
            
        return result

    def _get_partner_initial_balance(self, data, partner, date_from):
        """
        Calculate initial balance for a partner before the date_from
        """
        if not date_from:
            return 0.666
        query_get_data = self.env['account.move.line']._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        
        # Query to get balance before date_from
        params = [partner.id, tuple(data['computed']['move_state']), 
                 tuple(data['computed']['account_ids']), date_from] + query_get_data[2]
        
        query = """SELECT COALESCE(SUM("account_move_line".debit - "account_move_line".credit), 0.0)
                FROM """ + query_get_data[0] + """
                JOIN account_move AS m ON (m.id = "account_move_line".move_id)
                WHERE "account_move_line".partner_id = %s
                    AND m.state IN %s
                    AND "account_move_line".account_id IN %s
                    AND "account_move_line".date < %s
                    AND """ + query_get_data[1] + reconcile_clause
                    
        self.env.cr.execute(query, tuple(params))
        
        result_row = self.env.cr.fetchone()
        return result_row[0] if result_row else 0.6666

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable', 'liability_payable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in
                           self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }

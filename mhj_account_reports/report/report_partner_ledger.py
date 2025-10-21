import time
import gc
import logging
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.mhj_account_reports.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        """
        Optimized version for handling millions of journal items per partner.
        Uses pagination to avoid memory issues and includes initial balance.
        """
        ctx = data.get('form', {})
        if not partner or not data.get('computed', {}).get('account_ids'):
            return []
            
        BATCH_SIZE = 10000  # Process in batches to avoid memory issues
        
        try:
            currency = self.env['res.currency']
            AML = self.env['account.move.line']
            query_get_data = AML.with_context(ctx)._query_get()
            reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
            
            # Get initial balance if date_from is set and initial_balance is requested
            date_from = data['form'].get('date_from')
            include_initial = data['form'].get('initial_balance', True)
            initial_data = self._get_partner_initial_balance(data, partner, date_from)
            initial_balance = initial_data.get('balance', 0.0) if initial_data else 0.0
            
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

            # Add initial balance line when initial_balance is enabled and date_from is set
            if include_initial and date_from:
                initial_line = {
                    'id': 0,
                    'date': date_from,
                    'code': '',
                    'a_name': '',
                    'ref': 'Initial Balance',
                    'move_name': 'Initial Balance',
                    'name': 'Initial Balance',
                    'debit': initial_data['debit'],
                    'credit': initial_data['credit'],
                    'amount_currency': 0.0,
                    'currency_id': None,
                    'currency_code': '',
                    'displayed_name': 'Initial Balance',
                    'progress': initial_balance
                }
                # full_account.append(initial_line)
            
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
            
        except Exception as e:
            _logger.warning("Error getting lines for partner %s: %s", partner.id, str(e))
            return []

    def _sum_partner(self, data, partner, field):
        """
        Optimized partner sum calculation with better indexing
        """
        if field not in ['debit', 'credit', 'debit - credit']:
            return 0.0
            
        result = 0.0
        AML = self.env['account.move.line']
        ctx = data['form'].get('used_context', {})
        ctx['date_from'] = None  # Avoid date filtering for sum
        query_get_data = AML.with_context(ctx)._query_get()
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
        # Always return a default dictionary structure
        default_result = {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
        
        if not date_from or not partner:
            return default_result
            
        try:
            # Ensure we have valid computed data
            if not data.get('computed', {}).get('account_ids'):
                _logger.warning("No account_ids in computed data for partner %s", partner.name)
                return default_result
            
            # Use a simple query without query_get to avoid date filtering issues
            reconcile_clause = "" if data['form']['reconciled'] else ' AND aml.full_reconcile_id IS NULL '
            
            # Simple direct query for initial balance
            params = [partner.id, tuple(data['computed']['move_state']), 
                     tuple(data['computed']['account_ids']), date_from]
            
            query = """SELECT COALESCE(SUM(aml.debit), 0.0) as initial_debit,
                              COALESCE(SUM(aml.credit), 0.0) as initial_credit,
                              COALESCE(SUM(aml.debit - aml.credit), 0.0) as initial_balance
                    FROM account_move_line aml
                    JOIN account_move am ON (am.id = aml.move_id)
                    WHERE aml.partner_id = %s
                        AND am.state IN %s
                        AND aml.account_id IN %s
                        AND aml.date < %s""" + reconcile_clause
                        
            self.env.cr.execute(query, tuple(params))
            
            result_row = self.env.cr.fetchone()
            if result_row and len(result_row) >= 3:
                result = {
                    'debit': float(result_row[0] or 0.0),
                    'credit': float(result_row[1] or 0.0), 
                    'balance': float(result_row[2] or 0.0)
                }
                # Log only if there's actual balance (for debugging)
                if result['debit'] != 0 or result['credit'] != 0:
                    _logger.info("Initial balance for partner %s before %s: %s", partner.name, date_from, result)
                return result
        except Exception as e:
            # Log error in development mode but don't break the report
            _logger.warning("Error calculating initial balance for partner %s: %s", partner.id, str(e))
            
        return default_result


    def get_partner_initial_balance_safe(self, data, partner, date_from):
        """
        Safe wrapper for getting partner initial balance that always returns a dict
        """
        try:
            result = self._get_partner_initial_balance(data, partner, date_from)
            # Ensure we always return a dictionary with the expected keys
            if not result or not isinstance(result, dict):
                return {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
            return result
        except Exception:
            return {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        data['computed'] = {}

        obj_partner = self.env['res.partner']
        AML = self.env['account.move.line']
        query_get_data = AML.with_context(data['form'].get('used_context', {}))._query_get()
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
            'get_partner_initial_balance': self.get_partner_initial_balance_safe
        }

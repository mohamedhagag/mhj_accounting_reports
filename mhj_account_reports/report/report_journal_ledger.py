import time
import gc
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportJournalLedger(models.AbstractModel):
    """Journal Ledger Report - entries grouped by journal and then by account."""
    _name = 'report.mhj_account_reports.report_journal_ledger'
    _description = 'Journal Ledger Report'

    def _get_journals(self, data):
        """Get journals from wizard form or search all."""
        journal_ids = data.get('form', {}).get('journal_ids', [])
        if journal_ids:
            return self.env['account.journal'].browse(journal_ids)
        return self.env['account.journal'].search([])

    def _get_accounts(self, data):
        """Get accounts from wizard form or search all."""
        account_ids = data.get('form', {}).get('account_ids', [])
        if account_ids:
            return self.env['account.account'].browse(account_ids)
        return self.env['account.account'].search([])

    def _get_query_get_clause(self, data):
        """Get database query clause for filtering move lines."""
        return self.env['account.move.line']._query_get()

    def _get_account_move_entry(self, accounts, journals, date_from, date_to, 
                                target_move, partner_ids=None):
        """Get journal entries for specified accounts and journals."""
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        
        # Build query
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        
        query_get_clause = self._get_query_get_clause({})
        
        domain = [
            ('account_id', 'in', accounts.ids),
            ('journal_id', 'in', journals.ids),
            ('parent_state', 'in', move_state),
        ]
        
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        
        move_lines = MoveLine.search(domain, order='journal_id, account_id, date, id')
        return move_lines

    def _get_account_initial_balance(self, account, journal, date_from):
        """Get account initial balance before date_from for specific journal."""
        if not date_from:
            return 0.0
        
        domain = [
            ('account_id', '=', account.id),
            ('journal_id', '=', journal.id),
            ('date', '<', date_from),
            ('parent_state', '!=', 'cancel'),
        ]
        
        move_lines = self.env['account.move.line'].search(domain)
        balance = sum(line.debit - line.credit for line in move_lines)
        return balance

    def _get_initial_balance(self, account, journal, date_from):
        """Get initial balance for account in journal."""
        return self._get_account_initial_balance(account, journal, date_from)

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate journal ledger report."""
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        company = self.env.company
        
        # Get filters from wizard
        journals = self._get_journals(data)
        accounts = self._get_accounts(data)
        date_from = data['form'].get('date_from')
        date_to = data['form'].get('date_to')
        target_move = data['form'].get('target_move', 'all')
        
        # Get move lines
        move_lines = self._get_account_move_entry(
            accounts, journals, date_from, date_to, target_move
        )
        
        # Group by journal and account
        journals_data = {}
        
        for move_line in move_lines:
            journal_id = move_line.journal_id.id
            account_id = move_line.account_id.id
            
            # Initialize journal
            if journal_id not in journals_data:
                journals_data[journal_id] = {
                    'journal_id': journal_id,
                    'journal_code': move_line.journal_id.code,
                    'journal_name': move_line.journal_id.name,
                    'accounts': {}
                }
            
            # Initialize account
            if account_id not in journals_data[journal_id]['accounts']:
                initial_balance = self._get_initial_balance(
                    move_line.account_id, move_line.journal_id, date_from
                )
                journals_data[journal_id]['accounts'][account_id] = {
                    'account_id': account_id,
                    'account_code': move_line.account_id.code,
                    'account_name': move_line.account_id.name,
                    'initial_balance': initial_balance,
                    'lines': []
                }
            
            # Add move line
            journals_data[journal_id]['accounts'][account_id]['lines'].append({
                'date': move_line.date,
                'move_name': move_line.move_id.name,
                'partner': move_line.partner_id.name if move_line.partner_id else '',
                'ref': move_line.ref or '',
                'label': move_line.name or '',
                'debit': move_line.debit,
                'credit': move_line.credit,
                'balance': 0,  # Will be calculated below
            })
        
        # Calculate running balances and totals
        journal_list = []
        total_debit = 0
        total_credit = 0
        
        for journal_id, journal_data in sorted(journals_data.items(), 
                                              key=lambda x: x[1]['journal_code']):
            account_list = []
            journal_debit = 0
            journal_credit = 0
            
            for account_id, account_data in sorted(journal_data['accounts'].items(),
                                                   key=lambda x: x[1]['account_code']):
                running_balance = account_data['initial_balance']
                account_debit = 0
                account_credit = 0
                
                # Calculate running balance for each line
                for line in account_data['lines']:
                    running_balance += line['debit'] - line['credit']
                    line['balance'] = running_balance
                    account_debit += line['debit']
                    account_credit += line['credit']
                
                account_list.append({
                    'account_code': account_data['account_code'],
                    'account_name': account_data['account_name'],
                    'account_id': account_id,
                    'initial_balance': account_data['initial_balance'],
                    'lines': account_data['lines'],
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_data['initial_balance'] + account_debit - account_credit,
                })
                
                journal_debit += account_debit
                journal_credit += account_credit
            
            journal_list.append({
                'journal_code': journal_data['journal_code'],
                'journal_name': journal_data['journal_name'],
                'journal_id': journal_id,
                'accounts': account_list,
                'debit': journal_debit,
                'credit': journal_credit,
            })
            
            total_debit += journal_debit
            total_credit += journal_credit
        
        return {
            'data': data['form'],
            'company': company,
            'date_from': date_from,
            'date_to': date_to,
            'journals': journal_list,
            'total_debit': total_debit,
            'total_credit': total_credit,
        }

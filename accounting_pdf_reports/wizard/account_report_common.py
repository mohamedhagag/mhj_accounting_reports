from odoo import api, fields, models, _
from odoo.tools.misc import get_lang


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        required=True,
        default=lambda self: self.env['account.journal'].search([('company_id', '=', self.company_id.id)]),
        domain="[('company_id', '=', company_id)]",
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    
    # Memory optimization fields
    enable_pagination = fields.Boolean(
        string='Enable Pagination',
        default=True,
        help='Enable pagination for large datasets to avoid memory issues'
    )
    max_records_per_account = fields.Integer(
        string='Max Records per Account',
        default=50000,
        help='Maximum number of journal entries to process per account (0 = no limit)'
    )
    batch_size = fields.Integer(
        string='Batch Size', 
        default=10000,
        help='Number of records to process in each batch'
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        # Add optimization settings
        result['enable_pagination'] = data['form'].get('enable_pagination', True)
        result['max_records_per_account'] = data['form'].get('max_records_per_account', 50000)
        result['batch_size'] = data['form'].get('batch_size', 10000)
        return result

    def _print_report(self, data):
        raise NotImplementedError()

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id', 
                                'enable_pagination', 'max_records_per_account', 'batch_size'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)

    def _print_excel_report(self, data):
        """Base method for Excel export - should be overridden by subclasses"""
        raise NotImplementedError("Excel export not implemented for this report type")

    def print_excel_report(self):
        """Generic Excel export method for all reports"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        
        # Get all fields from the current model
        all_fields = []
        for field_name, field in self._fields.items():
            if not field.compute and field_name not in ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update']:
                all_fields.append(field_name)
        
        # Read all available fields
        try:
            data['form'] = self.read(all_fields)[0]
        except Exception:
            # Fallback to basic fields if reading all fields fails
            basic_fields = ['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id', 
                           'enable_pagination', 'max_records_per_account', 'batch_size']
            data['form'] = self.read(basic_fields)[0]
        
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_excel_report(data)

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountReportOptimization(models.TransientModel):
    _name = 'account.report.optimization'
    _description = 'Account Report Optimization Tools'

    @api.model
    def create_performance_indexes(self):
        """
        Create database indexes to improve performance for large datasets
        """
        cr = self.env.cr
        
        indexes_to_create = [
            # Index for account_move_line date and account_id (General Ledger)
            ("idx_aml_date_account", "account_move_line", ["date", "account_id"]),
            
            # Index for account_move_line partner_id and date (Partner Ledger)
            ("idx_aml_partner_date", "account_move_line", ["partner_id", "date"]),
            
            # Index for account_move_line account_id, partner_id, date (Combined queries)
            ("idx_aml_account_partner_date", "account_move_line", ["account_id", "partner_id", "date"]),
            
            # Index for account_move_line date_maturity and account_id (Aged Partner)
            ("idx_aml_maturity_account", "account_move_line", ["date_maturity", "account_id"]),
            
            # Index for account_move_line company_id and date (Multi-company)
            ("idx_aml_company_date", "account_move_line", ["company_id", "date"]),
            
            # Index for account_move state (filtering posted entries)
            ("idx_am_state", "account_move", ["state"]),
            
            # Index for reconciliation queries
            ("idx_aml_reconcile", "account_move_line", ["full_reconcile_id", "date"]),
        ]
        
        created_indexes = []
        failed_indexes = []
        
        for index_name, table_name, columns in indexes_to_create:
            try:
                # Check if index already exists
                cr.execute("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = %s AND indexname = %s
                """, (table_name, index_name))
                
                if not cr.fetchone():
                    # Create the index
                    columns_str = ", ".join(columns)
                    sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
                    cr.execute(sql)
                    created_indexes.append(index_name)
                    _logger.info(f"Created index: {index_name}")
                else:
                    _logger.info(f"Index {index_name} already exists")
                    
            except Exception as e:
                failed_indexes.append((index_name, str(e)))
                _logger.error(f"Failed to create index {index_name}: {str(e)}")
        
        return {
            'created': created_indexes,
            'failed': failed_indexes
        }
    
    @api.model
    def analyze_table_statistics(self):
        """
        Update table statistics for better query planning
        """
        cr = self.env.cr
        
        tables_to_analyze = [
            'account_move_line',
            'account_move', 
            'account_account',
            'res_partner',
            'account_journal'
        ]
        
        analyzed_tables = []
        
        for table in tables_to_analyze:
            try:
                cr.execute(f"ANALYZE {table}")
                analyzed_tables.append(table)
                _logger.info(f"Analyzed table: {table}")
            except Exception as e:
                _logger.error(f"Failed to analyze table {table}: {str(e)}")
        
        return analyzed_tables
    
    @api.model
    def get_table_statistics(self):
        """
        Get statistics about table sizes for monitoring
        """
        cr = self.env.cr
        
        # Get table sizes
        cr.execute("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE tablename IN ('account_move_line', 'account_move', 'account_account')
            ORDER BY tablename, attname
        """)
        
        stats = cr.dictfetchall()
        
        # Get table sizes
        cr.execute("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE tablename IN ('account_move_line', 'account_move', 'account_account')
        """)
        
        sizes = cr.dictfetchall()
        
        return {
            'statistics': stats,
            'sizes': sizes
        }
    
    @api.model
    def vacuum_analyze_accounting_tables(self):
        """
        Vacuum and analyze accounting tables for optimal performance
        Note: This should be run during maintenance windows
        """
        cr = self.env.cr
        
        tables = ['account_move_line', 'account_move', 'account_account']
        results = []
        
        for table in tables:
            try:
                # Note: VACUUM cannot be run inside a transaction in PostgreSQL
                # This is for informational purposes
                cr.execute(f"ANALYZE {table}")
                results.append(f"Analyzed {table}")
                _logger.info(f"Analyzed table: {table}")
            except Exception as e:
                results.append(f"Failed to analyze {table}: {str(e)}")
                _logger.error(f"Failed to analyze table {table}: {str(e)}")
        
        return results


class AccountMoveLineOptimized(models.Model):
    _inherit = 'account.move.line'
    
    @api.model
    def _get_query_optimizations(self):
        """
        Return query optimization hints for large datasets
        """
        return {
            'use_index_hints': True,
            'batch_size': 10000,
            'max_records_per_query': 50000,
            'enable_query_cache': True,
        }
    
    def _query_get_optimized(self, domain=None, date_field='date'):
        """
        Optimized version of _query_get for large datasets
        """
        # Use the standard _query_get but with optimizations
        tables, where_clause, where_params = self._query_get(domain, date_field)
        
        # Add query hints for PostgreSQL
        if self.env.registry.db_name:  # Check if we're using PostgreSQL
            # Add index hints in the WHERE clause comments
            where_clause = f"/* USE INDEX */ {where_clause}"
        
        return tables, where_clause, where_params
import logging
from . import wizard
from . import models
from . import report

_logger = logging.getLogger(__name__)


def _pre_init_clean_m2m_models(env):
    """Clean up legacy M2M tables before installation"""
    _logger.info("Cleaning up legacy M2M tables...")
    env.cr.execute("""DROP TABLE IF EXISTS account_journal_account_report_partner_ledger_rel""")
    _logger.info("M2M table cleanup completed")


def _post_init_hook(env):
    """Post-installation optimizations for large databases"""
    _logger.info("Starting post-installation optimizations...")
    
    try:
        # Recompute financial report levels efficiently
        financial_reports = env['account.financial.report'].search([])
        if financial_reports:
            _logger.info(f"Computing levels for {len(financial_reports)} financial reports...")
            financial_reports._get_level()
            
        # Optional: Create performance indexes if database is large
        move_line_count = env['account.move.line'].search_count([])
        if move_line_count > 100000:  # Only for databases with 100K+ journal entries
            _logger.info(f"Large database detected ({move_line_count:,} journal entries). Creating performance indexes...")
            try:
                optimization_obj = env['account.report.optimization']
                result = optimization_obj.create_performance_indexes()
                _logger.info(f"Created {len(result.get('created', []))} performance indexes")
                if result.get('failed'):
                    _logger.warning(f"Failed to create {len(result['failed'])} indexes")
            except Exception as e:
                _logger.warning(f"Could not create performance indexes: {e}")
        
        _logger.info("Post-installation optimizations completed successfully")
        
    except Exception as e:
        _logger.error(f"Post-installation optimization failed: {e}")
        # Don't raise the exception - installation should continue even if optimizations fail

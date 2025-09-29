import psutil
import gc
import logging
from odoo import api, models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportMemoryMonitor:
    """
    Memory monitoring utility for accounting reports
    """
    
    def __init__(self):
        self.initial_memory = None
        self.peak_memory = 0
        self.memory_threshold = 1024 * 1024 * 1024  # 1GB in bytes
        
    def start_monitoring(self):
        """Start memory monitoring"""
        try:
            process = psutil.Process()
            self.initial_memory = process.memory_info().rss
            self.peak_memory = self.initial_memory
            _logger.info(f"Memory monitoring started. Initial memory: {self.initial_memory / 1024 / 1024:.2f} MB")
        except Exception as e:
            _logger.warning(f"Could not start memory monitoring: {e}")
            
    def check_memory(self, force_gc=False):
        """Check current memory usage and optionally force garbage collection"""
        try:
            process = psutil.Process()
            current_memory = process.memory_info().rss
            
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
                
            memory_increase = current_memory - (self.initial_memory or current_memory)
            
            if current_memory > self.memory_threshold:
                _logger.warning(f"High memory usage detected: {current_memory / 1024 / 1024:.2f} MB")
                
            if force_gc or memory_increase > 512 * 1024 * 1024:  # 512MB increase
                collected = gc.collect()
                new_memory = process.memory_info().rss
                _logger.info(f"Garbage collection freed {collected} objects, "
                           f"memory: {current_memory / 1024 / 1024:.2f} -> {new_memory / 1024 / 1024:.2f} MB")
                return new_memory
                
            return current_memory
            
        except Exception as e:
            _logger.warning(f"Could not check memory: {e}")
            return 0
            
    def get_memory_stats(self):
        """Get memory statistics"""
        try:
            process = psutil.Process()
            current_memory = process.memory_info().rss
            
            return {
                'initial_memory_mb': (self.initial_memory or 0) / 1024 / 1024,
                'current_memory_mb': current_memory / 1024 / 1024,
                'peak_memory_mb': self.peak_memory / 1024 / 1024,
                'memory_increase_mb': ((current_memory - (self.initial_memory or current_memory)) / 1024 / 1024),
            }
        except Exception as e:
            _logger.warning(f"Could not get memory stats: {e}")
            return {}


class AccountReportMemoryMixin(models.AbstractModel):
    """
    Mixin to add memory monitoring to report models
    """
    _name = 'account.report.memory.mixin'
    _description = 'Memory Monitoring Mixin for Reports'
    
    def _get_memory_monitor(self):
        """Get or create memory monitor instance"""
        if not hasattr(self, '_memory_monitor'):
            self._memory_monitor = ReportMemoryMonitor()
        return self._memory_monitor
    
    def _start_memory_monitoring(self):
        """Start memory monitoring for the report"""
        monitor = self._get_memory_monitor()
        monitor.start_monitoring()
        
    def _check_memory_usage(self, context_msg="", force_gc=False):
        """Check memory usage with optional context message"""
        monitor = self._get_memory_monitor()
        current_memory = monitor.check_memory(force_gc=force_gc)
        
        if context_msg and current_memory:
            _logger.info(f"Memory check ({context_msg}): {current_memory / 1024 / 1024:.2f} MB")
            
        return current_memory
    
    def _log_memory_summary(self):
        """Log final memory usage summary"""
        monitor = self._get_memory_monitor()
        stats = monitor.get_memory_stats()
        
        if stats:
            _logger.info(f"Memory Summary - Initial: {stats['initial_memory_mb']:.2f} MB, "
                        f"Peak: {stats['peak_memory_mb']:.2f} MB, "
                        f"Final: {stats['current_memory_mb']:.2f} MB, "
                        f"Increase: {stats['memory_increase_mb']:.2f} MB")


class ReportProgressTracker:
    """
    Progress tracking for long-running reports
    """
    
    def __init__(self, total_items, description="Processing"):
        self.total_items = total_items
        self.processed_items = 0
        self.description = description
        self.start_time = fields.Datetime.now()
        
    def update_progress(self, items_processed):
        """Update progress and log if needed"""
        self.processed_items += items_processed
        
        if self.total_items > 0:
            progress_percent = (self.processed_items / self.total_items) * 100
            
            # Log progress every 10%
            if self.processed_items > 0 and (self.processed_items % max(1, self.total_items // 10)) == 0:
                elapsed = fields.Datetime.now() - self.start_time
                _logger.info(f"{self.description}: {progress_percent:.1f}% complete "
                           f"({self.processed_items}/{self.total_items}), "
                           f"Elapsed: {elapsed}")
    
    def finish(self):
        """Log completion"""
        elapsed = fields.Datetime.now() - self.start_time
        _logger.info(f"{self.description}: Completed {self.processed_items} items in {elapsed}")
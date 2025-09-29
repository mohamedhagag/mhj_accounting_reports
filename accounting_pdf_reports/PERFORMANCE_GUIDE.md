# Odoo 18 Accounting Reports - Performance Optimization Guide

This module has been optimized to handle millions of journal items efficiently while avoiding out-of-memory issues.

## Key Performance Improvements

### 1. Memory Management
- **Batch Processing**: Reports process data in configurable batches (default: 10,000 records)
- **Pagination**: Large datasets are paginated to avoid loading all data into memory
- **Garbage Collection**: Automatic memory cleanup after each batch
- **Memory Monitoring**: Built-in monitoring to track memory usage during report generation

### 2. Database Optimizations
- **Optimized SQL Queries**: Improved JOIN structures and WHERE clauses
- **Database Indexing**: Automatic creation of performance indexes
- **Query Limitations**: Configurable limits on records per account/partner
- **Batch Account Processing**: Accounts processed in batches to control memory

### 3. Configuration Options

Each report wizard now includes performance options:

- **Enable Pagination**: Toggle pagination on/off (recommended: ON for large datasets)
- **Max Records per Account**: Limit journal entries per account (default: 50,000)
- **Batch Size**: Number of records processed per batch (default: 10,000)

## Recommended Settings for Large Datasets

### For databases with 1M+ journal items:
```
Enable Pagination: ✓ Yes
Max Records per Account: 50,000
Batch Size: 10,000
```

### For databases with 10M+ journal items:
```
Enable Pagination: ✓ Yes  
Max Records per Account: 25,000
Batch Size: 5,000
```

### For databases with 100M+ journal items:
```
Enable Pagination: ✓ Yes
Max Records per Account: 10,000
Batch Size: 2,000
```

## Database Optimization Tools

Access **Accounting > Reports > Performance Tools** to:

1. **Create Performance Indexes**: Add database indexes for faster queries
2. **Update Table Statistics**: Refresh database statistics for optimal query planning
3. **View Table Statistics**: Monitor database table sizes and performance metrics

### Recommended Indexes

The module automatically creates these performance indexes:

- `idx_aml_date_account`: account_move_line (date, account_id)
- `idx_aml_partner_date`: account_move_line (partner_id, date)  
- `idx_aml_account_partner_date`: account_move_line (account_id, partner_id, date)
- `idx_aml_maturity_account`: account_move_line (date_maturity, account_id)
- `idx_aml_company_date`: account_move_line (company_id, date)
- `idx_am_state`: account_move (state)
- `idx_aml_reconcile`: account_move_line (full_reconcile_id, date)

## Memory Monitoring

The system automatically logs memory usage during report generation:

```
INFO: Memory monitoring started. Initial memory: 256.34 MB
INFO: Memory check (Before processing accounts): 512.67 MB  
INFO: Garbage collection freed 1247 objects, memory: 512.67 -> 387.23 MB
INFO: Memory Summary - Initial: 256.34 MB, Peak: 512.67 MB, Final: 387.23 MB
```

## Troubleshooting Performance Issues

### Issue: Reports still running out of memory
**Solution**: 
1. Reduce batch size to 5,000 or 2,000
2. Reduce max records per account to 25,000 or 10,000
3. Filter reports by date range
4. Process fewer accounts at once

### Issue: Reports running too slowly
**Solution**:
1. Create performance indexes via Performance Tools
2. Update table statistics regularly
3. Consider running during off-peak hours
4. Increase batch size if memory allows

### Issue: Database performance degradation
**Solution**:
1. Run `ANALYZE` on accounting tables regularly
2. Consider `VACUUM ANALYZE` during maintenance windows  
3. Monitor table sizes via Performance Tools
4. Archive old journal entries if possible

## Best Practices

1. **Regular Maintenance**: 
   - Create indexes after initial setup
   - Update statistics weekly
   - Monitor memory usage patterns

2. **Report Usage**:
   - Use date filters to limit data scope
   - Run large reports during off-peak hours
   - Consider exporting to Excel for very large datasets

3. **System Resources**:
   - Ensure adequate RAM (8GB+ recommended for large datasets)
   - Use SSD storage for better I/O performance
   - Monitor database connection limits

4. **Data Management**:
   - Archive old fiscal years when possible
   - Regular database maintenance (VACUUM, REINDEX)
   - Monitor journal entry growth patterns

## Technical Details

### Memory Optimization Classes

- `ReportMemoryMonitor`: Tracks memory usage during report generation
- `AccountReportMemoryMixin`: Mixin for adding memory monitoring to reports
- `ReportProgressTracker`: Tracks progress for long-running operations

### Optimized Report Methods

- `_get_account_move_entry()`: Batch processing for General Ledger
- `_lines()`: Pagination for Partner Ledger  
- `_get_accounts()`: Batch processing for Trial Balance
- `_get_partner_move_lines()`: Batch processing for Aged Partner Balance

## Support and Updates

For questions or issues related to performance optimization:
- Check the system logs for memory usage patterns
- Use the Performance Tools to monitor database health  
- Adjust batch sizes based on your system capabilities
- Contact support with memory usage logs if issues persist
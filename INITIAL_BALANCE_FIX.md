# Initial Balance Fix Summary

## Root Cause of Zero Initial Balance

The initial balance was always showing as zero because of a critical issue in the `_get_partner_initial_balance` method:

### Problem:
The method was using `AML.with_context(data['form'].get('used_context', {}))._query_get()` which includes date filters from the form context. When calculating initial balance, we need data **before** the `date_from`, but the context was filtering out that data.

### Solution:
1. **Removed dependency on `query_get()`** for initial balance calculation
2. **Used direct SQL query** without date-filtered context
3. **Simplified the query** to avoid context conflicts

### Key Changes:

#### Before (Broken):
```python
# Used query_get() with date-filtered context
query_get_data = AML.with_context(data['form'].get('used_context', {}))._query_get()
# This filtered out data before date_from, making initial balance always zero
```

#### After (Fixed):
```python
# Direct SQL query without context filtering
query = '''SELECT COALESCE(SUM(aml.debit), 0.0) as initial_debit,
                  COALESCE(SUM(aml.credit), 0.0) as initial_credit,
                  COALESCE(SUM(aml.debit - aml.credit), 0.0) as initial_balance
           FROM account_move_line aml
           JOIN account_move am ON (am.id = aml.move_id)
           WHERE aml.partner_id = %s
               AND am.state IN %s
               AND aml.account_id IN %s
               AND aml.date < %s'''
```

## Expected Results:

### PDF Report:
- Initial balance row will now show actual balances (when they exist)
- Row appears when `initial_balance` checkbox is checked
- Shows zeros when no initial balance exists

### XLSX Report:
- Initial balance lines appear as first entries with yellow background
- Shows actual calculated balances from before `date_from`
- Properly formatted and integrated with other lines

## Testing:
1. Generate Partner Ledger with `date_from` set and `initial_balance` checked
2. Check that initial balance shows actual amounts, not zeros
3. Verify both PDF and XLSX formats work correctly

The fix ensures that initial balance calculation gets all data before the specified date without being filtered by the report's date context.
# Fix for Excel Export Action Error

## Problem
The error "print_excel_report is not a valid action on account.common.report" occurred because the Excel export button was trying to call a method that didn't exist in the base report class.

## Solution Implemented

### 1. Base Class Enhancement
Added the `print_excel_report()` method to the base `account.common.report` class in `wizard/account_report_common.py`:

- **Generic implementation**: Works for all report types by reading all available fields
- **Extensible design**: Calls `_print_excel_report()` which subclasses override
- **Error handling**: Graceful fallback if field reading fails

### 2. Subclass Implementation
Updated all specific report wizards to implement `_print_excel_report()`:

- **General Ledger** (`account_general_ledger.py`): Adds initial_balance and sortby fields
- **Partner Ledger** (`account_partner_ledger.py`): Adds partner selection and currency options  
- **Trial Balance** (`account_trial_balance.py`): Adds display_account and analytic_account_ids

### 3. Dynamic Excel Class Loading
Enhanced Excel report classes in `report/report_excel.py`:

- **Conditional inheritance**: Only inherit from `report.report_xlsx.abstract` if available
- **Runtime detection**: Check if `report_xlsx` module is installed
- **Clear error messages**: Guide users to install missing dependencies
- **Graceful degradation**: No crashes if Excel functionality unavailable

## Benefits

✅ **Universal compatibility**: Excel button works on all report forms
✅ **Extensible architecture**: Easy to add Excel export to new reports  
✅ **Robust error handling**: Clear messages when dependencies missing
✅ **No breaking changes**: Existing PDF functionality unchanged
✅ **Dynamic loading**: Adapts to available modules at runtime

## Usage

Users can now click the **"Export Excel"** button on any supported report form:
1. Configure report parameters (dates, filters, etc.)
2. Click **"Export Excel"** instead of **"Print PDF"**  
3. Excel file downloads automatically with professional formatting

The fix ensures the Excel export feature works consistently across all accounting reports while maintaining backward compatibility with the PDF export functionality.
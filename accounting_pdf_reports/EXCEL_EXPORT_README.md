# Excel Export for Accounting Reports

This module now supports Excel (XLSX) export for major accounting reports alongside the existing PDF reports.

## Features

### Supported Reports
- **General Ledger**: Export detailed account movements with running balances
- **Partner Ledger**: Export partner-wise account movements and balances  
- **Trial Balance**: Export account summaries with debit/credit totals

### Excel Export Features
- **Professional formatting**: Headers, borders, number formatting
- **Multiple worksheets**: Each report type gets its own formatted worksheet
- **Automatic column sizing**: Optimal widths for data readability
- **Summary totals**: Account and partner subtotals with grand totals
- **Date formatting**: Proper date display in Excel format
- **Currency formatting**: Numbers formatted with proper decimal places

## How to Use

### Requirements
1. Install the `report_xlsx` module in your Odoo instance
2. Install the `xlsxwriter` Python library:
   ```bash
   pip install xlsxwriter
   ```

### Generating Excel Reports

1. Navigate to **Accounting > Reporting**
2. Select your desired report (General Ledger, Partner Ledger, or Trial Balance)
3. Configure your report parameters (date range, journals, etc.)
4. Click **"Export Excel"** instead of **"Print PDF"**
5. The Excel file will be automatically downloaded

### Report Content

#### General Ledger Excel Export
- Report parameters (date range, target moves)
- Account-wise breakdown with:
  - Move lines with date, journal, partner, reference
  - Debit, credit, and running balance amounts
  - Account subtotals

#### Partner Ledger Excel Export  
- Report parameters and filters
- Partner-wise breakdown with:
  - Transaction details by date
  - Account information and move references
  - Partner balances and totals
  - Currency information when applicable

#### Trial Balance Excel Export
- Summary of all accounts with:
  - Account code and name
  - Total debits and credits
  - Account balances
  - Grand totals

## Technical Implementation

### Architecture
- Conditional imports handle environments without `report_xlsx`
- Separate Excel report models inherit from `report.report_xlsx.abstract`
- Existing report logic is reused for data generation
- Professional Excel formatting with corporate styling

### Error Handling
- Graceful degradation when Excel dependencies are missing
- Clear error messages guide users to install required modules
- No impact on existing PDF report functionality

### Performance
- Leverages existing optimized report queries
- Memory-efficient processing for large datasets
- Same batching and pagination as PDF reports

## Installation Notes

If you encounter issues:
1. Ensure `report_xlsx` module is installed and activated
2. Verify `xlsxwriter` Python library is available
3. Check module dependencies in `__manifest__.py`
4. Restart Odoo service after installing dependencies

The Excel export feature is optional - PDF reports continue to work normally even if Excel dependencies are not available.
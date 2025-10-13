# Hajjaj.Pro Accounting Financial Reports

This module provides comprehensive financial reports for Odoo, with advanced performance optimizations for handling millions of journal items. It also supports professional Excel (XLSX) export for major accounting reports.

---

## Installation

1. Download the module and add it to your Odoo addons folder.
2. Log on to your Odoo server and go to the Apps menu.
3. Trigger debug mode and update the list by clicking on the "Update Apps List" link.
4. Install the module by clicking on the install button.

## Upgrade

1. Download the module and add it to your Odoo addons folder.
2. Restart the server and log on to your Odoo server.
3. Select the Apps menu and upgrade the module by clicking on the upgrade button.

---

## Features

### Financial Reports
* General Ledger
* Partner Ledger **With Invoice line details**
* Trial Balance
* Journal Audit
* Tax Report
* Aged Partner Balance
* Profit and Loss
* Balance Sheet

### Excel Export

This module supports Excel (XLSX) export for major accounting reports alongside the existing PDF reports.

#### Supported Reports
- **General Ledger**: Export detailed account movements with running balances
- **Partner Ledger**: Export partner-wise account movements and balances
- **Trial Balance**: Export account summaries with debit/credit totals

#### Excel Export Features
- **Professional formatting**: Headers, borders, number formatting
- **Multiple worksheets**: Each report type gets its own formatted worksheet
- **Automatic column sizing**: Optimal widths for data readability
- **Summary totals**: Account and partner subtotals with grand totals
- **Date formatting**: Proper date display in Excel format
- **Currency formatting**: Numbers formatted with proper decimal places

#### How to Use Excel Export

1. Install the `report_xlsx` module in your Odoo instance
2. Install the `xlsxwriter` Python library:
	 ```bash
	 pip install xlsxwriter
	 ```
3. Navigate to **Accounting > Reporting**
4. Select your desired report (General Ledger, Partner Ledger, or Trial Balance)
5. Configure your report parameters (date range, journals, etc.)
6. Click **"Export Excel"** instead of **"Print PDF"**
7. The Excel file will be automatically downloaded

##### Report Content

**General Ledger Excel Export**
- Report parameters (date range, target moves)
- Account-wise breakdown with:
	- Move lines with date, journal, partner, reference
	- Debit, credit, and running balance amounts
	- Account subtotals

**Partner Ledger Excel Export**
- Report parameters and filters
- Partner-wise breakdown with:
	- Transaction details by date
	- Account information and move references
	- Partner balances and totals
	- Currency information when applicable

**Trial Balance Excel Export**
- Summary of all accounts with:
	- Account code and name
	- Total debits and credits
	- Account balances
	- Grand totals

##### Technical Implementation
- Conditional imports handle environments without `report_xlsx`
- Separate Excel report models inherit from `report.report_xlsx.abstract`
- Existing report logic is reused for data generation
- Professional Excel formatting with corporate styling

##### Error Handling
- Graceful degradation when Excel dependencies are missing
- Clear error messages guide users to install required modules
- No impact on existing PDF report functionality

##### Performance
- Leverages existing optimized report queries
- Memory-efficient processing for large datasets
- Same batching and pagination as PDF reports

##### Installation Notes

If you encounter issues:
1. Ensure `report_xlsx` module is installed and activated
2. Verify `xlsxwriter` Python library is available
3. Check module dependencies in `__manifest__.py`
4. Restart Odoo service after installing dependencies

The Excel export feature is optional - PDF reports continue to work normally even if Excel dependencies are not available.

---

## Performance Optimization Guide

This module has been optimized to handle millions of journal items efficiently while avoiding out-of-memory issues.

### Key Performance Improvements

#### 1. Memory Management
- **Batch Processing**: Reports process data in configurable batches (default: 10,000 records)
- **Pagination**: Large datasets are paginated to avoid loading all data into memory
- **Garbage Collection**: Automatic memory cleanup after each batch
- **Memory Monitoring**: Built-in monitoring to track memory usage during report generation

#### 2. Database Optimizations
- **Optimized SQL Queries**: Improved JOIN structures and WHERE clauses
- **Database Indexing**: Automatic creation of performance indexes
- **Query Limitations**: Configurable limits on records per account/partner
- **Batch Account Processing**: Accounts processed in batches to control memory

#### 3. Configuration Options

Each report wizard now includes performance options:

- **Enable Pagination**: Toggle pagination on/off (recommended: ON for large datasets)
- **Max Records per Account**: Limit journal entries per account (default: 50,000)
- **Batch Size**: Number of records processed per batch (default: 10,000)

#### Memory Monitoring Example

The system automatically logs memory usage during report generation:

```
INFO: Memory monitoring started. Initial memory: 256.34 MB
INFO: Memory check (Before processing accounts): 512.67 MB  
INFO: Garbage collection freed 1247 objects, memory: 512.67 -> 387.23 MB
INFO: Memory Summary - Initial: 256.34 MB, Peak: 512.67 MB, Final: 387.23 MB
```

#### Automatic Optimizations

This module automatically performs the following optimizations:

1. Create performance database indexes
2. Update table statistics
3. Monitor database health

---

## Credits

### Contributors

* Hajjaj.Pro <odooapps@hajjaj.pro>

### Author & Maintainer

This module is maintained by Hajjaj.Pro
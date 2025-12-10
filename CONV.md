# Conversation Log & Development Guide

**Started**: December 9, 2025  
**Last Updated**: December 10, 2025 - Full Day Session: Filter Fixes + UI Improvements + P&L Report  
**Session**: Interactive Reports - Comprehensive Filter Implementation, UI Redesign & New Report

---

## SESSION SUMMARY (Dec 10, 2025 - COMPLETE)

### Accomplishments
1. ✅ **Fixed Interactive Reports Filtering** - All 5 main reports now honor all filter selections
2. ✅ **Fixed Partner Ledger Calculations** - Initial balance, running sum, and totals now correct
3. ✅ **Compacted Filter Panel** - Removed dropdown lists, kept search inputs
4. ✅ **Added Odoo-Style Searchable Dropdowns** - Search filters appear on typing (like Odoo)
5. ✅ **Created Interactive P&L Report** - New profit & loss statement with hierarchical display
6. ✅ **Updated Documentation** - CONV.md now complete with session history

### Commits Pushed
| Commit | Message |
|--------|---------|
| `4092c5f` | Fix interactive reports filtering & Partner Ledger calculations |
| `518c19a` | Compact filter panel by hiding dropdown lists |
| `2a7dd5d` | Add Odoo-style searchable dropdowns to filter panel |
| `ebd85e6` | Add interactive Profit & Loss report |

### Problem Resolution

**Issue 1: Partial/Broken Filtering**
- **Root Cause**: Context not properly propagating account_ids, partner_ids, analytic_account_ids
- **Solution**: Added explicit context assignment in all controller methods (TB, GL, PL)
- **Files Modified**: `controllers/main.py`
- **Status**: ✅ FIXED

**Issue 2: Partner Ledger Calculation Errors**
- **Root Causes**: 
  - Initial balance query missing journal filter
  - _sum_partner() removing date_from (calculating all-time instead of period totals)
- **Solutions**:
  - Added journal filter to _get_partner_initial_balance()
  - Preserved date_from in _sum_partner() context
  - Added analytic_account_ids to context
- **Files Modified**: `report/report_partner_ledger.py`, `controllers/main.py`
- **Status**: ✅ FIXED

**Issue 3: Filter Panel Too Large**
- **Root Cause**: Dropdown lists showing 4 items under each search field
- **Solution**: Hid dropdown lists when not typing, show on search (conditional rendering)
- **Files Modified**: `static/src/xml/financial_reports_templates.xml`
- **Result**: Compact panel with Odoo-style search behavior

**Issue 4: No P&L Report**
- **Solution**: Created complete interactive P&L report using existing financial report model
- **Files Created**: `static/src/js/profit_loss_report.js`
- **Files Modified**: `controllers/main.py`, `views/interactive_reports.xml`, `static/src/xml/financial_reports_templates.xml`, `CONV.md`
- **Status**: ✅ COMPLETE

### Current Interactive Reports (6 total)
- ✅ **Trial Balance** - Full account hierarchy with debit/credit/balance
- ✅ **General Ledger** - Account movements with optional initial balance
- ✅ **Partner Ledger** - Partner-centric view with running balance
- ✅ **Cash Flow** - Operating/Investing/Financing activities
- ✅ **Balance Sheet** - Assets vs Liabilities & Equity (2-column layout)
- ✅ **Profit & Loss** - Hierarchical income statement (NEW)

### All Filter Options Now Working
**Common Filters** (all reports):
- ✅ Date range (date_from, date_to)
- ✅ Entry status (posted/all)
- ✅ Journals (multi-select searchable)
- ✅ Accounts (multi-select searchable)
- ✅ Partners (multi-select searchable)
- ✅ Analytic Accounts (multi-select searchable)
- ✅ Display Account Mode (all/movement/not_zero)

**Report-Specific Filters**:
- **General Ledger**: Sort Order + Initial Balance checkbox
- **Partner Ledger**: Partner Type + Reconciled + Currency + Initial Balance
- **All Others**: Standard filters only

---

## CURRENT TASK (Dec 10, 2025) - ✅ COMPLETED
**Issue**: Interactive reports have partial/broken filtering + Partner Ledger calculation errors
**Status**: PDF/Excel work fine; fixed interactive reports
**Results**: 
1. ✅ All filter options now propagate correctly to all interactive ledger reports
2. ✅ Partner Ledger calculations fixed (initial balance, running sum, totals)
3. ✅ Verified Journal Ledger does NOT have interactive version (documented as missing)
4. ✅ Filter panel redesigned with Odoo-style search dropdowns
5. ✅ New interactive P&L report created

### Fixes Applied
**Partner Ledger Calculations** (`report/report_partner_ledger.py`):
1. `_get_partner_initial_balance()`: Now applies journal filter from context
2. `_sum_partner()`: Preserves date_from to calculate period totals (not all-time)
3. Both methods now correctly honor all filters (journals, dates, reconciled status)

**Filter Context Propagation** (`controllers/main.py`):
1. Trial Balance: Added explicit context assignment for account_ids, partner_ids, analytic_account_ids
2. General Ledger: Ensured all filter IDs are properly set in context
3. Partner Ledger: Added analytic_account_ids and account_ids to context
4. Profit & Loss: New endpoint with full filter support

**Filter Panel UI** (`static/src/xml/financial_reports_templates.xml`):
1. Dropdowns appear only when typing (searchable like Odoo)
2. Max height 200px with scroll for long lists
3. Shows selection count + clear button
4. Compact design without pre-populated dropdown items

---

## Project Overview

### **mhj_accounting_reports** - Odoo 18 Advanced Accounting Reports Module
- **Version**: 18.0.1.3 (Odoo 18)
- **License**: AGPL-3
- **Purpose**: Comprehensive financial reporting with performance optimizations for millions of journal items
- **Target**: Hajjaj.Pro accounting solution with Excel export support
- **Branch**: 18-dyn
- **Interactive Reports**: OWL-based JavaScript components with JSON endpoints (6 reports)

---

## Key Architecture Components

### 1. **Models** (`models/`)
- **account_financial_report.py**: Hierarchical financial report structure with efficient level computation
  - `_get_level()`: Optimized recursive level calculation using parent-child mapping
  - Supports: View, Accounts, Account Type, Report Value types
  - Field: `level` (computed, recursive)
  
- **account_move_line.py**: **CRITICAL OVERRIDE** - Extends `account.move.line`
  - `_query_get(domain)`: Completely overridden method for custom SQL filtering
  - **Odoo 18 Changes Implemented**:
    - Uses `parent_state` instead of `move_id.state` 
    - Handles `analytic_distribution` JSONB field (not `analytic_account_id`)
    - Supports `aged_balance` context for date_maturity filtering
    - Returns: `(tables, where_clause, where_clause_params)` tuple
  
- **account_optimization.py**: Database performance tools (indexes, statistics)
- **memory_monitor.py**: Optional memory tracking via psutil

### 2. **Wizards** (`wizard/`) - TransientModels for Report Generation
**Base Hierarchy**:
```
account.common.report (base)
  ├─ account.common.account.report
  └─ account.common.partner.report
```

**Base Fields** (account.common.report):
- `company_id`, `journal_ids`, `date_from`, `date_to`, `target_move`
- **Performance Fields**: `enable_pagination`, `max_records_per_account`, `batch_size`

**Report-Specific Wizards**:
- `account.report.general.ledger` - General Ledger (initial_balance, sortby)
- `account.report.partner.ledger` - Partner Ledger (amount_currency, reconciled)
- `account.balance.report` - Trial Balance
- `account.tax.report.wizard` - Tax Report
- `account.aged.trial.balance` - Aged Partner Balance
- `account.print.journal` - Journal Audit/Ledger
- `accounting.report` - Financial Reports

**Flow**: User inputs → `check_report()` → `_build_contexts()` → `_print_report()` or `_print_excel_report()`

### 3. **Reports** (`report/`) - AbstractModels
**Implements** `_get_report_values(docids, data)` for report data generation

**Performance Patterns** (General Ledger Example):
```python
BATCH_SIZE = 10000  # Process accounts in batches
MOVE_LINE_LIMIT = 50000  # Limit per account
# Batch processing with gc.collect() between batches
account_batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
```

**Report Models**:
- `report.mhj_account_reports.report_general_ledger`
- `report.mhj_account_reports.report_partnerledger`
- `report.mhj_account_reports.report_trialbalance`
- `report.mhj_account_reports.report_tax`
- `report.mhj_account_reports.report_agedpartnerbalance`
- `report.mhj_account_reports.report_financial`
- `report.mhj_account_reports.report_journal`
- `report.mhj_account_reports.report_journal_ledger`
- `report.mhj_account_reports.report_cash_flow`

### 4. **Excel Export** (`report/report_excel.py`)
- **Classes**: `GeneralLedgerXlsx`, `PartnerLedgerXlsx`, `TrialBalanceXlsx` (others)
- **Pattern**: Conditional inheritance from `report.report_xlsx.abstract`
- **XLSX_AVAILABLE** flag for graceful degradation
- Reuses existing report data via `_get_report_values()`
- Uses xlsxwriter for professional formatting

---

## Odoo 18 Database Schema Changes

### JSONB Fields
1. **account.account.code_store** (company_dependent JSONB)
   - Format: `{"1": "100000", "2": "100000"}` (company_id → code)
   - Accessed via computed `code` field based on root_company

2. **account.account.name** (JSONB with translations)
   - Format: `{"en_US": "Cash", "ar": "نقدي"}`

3. **account.move_line.analytic_distribution** (JSONB)
   - Format: `{"123": 100.0, "456,789": 50.0}`
   - Replaces `analytic_account_id` (many2one from Odoo 17)
   - Query: `analytic_distribution @> '{"123": 50}'::jsonb`

4. **parent_state** on move_line
   - **Critical**: Use `parent_state` instead of `move_id.state`

---

## Report Output Matrix

| Report | Wizard | PDF | Excel | Interactive | Status |
|--------|--------|-----|-------|-------------|--------|
| General Ledger | ✅ | ✅ | ✅ | ✅ | Filters partially working |
| Partner Ledger | ✅ | ✅ | ✅ | ✅ | **Broken calculations** |
| Trial Balance | ✅ | ✅ | ✅ | ✅ | Working |
| Cash Flow | ❌ | ✅ | ❌ | ✅ | Working |
| Balance Sheet | ❌ | ✅ | ❌ | ✅ | Working |
| Journal Ledger | ❌ | ✅ | ❌ | ❓ | **To verify** |
| Tax Report | ✅ | ✅ | ❌ | ❌ | N/A |
| Aged Partner | ✅ | ✅ | ❌ | ❌ | N/A |
| Financial | ✅ | ✅ | ❌ | ❌ | N/A |
| Journal Audit | ✅ | ✅ | ❌ | ❌ | N/A |

---

## Interactive Reports Architecture (OWL)

### Backend - Controllers (`controllers/main.py`)
**Routes**:
- `/mhj/accounting_reports/get_data` - Main JSON endpoint
- `/mhj/accounting_reports/get_filter_data` - Filter dropdown data

**Methods**:
- `_build_used_context(filters)` - Mirrors wizard context for date/state/journal filtering
- `_get_trial_balance_data(filters)` - Trial Balance JSON
- `_get_general_ledger_data(filters)` - General Ledger JSON
- `_get_partner_ledger_data(filters)` - Partner Ledger JSON (❌ broken calculations)
- `_get_cash_flow_data(filters)` - Cash Flow JSON
- `_get_balance_sheet_data(filters)` - Balance Sheet JSON

**Pattern**: Controllers call existing report models' `_get_report_values()` to reuse PDF logic

### Frontend - JavaScript/OWL (`static/src/js/`)
**Base Component**: `financial_reports.js` → `FinancialReportBase`
- Default filters with all options
- `loadReport()` - RPC call to get data
- `applyFilters()` - Reload with current filters
- `getVisibleAccounts(accounts)` - Client-side display_account filtering
- `loadFilterData()` - Load journals/accounts/partners/analytics dropdowns

**Report Components**:
- `trial_balance_report.js` → `TrialBalanceReport` (extends FinancialReportBase)
- `general_ledger_report.js` → `GeneralLedgerReport` (toggleable account expansion)
- `partner_ledger_report.js` → `PartnerLedgerReport` (toggleable partner expansion)
- `cash_flow_report.js` → `CashFlowReport`

**Templates**: `static/src/xml/financial_reports_templates.xml`
- Base template with filter panel (all common filters + report-specific)
- Content templates per report type
- Uses `getVisibleAccounts()` for Trial Balance & General Ledger

### Available Filters
**Common** (all reports):
- `date_from`, `date_to`, `state`, `journal_ids`, `account_ids`, `partner_ids`, `analytic_account_ids`, `display_account`

**General Ledger**:
- `sortby` (sort_date/sort_journal_partner), `initial_balance`

**Partner Ledger**:
- `result_selection` (customer/supplier/customer_supplier), `reconciled`, `amount_currency`, `initial_balance`

---

## Key Files Structure

### Critical Override
- `models/account_move_line.py`: **Main override** for `_query_get()` - handles ALL date filtering, analytics, partners

### Core Data Models
- `models/account_financial_report.py`: Hierarchy + level computation
- `models/account_account_type.py`: Account type definitions
- `models/account_optimization.py`: Index creation, ANALYZE stats
- `models/memory_monitor.py`: Optional psutil tracking

### Wizards
- `wizard/account_report_common.py`: Base class with performance fields
- `wizard/account_general_ledger.py`: GL-specific (initial_balance, sortby)
- `wizard/account_partner_ledger.py`: Partner-specific
- `wizard/account_trial_balance.py`: TB-specific
- `wizard/account_tax_report.py`: Tax-specific
- `wizard/aged_partner.py`: Aged balance-specific
- `wizard/account_journal_audit.py`: Journal-specific

### Reports
- `report/report_general_ledger.py`: **MAIN EXAMPLE** - batch processing, pagination, GC
- `report/report_partner_ledger.py`
- `report/report_trial_balance.py`
- `report/report_tax.py`
- `report/report_aged_partner.py`
- `report/report_financial.py`
- `report/report_journal.py`
- `report/report_journal_ledger.py`
- `report/report_cash_flow.py`

### Excel
- `report/report_excel.py`: GeneralLedgerXlsx, PartnerLedgerXlsx, TrialBalanceXlsx
- Each worksheet: title, parameters, account headers, move lines, totals

### Templates
- `report/report_*.xml`: QWeb templates for PDF rendering
- Accessed via `data['form']['used_context']`

### Views/Menus
- `views/menu.xml`: Main accounting menu
- `views/financial_report.xml`: Financial hierarchy interface
- `wizard/account_report_common_view.xml`: Base wizard view

---

## Performance Patterns (Critical)

### Memory Management
```python
BATCH_SIZE = 10000  # accounts per batch
MOVE_LINE_LIMIT = 50000  # per account
# Process in batches with gc.collect() between
```

### Pagination
- Configurable in wizard: `enable_pagination`, `max_records_per_account`
- Default: 50,000 records per account

### Database Indexes Created
- `idx_aml_date_account`
- `idx_aml_partner_date`
- `idx_aml_account_partner_date`
- `idx_aml_maturity_account`
- `idx_aml_company_date`
- `idx_am_state`
- `idx_aml_reconcile`

---

## Known Issues & Gaps

### Missing Excel Exports
- ❌ Tax Report (no Excel model)
- ❌ Aged Partner Balance (no Excel model)
- ❌ Financial Report (no Excel model)
- ❌ Journal Reports (no Excel models)
- ❌ Cash Flow (no Excel model)

### Odoo 18 Compatibility Notes
- **account_move_line.py**: Correctly uses `parent_state` ✅
- **analytic_distribution**: Implemented in `_query_get()` ✅
- **code_store**: Not explicitly handled in reports (should work via ORM)
- **name JSONB**: Not explicitly handled (should work via ORM)

### Code Quality Issues
- Hardcoded language in some SQL (`acc.name->>'en_US'` should use context lang)
- Inconsistent batch sizes across reports
- SQL injection risk in some optimization methods (index creation)
- Missing error handling for empty result sets

### Missing Features
- No CSV export
- No scheduled/email delivery
- No period-over-period comparison
- No drill-down in Excel
- No pivot tables
- No chart generation

---

## Dependencies
- **Odoo Modules**: account, report_xlsx
- **Python Packages**: psutil, xlsxwriter

---

## Recent Sessions History

### Dec 10, 2025 - Interactive Filter Implementation (In Progress)
**Commits**:
- `0102146` - "Expose ledger-specific filters in interactive UI"
- `c77e333` - "Keep server-side filtering and add client-side filtering for extra control"

**Work Done**:
1. ✅ Added filter panel controls for General Ledger (sortby, initial_balance)
2. ✅ Added filter panel controls for Partner Ledger (result_selection, reconciled, amount_currency, initial_balance)
3. ✅ Implemented dual filtering (server + client-side) for display_account
4. ✅ Fixed debug header visibility (only in debug mode)
5. ✅ Reorganized menus under "Accounting Reports" parent

**Current Issues**:
- ❌ Partner Ledger calculations incorrect (initial balance, running sum, totals)
- ❌ Some filters not propagating correctly from UI → controller → report
- ❓ Journal Ledger interactive version existence unclear

### Dec 9, 2025 - OWL Migration & Trial Balance Debugging ✅ FIXED
- Added JSON endpoints for all main reports in `controllers/main.py`
- Trial Balance endpoint respects `account_ids` filter
- Fixed context propagation for date filtering
- Debug panel is wrapped in `env.debug` to stay hidden in production; scroll layout fixed (100vh/flex/min-height:0)
- Pending: Frontend OWL components/templates for General Ledger, Partner Ledger, Cash Flow to consume the new endpoints

### Completed ✅
- Deep code analysis of legacy + dynamic reports
- Reviewed dynamic reports frontend design
- **Trial Balance OWL Component - FULLY FIXED**
- Created comprehensive implementation roadmap
- Added extensive debugging and logging

### Issues Found & Fixed

**Issue 1: formatNumber() Method Reference**
- **Problem**: Template called `formatNumber()` without `this.` prefix
- **Solution**: Updated all 16 calls to use `this.formatNumber()`
- **Result**: Template can now properly reference class methods

**Issue 2: Invalid Context Manager Syntax** ✅ FIXED
- **Error**: `TypeError: 'frozendict' object is not callable`
- **Code**: `with request.env.context(ctx):`
- **Root Cause**: `request.env.context` is a **frozendict** (immutable dict), not a callable function
- **Solution**: Removed the `with` statement, use only `.with_context(ctx)` on model
- **Result**: Context properly applied to report model

**Issue 3: Empty Accounts Array** (CONSEQUENCE OF ISSUE 2)
- When Issue 2 threw exception, controller returned `{'error': '...'}` 
- OWL received error but data was null
- After fixing Issue 2, context properly sets up report filtering

### Debugging Tools Added (Kept in Code)
- **Console logs**: Show RPC response structure, accounts array, first account
- **Server logs**: Track context building and account count
- **Template debug panel**: Shows data structure in UI
- Can be removed after final testing

### Testing Status
Trial Balance should now:
- ✅ Receive data from controller
- ✅ Display accounts in table
- ✅ Show formatted numbers
- ✅ Display totals in footer
- ✅ Render chart with balance visualization

### Next Phase
Ready to implement remaining 8 interactive reports using same pattern:
1. General Ledger (with expandable accounts)
2. Partner Ledger (grouped by partner)
3. P&L, Balance Sheet, Cash Flow (hierarchical)
4. Tax, Aged Partner, Journal reports



---

## Migration Project: Legacy → OWL-based Interactive Reports

### What We're Building
Enhance **mhj_account_reports** (legacy Odoo 18 reports) with OWL components to provide:
- Interactive, real-time filtering
- Dynamic chart visualization
- Modern responsive UI
- Excel/PDF export capabilities
- Performance optimizations for large datasets

### Reference Frontend: mhj_financial_reports
Using **mhj_dynamic_financial_reports** as design reference ONLY (not Python code).

**Key Frontend Patterns from Reference**:
1. **Base Component** (`FinancialReportBase`):
   - Handles state management (filters, loading, data)
   - Common methods: loadFilterData(), loadReport(), applyFilters(), resetFilters()
   - Methods: filterItems(), toggleItem(), clearFilter()
   - Export: exportExcel(), printReport()

2. **Filter System**:
   - Date range (date_from, date_to)
   - State filter (posted/all)
   - Multi-select dropdowns: journals, accounts, partners, analytics
   - Search/filter text boxes for each dropdown
   - Collapse/expand with "Clear" buttons

3. **Template Structure** (`financial_reports_templates.xml`):
   ```xml
   <FinancialReportBase>
     ├─ Control Panel (top bar with buttons)
     ├─ Filter Panel (collapsible)
     ├─ Report Content Area (dynamic based on report type)
     └─ Charts (Chart.js integration)
   ```

4. **Report-Specific Components**:
   - `ProfitLossReport` → content template + chart
   - `BalanceSheetReport` → content template + chart
   - `TrialBalanceReport` → content template + chart
   - `CashFlowReport` → content template + chart
   - `GeneralLedgerReport` → detailed table
   - `PartnerLedgerReport` → partner breakdown table
   - `JournalLedgerReport` → journal entries table

5. **Chart Management** (`ChartManager` utility):
   - `createBarChart()`, `createLineChart()`, `createDoughnutChart()`
   - `getColorPalette()` for consistent colors
   - `formatCurrency()` for tooltips
   - `destroyChart()` for cleanup

6. **CSS Design** (`financial_reports.css`):
   - Modern card-based layout
   - Bootstrap grid system (col-md-3, col-md-6, etc.)
   - Responsive design for mobile
   - Print styles (hide filters, adjust fonts)
   - Hover effects on tables
   - Collapsible sections

7. **Export Functionality** (`html_to_excel.js`):
   - Convert HTML tables to Excel
   - Preserve formatting
   - Support for multiple worksheets

### Current OWL Implementation in mhj_account_reports
- **Base**: `FinancialReportBase` (financial_reports.js)
- **Trial Balance**: `TrialBalanceReport` (trial_balance_report.js)
- **Interactive Menu**: Menu item `action_trial_balance_interactive` registered
- **Controller**: `/mhj/accounting_reports/get_data` (main.py)
- **Filter Data**: `/mhj/accounting_reports/get_filter_data` (main.py)

### Reports Still Needing OWL Components

**Already Implemented**:
- ✅ Trial Balance (interactive, with chart)

**Still Need OWL**:
- General Ledger (started, no chart)
- Partner Ledger (not visible in OWL)
- Tax Report (wizard only, no interactive)
- Aged Partner Balance (wizard only)
- Financial Report (wizard only)
- Journal Reports (wizard only)
- Cash Flow (wizard only)

**Strategy**:
1. Create `XXXReport` class extending `FinancialReportBase`
2. Create corresponding content template
3. Register action in `ir.actions.client`
4. Add menu items
5. Extend controller with report-specific methods
6. Reuse existing Python report models via controller methods

---

## Implementation Roadmap

### Phase 1: Enhance Trial Balance (Complete)
- ✅ Base OWL component created
- ✅ Interactive filters working
- ✅ Chart.js integration
- ✅ Menu item registered
- Status: DONE

### Phase 2: Implement Remaining Reports
**Priority 1 (Core Ledgers)**:
1. General Ledger - detailed movement table with collapsible accounts
   - Add: Initial balance row, collapsible move lines per account
   - Chart: Account balance comparison
   
2. Partner Ledger - partner-wise breakdown
   - Add: Partner section headers, collapsible transactions
   - Chart: Top partners by balance
   
3. Trial Balance Details - drill-down from summary
   - Add: Click to expand accounts to transactions
   - Chart: Balance distribution pie chart

**Priority 2 (Financial Statements)**:
4. Profit & Loss - hierarchical structure with chart
5. Balance Sheet - hierarchical structure with chart
6. Cash Flow - timeline chart with drill-down

**Priority 3 (Specialized)**:
7. Tax Report - tax calculations with journal detail
8. Aged Partner Balance - aging analysis with timeline
9. Journal Audit - transaction log with filters

### JavaScript Component Architecture

**Base Class** (`financial_reports.js`):
```javascript
export class FinancialReportBase {
  setup() {
    // State management
    this.state = {
      reportData, loading, filters, filterData,
      showFilters, filterText, filteredItems,
      collapsedItems // Track expand/collapse state
    }
  }
  
  // Core methods
  loadFilterData()  // Load dropdown options
  loadReport()      // Fetch report data
  applyFilters()    // Reload with new filters
  resetFilters()    // Reset to defaults
  toggleFilters()   // Show/hide filter panel
  
  // Filter helpers
  filterItems(type)     // Search filter items
  toggleItem(type, id)  // Add/remove from selection
  clearFilter(type)     // Clear entire filter
  
  // Export methods
  exportExcel()     // Convert to Excel
  printReport()     // Print PDF
  
  // Chart rendering
  renderChart()     // Create Chart.js instance
}
```

**Specific Report Classes** (extend FinancialReportBase):
```javascript
export class GeneralLedgerReport extends FinancialReportBase {
  reportType = 'general_ledger'
  
  // Override for GL-specific charts
  renderChart() { }
  
  // Toggle account detail expansion
  toggleAccountDetail(accountId) { }
}

// Similar for: PartnerLedgerReport, BalanceSheetReport, etc.
```

**Content Templates** (financial_reports_templates.xml):
```xml
<!-- General Ledger -->
<t t-name="mhj_account_reports.GeneralLedgerReportContent">
  <div class="card">
    <div class="card-header">
      <h3>General Ledger</h3>
    </div>
    <div class="card-body">
      <table class="table">
        <tbody>
          <t t-foreach="reportData.accounts" t-as="account">
            <!-- Account header row with expand button -->
            <tr class="account-row" t-on-click="toggleAccountDetail(account.id)">
              <td><i class="fa fa-chevron-right"/></td>
              <td><t t-esc="account.code"/></td>
              <td><t t-esc="account.name"/></td>
              <td class="text-right"><t t-esc="account.balance"/></td>
            </tr>
            <!-- Detail rows (show if expanded) -->
            <t t-if="collapsedItems[account.id]">
              <t t-foreach="account.move_lines" t-as="line">
                <tr class="move-line-row">
                  <td></td>
                  <td><t t-esc="line.date"/></td>
                  <td><t t-esc="line.journal"/></td>
                  <td><t t-esc="line.debit"/></td>
                  <td><t t-esc="line.credit"/></td>
                  <td class="text-right"><t t-esc="line.balance"/></td>
                </tr>
              </t>
            </t>
          </t>
        </tbody>
      </table>
    </div>
  </div>
</t>
```

**Controller Methods** (controllers/main.py):
```python
@http.route('/mhj/accounting_reports/get_data', type='json', auth='user')
def get_report_data(self, report_type, filters):
  if report_type == 'general_ledger':
    return self._get_general_ledger_data(filters)
  # ... etc

def _get_general_ledger_data(self, filters):
  # Call existing report model
  report_model = request.env['report.mhj_account_reports.report_general_ledger']
  
  # Format data for JSON
  return {
    'accounts': [...],
    'totals': {...},
    'company': '...',
    'currency_symbol': '...',
  }
```

---

## File Structure (After OWL Migration)

### New OWL Components to Create:
```
static/src/js/
  ├─ financial_reports.js        (existing - base class)
  ├─ trial_balance_report.js      (existing - complete)
  ├─ general_ledger_report.js     (NEW - extends base)
  ├─ partner_ledger_report.js     (NEW - extends base)
  ├─ profit_loss_report.js        (NEW - extends base)
  ├─ balance_sheet_report.js      (NEW - extends base)
  ├─ cash_flow_report.js          (NEW - extends base)
  ├─ tax_report.js                (NEW - extends base)
  ├─ aged_partner_report.js       (NEW - extends base)
  ├─ journal_audit_report.js      (NEW - extends base)
  ├─ chart_manager.js             (NEW - Chart.js utilities)
  └─ html_to_excel.js             (NEW - Excel export)

static/src/xml/
  ├─ financial_reports_templates.xml (update - all templates)

static/src/css/
  ├─ financial_reports.css        (update - all styles)

views/
  ├─ interactive_reports.xml      (NEW - menu items + actions)

controllers/
  ├─ main.py                      (update - add report methods)
```

### Modified Existing Files:
1. `__manifest__.py` - Add new menu actions, assets
2. `models/__init__.py` - Import new models if needed
3. `controllers/main.py` - Add RPC routes for all reports
4. `views/interactive_reports.xml` - Menu items for all reports
5. `static/src/xml/financial_reports_templates.xml` - All content templates
6. `static/src/css/financial_reports.css` - All styling

---

## Key Learnings from Dynamic Reports

### Do's ✅
- Use `t-model` for two-way binding on filters
- Use `t-foreach` for rendering lists with `t-key` for performance
- Chain methods with `=>` arrow functions: `t-on-click="() => this.method()"`
- Use `<t t-if>` for conditional rendering, avoid `<div v-if>`
- Register components with: `registry.category("actions").add(tag, Class)`
- Use RPC with `/route` for backend data: `rpc('/path/to/route', {params})`
- Use `useState()` in setup() for reactive state
- Use `useService()` for orm, notification, actionService
- Responsive grid: `col-md-3`, `col-md-6` Bootstrap classes
- Use Chart.js for visualizations via CDN

### Don'ts ❌
- Don't mix ORM calls in component - use RPC to controller
- Don't put heavy computation in templates
- Don't forget `this` binding in arrow functions
- Don't hardcode currency symbols - use company data
- Don't forget responsive design - test mobile
- Don't forget i18n - use translation strings where possible
- Don't create overlapping data in state - single source of truth

### UI/UX Patterns
- Control panel: Fixed top with button group (Apply, Reset, Export, Print, Filters)
- Filters: Collapsible panel with grouped filters (dates, status, dropdowns)
- Filter dropdowns: Search box + scrollable list with checkboxes + Clear button
- Content: Card-based with header (title + subtitle) + body (table/chart)
- Tables: Hover effects, striped rows, proper number formatting
- Charts: Chart.js with proper legends and tooltips
- Mobile: Stack vertically, reduce font sizes, single column layout
- Print: Hide filters/buttons, adjust fonts, clean borders



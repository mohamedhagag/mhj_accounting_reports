# Odoo Accounting Reports Module - AI Coding Guide

## Architecture Overview

This is an **Odoo 18 module** (`mhj_account_reports`) providing advanced accounting reports with performance optimizations for databases containing millions of journal entries. The module follows Odoo's MVC architecture with wizard-driven report generation.

## Critical Odoo 18 Changes

### Database Schema Changes
- **account.account.code**: Now stored in **JSONB field** `code_store` (company_dependent), computed field `code` uses multi-company logic
- **account.account.name**: **JSONB field** supporting translations per language
- **account.move_line.analytic_distribution**: **JSONB field** replacing many2one `analytic_account_id` (format: `{"account_id1,account_id2": percentage}`)
- **Multi-company architecture**: Accounts can belong to multiple companies via M2M `company_ids`, root company determines code storage
- **parent_state**: Replaces direct `state` checks on move lines (use `parent_state` instead of `move_id.state`)

### Key Model Changes (Odoo 18)
```python
# OLD (Odoo 17 and below)
account.code  # Simple Char field
account.analytic_account_id  # Many2one on account.move.line

# NEW (Odoo 18)
account.code_store  # JSONB, company_dependent
account.code  # Computed from code_store based on env.company
account.move.line.analytic_distribution  # JSONB: {"123,456": 50.0}
```

### Core Components

- **Wizards** (`wizard/`): TransientModels that collect user input for report generation
  - **Base Classes**: `account.common.report` → `account.common.account.report` / `account.common.partner.report`
  - **Inheritance Chain**: 
    ```
    account.common.report (base fields: company_id, journal_ids, date_from, date_to, target_move)
      ├─ account.common.account.report (adds: display_account, analytic_account_ids, account_ids, partner_ids)
      └─ account.common.partner.report (adds: result_selection, partner_ids)
    ```
  - **Methods**: `_print_report()` for PDF, `_print_excel_report()` for Excel, `pre_print_report()` to prepare data
  - **Data Flow**: `check_report()` → reads fields → `_build_contexts()` → `_print_report()`
  - Example: `account_general_ledger.py` extends `account.common.account.report` with `initial_balance` and `sortby` fields

- **Report Models** (`report/`): AbstractModels with `_name = 'report.<module>.<report_name>'`
  - Implement `_get_report_values(docids, data)` to generate report data
  - Use batching and pagination for large datasets (see performance patterns below)
  - Example: `report_general_ledger.py` processes accounts in 10K batches with garbage collection

- **Excel Exporters** (`report/report_excel.py`): AbstractModels inheriting from `report.report_xlsx.abstract`
  - Check `XLSX_AVAILABLE` flag for graceful degradation when `report_xlsx` module is missing
  - Implement `generate_xlsx_report(workbook, data, objects)` with xlsxwriter formatting
  - Reuse data from existing report models via `_get_report_values()`

- **Models** (`models/`): Business logic extensions
  - `account_financial_report.py`: Hierarchical financial report structure with efficient level computation
  - `account_optimization.py`: Database performance tools (index creation, table statistics)
  - `memory_monitor.py`: Optional memory tracking using psutil for large dataset processing

## Performance Patterns (Critical for Large Databases)

This module is **optimized for millions of records**. Key patterns:

```python
# 1. Batch Processing - Process records in chunks
BATCH_SIZE = 10000
account_batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
for batch in account_batches:
    process_batch(batch)
    gc.collect()  # Force garbage collection between batches

# 2. Pagination - Limit records per account
MOVE_LINE_LIMIT = 50000
context['max_records_per_account'] = 50000

# 3. SQL Optimization - Use raw SQL with proper indexes
cr.execute("""
    SELECT account_id, SUM(debit), SUM(credit)
    FROM account_move_line
    WHERE date < %s AND account_id IN %s
    GROUP BY account_id
""", (date_from, tuple(account_ids)))

# 4. Memory Monitoring - Track and log memory usage
self._start_memory_monitoring()
self._check_memory_usage("After processing accounts", force_gc=True)
```

The module creates PostgreSQL indexes automatically on installation for large databases (>100K records): `idx_aml_date_account`, `idx_aml_partner_date`, `idx_aml_account_partner_date`, etc.

## Report Development Workflow

### Adding a New Report (3-step process)

1. **Create Wizard** (`wizard/account_<report>.py`):
   ```python
   class AccountReport<Name>(models.TransientModel):
       _name = "account.report.<report_name>"
       _inherit = "account.common.account.report"  # or account.common.partner.report
       
       custom_field = fields.Boolean(string='Custom Option')
       
       def _print_report(self, data):
           data = self.pre_print_report(data)  # Required for account.common.account.report
           data['form'].update(self.read(['custom_field'])[0])
           return self.env.ref('mhj_account_reports.action_report_<name>').report_action(self, data=data)
   ```

2. **Create Report Model** (`report/report_<name>.py`):
   ```python
   class Report<Name>(models.AbstractModel):
       _name = 'report.mhj_account_reports.report_<name>'
       _description = '<Description>'
       
       def _get_report_values(self, docids, data=None):
           # Extract parameters from data['form']
           # Query database with performance optimizations
           # Return dict with template context
           return {
               'doc_ids': docids,
               'doc_model': data['model'],
               'data': data['form'],
               'Results': computed_data,
           }
   ```

3. **Register Reports** (`report/report.xml`):
   ```xml
   <!-- PDF Report -->
   <record id="action_report_<name>" model="ir.actions.report">
       <field name="name">Report Name</field>
       <field name="model">account.report.<report_name></field>
       <field name="report_type">qweb-html</field>
       <field name="report_name">mhj_account_reports.report_<name></field>
   </record>
   
   <!-- Excel Report (optional) -->
   <record id="action_report_<name>_xlsx" model="ir.actions.report">
       <field name="report_type">xlsx</field>
       <field name="report_name">mhj_account_reports.<name>_xlsx</field>
   </record>
   ```

### Excel Export Pattern

Excel reports use conditional imports for optional dependency:

```python
try:
    from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

class ReportXlsx(models.AbstractModel):
    _inherit = 'report.report_xlsx.abstract' if XLSX_AVAILABLE else []
    
    def generate_xlsx_report(self, workbook, data, objects):
        if not XLSX_AVAILABLE:
            raise UserError(_("Install 'report_xlsx' module"))
        # Use xlsxwriter formats for professional styling
        # Reuse existing report logic: report_obj._get_report_values()
```

## Module Structure Conventions

- **Naming**: Models use `account.<purpose>`, wizards use `account.report.<name>`, reports use `report.mhj_account_reports.report_<name>`
- **Inheritance**: Wizards inherit from base classes (`account.common.report`, `account.common.account.report`, `account.common.partner.report`)
- **Security**: All models require entries in `security/ir.model.access.csv` with separate rules for `account.group_account_user` and `account.group_account_manager`
- **Translations**: Module supports Arabic (`i18n/ar.po`) - use `_()` for translatable strings
- **Dependencies**: Requires `account` and `report_xlsx` modules; external Python dependencies: `psutil`, `xlsxwriter`

## Installation Hooks

- **Pre-init**: `_pre_init_clean_m2m_models()` drops legacy M2M tables before installation
- **Post-init**: `_post_init_hook()` recomputes financial report levels and creates performance indexes for large databases (>100K records)

## Testing & Debugging

- **Large Dataset Testing**: Module includes configurable fields in wizards: `enable_pagination`, `max_records_per_account`, `batch_size`
- **Memory Profiling**: Use `account.report.memory.mixin` for optional memory tracking during development
- **SQL Performance**: Check query plans with `account.report.optimization.analyze_table_statistics()`

## Common Patterns

**Date Filtering Context**:
```python
context = {
    'date_from': data['form']['date_from'],
    'date_to': data['form']['date_to'],
    'strict_range': True if date_from else False,
    'state': 'posted',  # or 'all' for target_move
}
```

**Account Filtering**:
```python
domain = [('account_id', 'in', account_ids)]
if target_move == 'posted':
    domain.append(('move_id.state', '=', 'posted'))
if date_from:
    domain.append(('date', '>=', date_from))
```

**QWeb Template Access**: Reports use `data['form']['used_context']` to pass context to templates in XML files (`report/report_*.xml`)

## Complete Model & Field Inventory

### Custom Models (DB Tables)

1. **account.account.type** (`account_account_type`)
   - `name` (Char, required, translate): Account type display name
   - `type` (Selection, required): Account classification (18 types: asset_receivable, liability_payable, income, expense, etc.)
   - Purpose: Extends Odoo's account types for custom financial reporting

2. **account.financial.report** (`account_financial_report`)
   - `name` (Char, required, translate): Report line name
   - `parent_id` (Many2one → self): Hierarchical parent
   - `children_ids` (One2many): Child report lines
   - `sequence` (Integer): Display order
   - `level` (Integer, computed, recursive): Auto-computed hierarchy depth
   - `type` (Selection): sum/accounts/account_type/account_report
   - `account_ids` (Many2many → account.account): Direct account links
   - `account_type_ids` (Many2many → account.account.type): Type-based filtering
   - `account_report_id` (Many2one → self): Reference to another report
   - `sign` (Selection): Balance sign reversal (-1/1)
   - `display_detail` (Selection): How to show children (no_detail/detail_flat/detail_with_hierarchy)
   - `style_overwrite` (Selection): Visual formatting (0-6 levels)
   - `report_domain` (Char): Custom domain filter
   - **Performance**: `_get_level()` uses optimized parent-child mapping for efficient hierarchy computation

3. **account.report.optimization** (`account_report_optimization`, TransientModel)
   - No stored fields (pure utility model)
   - Methods:
     - `create_performance_indexes()`: Creates 7 PostgreSQL indexes on account_move_line
     - `analyze_table_statistics()`: Updates ANALYZE stats for query planner
     - `get_table_statistics()`: Returns pg_stats data
   - **Indexes Created**: idx_aml_date_account, idx_aml_partner_date, idx_aml_account_partner_date, idx_aml_maturity_account, idx_aml_company_date, idx_am_state, idx_aml_reconcile

4. **account.report.memory.mixin** (`account_report_memory_mixin`, AbstractModel)
   - No DB table (mixin only)
   - Provides memory monitoring via psutil
   - Methods: `_start_memory_monitoring()`, `_check_memory_usage()`, `_log_memory_summary()`

### Inherited Models (Extensions)

1. **account.move.line** (Extended in `models/account_move_line.py`)
   - **Custom Method**: `_query_get(domain=None)` - OVERRIDDEN
   - **Key Changes**:
     - Uses `parent_state` instead of `move_id.state` (Odoo 18)
     - Handles `analytic_distribution` JSONB field (not `analytic_account_id`)
     - Adds `aged_balance` context support for `date_maturity` filtering
     - Returns: `(tables, where_clause, where_clause_params)` tuple
   - **Critical for Reports**: All reports rely on this method for building SQL queries

### Wizard Models (TransientModels)

**Base Wizards**:
1. **account.common.report**
   - company_id, journal_ids, date_from, date_to, target_move
   - enable_pagination, max_records_per_account, batch_size (performance fields)
   
2. **account.common.account.report** (extends account.common.report)
   - display_account, analytic_account_ids, account_ids, partner_ids
   
3. **account.common.partner.report** (extends account.common.report)
   - result_selection, partner_ids

**Report-Specific Wizards**:
- `account.report.general.ledger`: initial_balance, sortby, journal_ids (M2M custom rel)
- `account.report.partner.ledger`: amount_currency, reconciled, initial_balance
- `account.balance.report` (Trial Balance): display_account, analytic_account_ids
- `account.tax.report.wizard`: date_from (required), date_to (required)
- `account.aged.trial.balance`: period_length, date_from
- `account.print.journal`: sort_selection
- `accounting.report` (Financial): enable_filter, account_report_id, filter_cmp, date_from_cmp, date_to_cmp, debit_credit, label_filter

## Database Schema Deep Dive

### JSONB Fields (Odoo 18 Specific)

1. **account.account.code_store** (company_dependent JSONB)
   ```json
   {
     "1": "100000",  // company_id: code
     "2": "100000"
   }
   ```
   - Accessed via computed `code` field which reads from root_company_id
   - Search uses `_search_code()` which queries `code_store` with root company context

2. **account.account.name** (JSONB with translations)
   ```json
   {
     "en_US": "Cash",
     "ar": "نقدي",
     "fr_FR": "Trésorerie"
   }
   ```
   - Use `account.name` to access (auto-translates based on context)
   - Direct DB access: `acc.name->>'en_US'` in SQL

3. **account.move_line.analytic_distribution** (JSONB)
   ```json
   {
     "123": 100.0,           // Single account: 100%
     "456,789": 50.0         // Multi-account key: percentage
   }
   ```
   - Replaces `analytic_account_id` (many2one) from Odoo 17
   - Format: `"account_id1,account_id2": percentage`
   - Query with: `WHERE analytic_distribution @> '{"123": 50}'::jsonb`
   - Access account IDs: Parse keys, split by comma

### Critical Query Patterns (Odoo 18)

**Filtering by Account Code** (must use code_store with root_company):
```python
self.env['account.account'].with_company(self.env.company.root_id).sudo().search([('code_store', '=like', '4%')])
```

**Querying Analytic Distribution**:
```python
# Find lines with specific analytic account
domain = [('analytic_distribution', 'in', [analytic_account.id])]

# SQL query (use JSONB operators)
cr.execute("""
    SELECT * FROM account_move_line 
    WHERE analytic_distribution ? %s  -- key exists
    OR analytic_distribution @> %s::jsonb  -- contains
""", (str(account_id), json.dumps({str(account_id): 50})))
```

**Parent State vs State**:
```python
# WRONG (Odoo 17 pattern)
domain = [('move_id.state', '=', 'posted')]

# CORRECT (Odoo 18)
domain = [('parent_state', '=', 'posted')]
```

## Report Output Matrix

| Report | Wizard Model | PDF/HTML | Excel | Report Model | Excel Model |
|--------|-------------|----------|-------|--------------|-------------|
| General Ledger | account.report.general.ledger | ✅ | ✅ | report.mhj_account_reports.report_general_ledger | report.mhj_account_reports.general_ledger_xlsx |
| Partner Ledger | account.report.partner.ledger | ✅ | ✅ | report.mhj_account_reports.report_partnerledger | report.mhj_account_reports.partner_ledger_xlsx |
| Trial Balance | account.balance.report | ✅ | ✅ | report.mhj_account_reports.report_trialbalance | report.mhj_account_reports.trial_balance_xlsx |
| Tax Report | account.tax.report.wizard | ✅ | ❌ | report.mhj_account_reports.report_tax | - |
| Aged Partner | account.aged.trial.balance | ✅ | ❌ | report.mhj_account_reports.report_agedpartnerbalance | - |
| Financial Report | accounting.report | ✅ | ❌ | report.mhj_account_reports.report_financial | - |
| Journal Audit | account.print.journal | ✅ | ❌ | report.mhj_account_reports.report_journal | - |
| Journal Ledger | - | ✅ | ❌ | report.mhj_account_reports.report_journal_ledger | - |
| Cash Flow | - | ✅ | ❌ | report.mhj_account_reports.report_cash_flow | - |

## Complete Report Generation Flow

### 1. User Clicks "Print PDF" or "Export Excel"

**Wizard View** (`wizard/*.xml`):
```xml
<button name="check_report" string="Print PDF" type="object" class="oe_highlight"/>
<button name="print_excel_report" string="Export Excel" type="object" class="btn-success"/>
```

### 2. Wizard Processing

**Base Class** (`account.common.report.check_report()`):
```python
def check_report(self):
    data = {
        'ids': self.env.context.get('active_ids', []),
        'model': self.env.context.get('active_model'),
        'form': self.read([fields...])  # All wizard fields
    }
    used_context = self._build_contexts(data)
    data['form']['used_context'] = used_context
    return self._print_report(data)  # or _print_excel_report()
```

### 3. Report Action Call

**Wizard** → **ir.actions.report**:
```python
# PDF
return self.env.ref('mhj_account_reports.action_report_general_ledger').report_action(self, data=data)

# Excel
return self.env.ref('mhj_account_reports.action_report_general_ledger_xlsx').report_action(self, data=data)
```

### 4. Report Model Execution

**AbstractModel** (`report/report_*.py`):
```python
@api.model
def _get_report_values(self, docids, data=None):
    # 1. Extract parameters from data['form']
    date_from = data['form']['date_from']
    ctx = data['form']['used_context']
    
    # 2. Query database with optimizations
    accounts = self.env['account.account'].search([...])
    accounts_res = self.with_context(ctx)._get_account_move_entry(accounts, ...)
    
    # 3. Return template context
    return {
        'doc_ids': docids,
        'doc_model': data['model'],
        'data': data['form'],
        'Accounts': accounts_res,
        'time': time,
    }
```

### 5A. PDF Rendering (QWeb)

**Template** (`report/report_*.xml`):
```xml
<t t-foreach="Accounts" t-as="account">
    <t t-set="total" t-value="sum(line['debit'] for line in account['move_lines'])"/>
    <t t-esc="account['code']"/> - <t t-esc="account['name']"/>
</t>
```

### 5B. Excel Generation

**Excel Model** (`report/report_excel.py`):
```python
def generate_xlsx_report(self, workbook, data, objects):
    # 1. Reuse PDF report logic
    report_obj = self.env['report.mhj_account_reports.report_general_ledger']
    report_data = report_obj._get_report_values(objects.ids, data)
    
    # 2. Create worksheet
    worksheet = workbook.add_worksheet('General Ledger')
    
    # 3. Write data with formatting
    for row, account in enumerate(report_data['Accounts']):
        worksheet.write(row, 0, account['code'], text_format)
        ...
```

## Missing & Incomplete Implementations

### 1. **Missing Excel Exports**
- ❌ **Tax Report**: No Excel export (has wizard, PDF model, but no Excel model)
- ❌ **Aged Partner Balance**: No Excel export
- ❌ **Financial Report**: No Excel export (complex hierarchy - would need special handling)
- ❌ **Journal Reports**: No Excel exports for Journal Audit, Journal Ledger, Journal Entries
- ❌ **Cash Flow Report**: No Excel export

### 2. **Odoo 18 Compatibility Issues**

**account.account.name Translation Access**:
```python
# CURRENT (may fail if name not JSONB)
acc.name->>'en_US'  # Direct SQL

# SHOULD BE
self.env['account.account'].browse(id).name  # Use ORM with translation
```

**Analytic Distribution**:
```python
# NOT IMPLEMENTED: Filtering by analytic accounts in reports
# account_report_common_account.py has analytic_account_ids but _query_get may not handle JSONB properly
```

### 3. **Missing Error Handling**

- No validation when `report_xlsx` module is not installed (graceful degradation implemented only in Excel models, not wizards)
- No error handling for empty result sets in partner ledger initial balance
- Missing try/except in batch processing loops (report_general_ledger.py)

### 4. **Unused/Incomplete Files**

- `views/optimization_tools.xml`: Commented out in manifest (not loaded)
- `wizard/account_report_common_journal.py`: Defined but no corresponding wizard using it
- `report/report_cash_flow.py`: Exists but no wizard to trigger it
- `report/report_journal_ledger.py`: Report model exists, but integration unclear

### 5. **Performance Optimization Gaps**

- Memory monitoring is optional and may fail silently
- No connection pooling for large batch queries
- Missing query result caching for repeated calls
- No async processing for multi-million record exports

### 6. **Code Quality Issues**

**Hardcoded Language**:
```python
acc.name->>'en_US'  # Should use lang from context
```

**Inconsistent Batch Sizes**:
- General Ledger: BATCH_SIZE = 10000
- Trial Balance: BATCH_SIZE = 5000
- Partner Ledger: BATCH_SIZE = 10000
- Should be configurable via wizard

**SQL Injection Risk**:
```python
sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
cr.execute(sql)  # Variables not parameterized
```

### 7. **Missing Features**

- No export to CSV format
- No email delivery of reports
- No scheduled report generation
- No report comparison (period-over-period)
- No drill-down from summary to detail in Excel
- No pivot table generation
- No chart/graph generation in Excel

**QWeb Template Access**: Reports use `data['form']['used_context']` to pass context to templates in XML files (`report/report_*.xml`)

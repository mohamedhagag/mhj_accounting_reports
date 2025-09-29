# Analysis: Why the Module Takes Long to Install on Large Databases

## Root Causes of Slow Installation

### 1. **Computed Field with Storage (`level` field)**
The main culprit is in `/models/account_financial_report.py`:

```python
level = fields.Integer(compute='_get_level', string='Level', store=True, recursive=True)

@api.depends('parent_id', 'parent_id.level')
def _get_level(self):
    for report in self:
        level = 0
        if report.parent_id:
            level = report.parent_id.level + 1
        report.level = level
```

**Why this is problematic:**
- **`store=True`**: Forces computation and storage in database
- **`recursive=True`**: Triggers recursive recomputation for hierarchical data
- **During installation**: Creates financial report records with parent-child relationships
- **Large DB impact**: Even though it's not directly related to journal entries, it can cause database locks

### 2. **Financial Report Records Creation**
The module creates multiple `account.financial.report` records during installation:
- Balance Sheet structure (7+ records with hierarchy)
- Profit & Loss structure  
- Each record triggers the computed field calculation

### 3. **Account Type Records**
Creates 18 `account.account.type` records which might trigger related computations.

### 4. **Database Operations During Installation**
- **Pre-init hook**: Drops existing M2M table (`account_journal_account_report_partner_ledger_rel`)
- **XML data loading**: Creates hierarchical financial reports
- **Field computations**: Triggers stored computed field calculations

## Performance Impact on Large Databases

### Why Journal Entries Matter:
1. **Database locks**: Financial report creation might acquire locks that conflict with existing journal entry indexes
2. **Vacuum/analyze operations**: New table/field creation might trigger automatic database maintenance
3. **Constraint checking**: Foreign key validations on large accounting tables
4. **Cache invalidation**: ORM cache clearing affects journal entry queries during installation

## Solutions to Speed Up Installation

### Immediate Fixes:

1. **Remove Stored Computation (Recommended)**
```python
# Change this:
level = fields.Integer(compute='_get_level', string='Level', store=True, recursive=True)

# To this:
level = fields.Integer(compute='_get_level', string='Level', recursive=True)
```

2. **Optimize the Computation Method**
```python
@api.depends('parent_id', 'parent_id.level')
def _get_level(self):
    # More efficient: compute all levels in one pass
    reports_by_parent = {}
    for report in self:
        reports_by_parent.setdefault(report.parent_id.id if report.parent_id else False, []).append(report)
    
    def compute_level(parent_id, level):
        for report in reports_by_parent.get(parent_id, []):
            report.level = level
            compute_level(report.id, level + 1)
    
    compute_level(False, 0)
```

3. **Add Installation Hook with Progress**
```python
def _post_init_hook(env):
    """Optimize installation for large databases"""
    _logger.info("Starting financial reports optimization...")
    
    # Disable automatic recomputation during installation
    env.context = dict(env.context, recompute=False)
    
    # Create records without triggering computations
    # Then trigger computation manually at the end
    _logger.info("Financial reports optimization completed")
```

### Advanced Optimizations:

1. **Lazy Loading for Financial Reports**
2. **Batch Processing for Level Computation** 
3. **Installation Progress Indicators**
4. **Database Index Creation (Optional)**

## Recommended Quick Fix

The fastest fix with minimal risk is to remove the `store=True` parameter:
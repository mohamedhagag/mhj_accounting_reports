#!/usr/bin/env python3
"""
Test script to debug initial balance calculation
Run this inside Odoo shell to test the initial balance logic
"""

def test_initial_balance_data():
    """
    Test if there's partner data in the database that should have initial balance
    """
    print("=== Initial Balance Debug Test ===")
    
    # This would be run inside Odoo shell
    test_sql = """
    -- Check if we have any partner move lines that should create initial balance
    SELECT 
        p.name as partner_name,
        COUNT(aml.id) as total_lines,
        SUM(aml.debit) as total_debit,
        SUM(aml.credit) as total_credit,
        MIN(aml.date) as earliest_date,
        MAX(aml.date) as latest_date
    FROM account_move_line aml
    JOIN res_partner p ON p.id = aml.partner_id
    JOIN account_account acc ON acc.id = aml.account_id
    JOIN account_move am ON am.id = aml.move_id
    WHERE p.id IS NOT NULL
        AND acc.account_type IN ('asset_receivable', 'liability_payable')
        AND am.state = 'posted'
        AND NOT acc.deprecated
    GROUP BY p.id, p.name
    HAVING COUNT(aml.id) > 0
    ORDER BY p.name
    LIMIT 10;
    """
    
    print("SQL to run in Odoo shell to check partner data:")
    print(test_sql)
    
    print("\nThen test initial balance for a specific partner and date:")
    print("""
# In Odoo shell:
partners = env['res.partner'].search([('customer_rank', '>', 0)], limit=1)
if partners:
    partner = partners[0]
    print(f"Testing partner: {partner.name}")
    
    # Check move lines for this partner
    lines = env['account.move.line'].search([
        ('partner_id', '=', partner.id),
        ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
    ])
    
    print(f"Found {len(lines)} lines for partner")
    for line in lines[:5]:  # Show first 5
        print(f"Date: {line.date}, Debit: {line.debit}, Credit: {line.credit}")
    """)

if __name__ == '__main__':
    test_initial_balance_data()
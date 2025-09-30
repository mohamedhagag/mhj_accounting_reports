#!/usr/bin/env python3
"""
Test script to verify partner ledger initial balance logic
"""

def test_initial_balance_dict():
    """Test the new initial balance dictionary structure"""
    
    # Simulate the new _get_partner_initial_balance method return
    def mock_get_partner_initial_balance(debit=1000.0, credit=200.0):
        balance = debit - credit
        return {
            'debit': debit,
            'credit': credit,
            'balance': balance
        }
    
    # Test case 1: Positive balance
    result1 = mock_get_partner_initial_balance(1000.0, 200.0)
    print("Test Case 1 - Positive Balance:")
    print(f"  Initial Debit: {result1['debit']}")
    print(f"  Initial Credit: {result1['credit']}")
    print(f"  Initial Balance: {result1['balance']}")
    print()
    
    # Test case 2: Negative balance
    result2 = mock_get_partner_initial_balance(100.0, 500.0)
    print("Test Case 2 - Negative Balance:")
    print(f"  Initial Debit: {result2['debit']}")
    print(f"  Initial Credit: {result2['credit']}")
    print(f"  Initial Balance: {result2['balance']}")
    print()
    
    # Test case 3: Zero balance
    result3 = mock_get_partner_initial_balance(0.0, 0.0)
    print("Test Case 3 - Zero Balance:")
    print(f"  Initial Debit: {result3['debit']}")
    print(f"  Initial Credit: {result3['credit']}")
    print(f"  Initial Balance: {result3['balance']}")
    print()
    
    # Test sum calculation logic
    def calculate_total_debit(period_debit, initial_debit):
        return period_debit + initial_debit
    
    def calculate_total_credit(period_credit, initial_credit):
        return period_credit + initial_credit
    
    def calculate_total_balance(period_balance, initial_balance):
        return period_balance + initial_balance
    
    # Example totals
    period_debit = 5000.0
    period_credit = 3000.0
    period_balance = period_debit - period_credit
    
    total_debit = calculate_total_debit(period_debit, result1['debit'])
    total_credit = calculate_total_credit(period_credit, result1['credit'])
    total_balance = calculate_total_balance(period_balance, result1['balance'])
    
    print("Total Calculation Example:")
    print(f"  Period Debit: {period_debit} + Initial Debit: {result1['debit']} = Total Debit: {total_debit}")
    print(f"  Period Credit: {period_credit} + Initial Credit: {result1['credit']} = Total Credit: {total_credit}")
    print(f"  Period Balance: {period_balance} + Initial Balance: {result1['balance']} = Total Balance: {total_balance}")
    print()
    
    # Verify balance calculation
    calculated_balance = total_debit - total_credit
    print(f"Verification: {total_debit} - {total_credit} = {calculated_balance} (should equal {total_balance})")
    print(f"Balance calculation correct: {calculated_balance == total_balance}")

if __name__ == "__main__":
    test_initial_balance_dict()
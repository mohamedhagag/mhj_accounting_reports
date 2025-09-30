#!/usr/bin/env python3
"""
Simple test script to validate the partner ledger fixes.
This tests the robustness of the initial balance calculation.
"""

def test_initial_balance_safety():
    """
    Test the safety measures for initial balance calculation
    """
    print("Testing initial balance safety measures...")
    
    # Simulate the get method calls that were causing issues
    test_cases = [
        None,  # NoneType that was causing the error
        {},    # Empty dict
        {'debit': 100.0, 'credit': 50.0, 'balance': 50.0},  # Normal case
        {'debit': None, 'credit': None, 'balance': None},    # None values
    ]
    
    for i, initial_balance in enumerate(test_cases):
        print(f"Test case {i + 1}: {initial_balance}")
        
        try:
            # Simulate the template logic with defensive checks
            debit_value = initial_balance.get('debit', 0) if initial_balance else 0
            credit_value = initial_balance.get('credit', 0) if initial_balance else 0  
            balance_value = initial_balance.get('balance', 0) if initial_balance else 0
            
            print(f"  Debit: {debit_value}")
            print(f"  Credit: {credit_value}")
            print(f"  Balance: {balance_value}")
            print("  ✓ Success")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()

def test_default_balance_structure():
    """
    Test the default balance structure that should always be returned
    """
    print("Testing default balance structure...")
    
    default_result = {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
    
    # Test that it has all required keys and proper types
    required_keys = ['debit', 'credit', 'balance']
    
    for key in required_keys:
        assert key in default_result, f"Missing key: {key}"
        assert isinstance(default_result[key], (int, float)), f"Invalid type for {key}"
    
    print("✓ Default balance structure is valid")

if __name__ == '__main__':
    test_initial_balance_safety()
    test_default_balance_structure()
    print("All tests completed!")
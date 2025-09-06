#!/usr/bin/env python3
"""
One-command demo of the Connascence Safety Analyzer.
Copy and paste this into a file, then run the analyzer to see immediate results.
"""

# This file intentionally contains common connascence violations for demo purposes

class PaymentProcessor:
    def __init__(self):
        self.data = {}
        self.cnt = 0

    # Magic numbers and parameter coupling
    def process_payment(self, amount, card_type, cvv, exp_month, exp_year):
        if amount > 10000:  # Magic limit
            return False
        if card_type not in [1, 2, 3]:  # Magic card types: 1=Visa, 2=MC, 3=Amex
            return False
        if len(str(cvv)) != 3 and card_type != 3:  # Amex has 4-digit CVV
            return False

        # God object - doing validation, processing, and storage
        payment_id = self.cnt + 1
        self.data[payment_id] = {
            'amount': amount,
            'type': card_type,
            'processed_at': self._get_timestamp(),
            'fee': self._calculate_fee(amount, card_type),
            'status': 1  # Magic: 1=pending, 2=complete, 3=failed
        }
        self.cnt += 1
        return payment_id

    def _get_timestamp(self):
        import time
        return int(time.time())

    def _calculate_fee(self, amount, card_type):
        # Duplicate fee calculation logic appears elsewhere too
        if card_type == 1:  # Visa
            return amount * 0.029
        elif card_type == 2:  # MasterCard
            return amount * 0.031
        else:  # Amex
            return amount * 0.035

# Duplicate fee logic in different class
class FeeCalculator:
    @staticmethod
    def get_processing_fee(amount, card_type):
        # Same algorithm as above - violation of DRY principle
        if card_type == 1:
            return amount * 0.029
        elif card_type == 2:
            return amount * 0.031
        else:
            return amount * 0.035

# Function with parameter position coupling
def generate_report(payments, include_fees, sort_by_date, format_currency):
    # Parameters must be in exact order, creating coupling
    results = []
    for payment in payments.values():
        if payment['status'] != 3:  # Magic number again
            results.append(payment)

    if sort_by_date:
        results.sort(key=lambda x: x['processed_at'])

    return results

"""
To see the analyzer in action:

1. Save this file as demo.py
2. Run: python -m analyzer.core --path demo.py --policy strict-core

Expected violations:
- Magic numbers (10000, card types 1/2/3, status codes)
- God object (PaymentProcessor doing too much)
- Parameter coupling (5+ positional parameters)
- Algorithm duplication (fee calculation)
- Inconsistent naming (cnt instead of count)

The analyzer will identify 8-12 violations and provide specific
refactoring recommendations with line numbers and severity levels.
"""

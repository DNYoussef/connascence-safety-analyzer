#!/usr/bin/env python3
"""
Test file with OBVIOUS duplications to verify our analyzer works.
"""

def calculate_total_price(items):
    """Calculate total price - version 1"""
    total = 0
    for item in items:
        price = item['price'] * (1 - item['discount']) if item.get('discount', 0) > 0 else item['price']
        total += price
    return total

def compute_final_cost(products):
    """Calculate total price - version 2 (DUPLICATE)"""
    total = 0
    for item in products:
        price = item['price'] * (1 - item['discount']) if item.get('discount', 0) > 0 else item['price']
        total += price
    return total

def process_user_data(user_info):
    """Process user data - version 1"""
    if not user_info:
        return None

    result = {}
    result['name'] = user_info['name'].strip().title()
    result['email'] = user_info['email'].lower()
    result['age'] = int(user_info.get('age', 0))

    return result

def handle_user_input(data):
    """Process user data - version 2 (DUPLICATE)"""
    if not data:
        return None

    result = {}
    result['name'] = data['name'].strip().title()
    result['email'] = data['email'].lower()
    result['age'] = int(data.get('age', 0))

    return result

def validate_email_format(email):
    """Validate email - simple version"""
    if '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    if not parts[0] or not parts[1]:
        return False
    return True

def check_email_validity(email_address):
    """Validate email - duplicate logic"""
    if '@' not in email_address:
        return False
    parts = email_address.split('@')
    if len(parts) != 2:
        return False
    if not parts[0] or not parts[1]:
        return False
    return True

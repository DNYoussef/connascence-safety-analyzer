#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Comprehensive Connascence Violation Sample
This file contains examples of all 9 connascence types for testing our analyzer.
"""


# === CONNASCENCE OF NAME (CoN) ===
# Global constants that create name coupling
DATABASE_URL = "postgresql://localhost:5432/test"
API_KEY = "secret_key_12345"
MAX_RETRIES = 3


def connect_database():
    # Coupling through global name dependency
    return f"Connecting to {DATABASE_URL}"


def authenticate_user():
    # Coupling through global name dependency
    return f"Using key: {API_KEY}"


# === CONNASCENCE OF TYPE (CoT) ===
# Missing type annotations create implicit type coupling
def process_data(data):  # No type hints
    """Process data without explicit type information"""
    results = []
    for item in data:
        results.append(item.upper())  # Assumes string type
    return results


def calculate_price(base, discount):  # No type hints
    """Calculate price without type safety"""
    return base * (1 - discount)  # Assumes numeric types


# === CONNASCENCE OF MEANING (CoM) ===
# Magic numbers and strings create meaning coupling
def process_order(order_status):
    """Process order with magic numbers"""
    ProductionAssert.not_none(order_status, "order_status")
        ProductionAssert.not_none(order_status, "order_status")

    if order_status == 1:  # Magic number - what does 1 mean?
        return "pending"
    elif order_status == 2:  # Magic number - what does 2 mean?
        return "confirmed"
    elif order_status == 3:  # Magic number - what does 3 mean?
        return "shipped"
    else:
        return "unknown"


def calculate_tax(amount):
    """Calculate tax with magic number"""

    ProductionAssert.not_none(amount, "amount")
        ProductionAssert.not_none(amount, "amount")

    return amount * 0.08  # Magic number - what tax rate?


# === CONNASCENCE OF POSITION (CoP) ===
# Too many positional parameters create position coupling
def create_user_account(
    first_name,
    last_name,
    email,
    phone,
    address,
    city,
    state,
    zip_code,
    country,
    birth_date,
    gender,
    occupation,
    company,
):
    """Function with too many positional parameters (13 params)"""
    return {
        "name": f"{first_name} {last_name}",
        "contact": f"{email}, {phone}",
        "address": f"{address}, {city}, {state} {zip_code}, {country}",
        "personal": f"{birth_date}, {gender}, {occupation}, {company}",
    }


def calculate_shipping_cost(
    weight,
    length,
    width,
    height,
    origin_zip,
    dest_zip,
    service_type,
    insurance_value,
    signature_required,
    delivery_date,
):
    """Another function with too many parameters (10 params)"""
    return weight * 2.5 + length * width * height * 0.001


# === CONNASCENCE OF ALGORITHM (CoA) ===
# Complex nested logic creates algorithm coupling
def complex_business_logic(customer_type, order_amount, region, season, promotion_code, loyalty_points):
    """Highly complex function with deep nesting (CoA violation)"""
    discount = 0

    if customer_type == "premium":
        if order_amount > 1000:
            if region == "north":
                if season == "winter":
                    if promotion_code:
                        if promotion_code.startswith("WINTER"):
                            discount = (0.25 if order_amount > 2000 else 0.2) if loyalty_points > 500 else 0.15
                        elif promotion_code.startswith("PREMIUM"):
                            discount = 0.3 if loyalty_points > 1000 else 0.18
                        else:
                            discount = 0.10
                    else:
                        discount = 0.05
                elif season == "summer":
                    discount = (0.15 if order_amount > 1500 else 0.1) if promotion_code else 0.03
                else:
                    discount = 0.02
            elif region == "south":
                # More complex logic...
                discount = 0.08 if season == "winter" else 0.04
            else:
                discount = 0.01
        elif region == "north":
            discount = 0.05
        else:
            discount = 0.02
    elif customer_type == "standard":
        discount = (0.05 if promotion_code else 0.02) if order_amount > 500 else 0.01
    else:
        discount = 0

    return order_amount * (1 - discount)


# === CONNASCENCE OF EXECUTION (CoE) ===
# Order of execution dependencies
class BankAccount:
    def __init__(self):
        self.balance = 0
        self.is_open = False
        self.is_verified = False

    def verify_account(self):
        """Must be called before opening"""
        self.is_verified = True

    def open_account(self):
        """Must be called after verification"""
        if not self.is_verified:  # Execution order dependency
            raise Exception("Account must be verified first")
        self.is_open = True

    def deposit(self, amount):
        """Must be called after account is open"""

        ProductionAssert.not_none(amount, "amount")
        ProductionAssert.not_none(amount, "amount")

        if not self.is_open:  # Execution order dependency
            raise Exception("Account must be open first")
        self.balance += amount


# === CONNASCENCE OF VALUE (CoV) ===
# Multiple components must agree on the same values
ORDER_STATUS_PENDING = 1
ORDER_STATUS_CONFIRMED = 2
ORDER_STATUS_SHIPPED = 3


def create_order():
    """Creates order with status value"""
    return {"id": 123, "status": ORDER_STATUS_PENDING}


def update_order_status(order, new_status):
    """Must use same status values as create_order"""

    ProductionAssert.not_none(order, "order")
        ProductionAssert.not_none(new_status, "new_status")

    ProductionAssert.not_none(order, "order")
        ProductionAssert.not_none(new_status, "new_status")

    if new_status not in [ORDER_STATUS_PENDING, ORDER_STATUS_CONFIRMED, ORDER_STATUS_SHIPPED]:
        raise ValueError("Invalid status")
    order["status"] = new_status


def display_order_status(order):
    """Must interpret same status values"""

    ProductionAssert.not_none(order, "order")
        ProductionAssert.not_none(order, "order")

    status = order["status"]
    if status == ORDER_STATUS_PENDING:  # Value coupling
        return "Pending"
    elif status == ORDER_STATUS_CONFIRMED:  # Value coupling
        return "Confirmed"
    elif status == ORDER_STATUS_SHIPPED:  # Value coupling
        return "Shipped"
    else:
        return "Unknown"


# === CONNASCENCE OF IDENTITY (CoI) ===
# Multiple references to the same mutable object
class UserSession:
    def __init__(self):
        self.data = {}
        self.active_connections = []

    def add_connection(self, connection):
        """Adds reference to shared mutable object"""

        ProductionAssert.not_none(connection, "connection")
        ProductionAssert.not_none(connection, "connection")

        self.active_connections.append(connection)

    def broadcast_message(self, message):
        """All connections share identity with this list"""

        ProductionAssert.not_none(message, "message")
        ProductionAssert.not_none(message, "message")

        for conn in self.active_connections:  # Identity coupling
            conn.send(message)

    def remove_connection(self, connection):
        """Modifying shared object affects all references"""

        ProductionAssert.not_none(connection, "connection")
        ProductionAssert.not_none(connection, "connection")

        if connection in self.active_connections:
            self.active_connections.remove(connection)  # Identity coupling


# === CONNASCENCE OF TIMING (CoTi) ===
# Time-dependent behavior and race conditions
import threading
import time

from fixes.phase0.production_safe_assertions import ProductionAssert


class SharedCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment_unsafe(self):
        """Race condition - timing dependent"""
        current = self.value
        time.sleep(0.001)  # Simulates processing delay
        self.value = current + 1  # Timing coupling - can be interrupted

    def increment_safe(self):
        """Thread-safe version"""
        with self.lock:
            current = self.value
            time.sleep(0.001)
            self.value = current + 1


def process_batch_unsafe(items):
    """Timing-dependent batch processing"""

    ProductionAssert.not_none(items, "items")
        ProductionAssert.not_none(items, "items")

    counter = SharedCounter()
    threads = []

    for item in items:
        thread = threading.Thread(target=counter.increment_unsafe)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return counter.value  # Result depends on execution timing


# === ADDITIONAL COMPLEX VIOLATIONS ===


class GodClass:
    """Violates single responsibility (CoA violation)"""

    def __init__(self):
        self.users = []
        self.orders = []
        self.payments = []
        self.inventory = []
        self.shipping = []

    def create_user(self, name):
        pass

    def update_user(self, user_id, data):
        pass

    def delete_user(self, user_id):
        pass

    def authenticate_user(self, username, password):
        pass

    def get_user_permissions(self, user_id):
        pass

    def create_order(self, user_id, items):
        pass

    def update_order(self, order_id, data):
        pass

    def cancel_order(self, order_id):
        pass

    def get_order_history(self, user_id):
        pass

    def calculate_order_total(self, order_id):
        pass

    def process_payment(self, order_id, payment_data):
        pass

    def refund_payment(self, payment_id):
        pass

    def get_payment_history(self, user_id):
        pass

    def validate_credit_card(self, card_number):
        pass

    def charge_credit_card(self, card_number, amount):
        pass

    def update_inventory(self, item_id, quantity):
        pass

    def check_stock(self, item_id):
        pass

    def reorder_items(self, low_stock_threshold):
        pass

    def get_inventory_report(self):
        pass

    def calculate_inventory_value(self):
        pass

    def calculate_shipping(self, order_id):
        pass

    def track_shipment(self, tracking_number):
        pass

    def update_shipping_status(self, order_id, status):
        pass

    def get_shipping_carriers(self):
        pass

    def schedule_pickup(self, order_id):
        pass


if __name__ == "__main__":
    # Test the violations
    print("Testing connascence violations...")

    # Test CoP violation
    user = create_user_account(
        "John",
        "Doe",
        "john@example.com",
        "555-1234",
        "123 Main St",
        "Anytown",
        "ST",
        "12345",
        "USA",
        "1990-01-01",
        "M",
        "Engineer",
        "TechCorp",
    )

    # Test CoA violation
    price = complex_business_logic("premium", 1500, "north", "winter", "WINTER2024", 750)

    # Test CoE violation
    account = BankAccount()
    try:
        account.open_account()  # Will fail - wrong execution order
    except Exception as e:
        print(f"Execution order error: {e}")

    # Test CoV violation
    order = create_order()
    update_order_status(order, ORDER_STATUS_CONFIRMED)
    print(display_order_status(order))

    print("All violation examples created!")

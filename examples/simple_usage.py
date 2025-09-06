#!/usr/bin/env python3
"""
Example demonstrating the new flake8-style connascence interface.

This shows how to use connascence with minimal configuration,
similar to how you'd use flake8.
"""

# Example of connascence violations that will be detected

# Connascence of Meaning (CoM) - Magic numbers
def calculate_circle_area(radius):
    return 3.14159 * radius * radius  # Magic number - should use math.pi

# Connascence of Position (CoP) - Too many positional parameters
def create_user(first_name, last_name, email, phone, address, city, state, zip_code):
    """This function has too many positional parameters."""
    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip_code': zip_code
    }

# Connascence of Algorithm (CoA) - Duplicated logic
def process_student_grade(grade):
    if grade >= 90:
        return "A"
    elif grade >= 80:
        return "B"
    elif grade >= 70:
        return "C"
    elif grade >= 60:
        return "D"
    else:
        return "F"

def process_employee_rating(rating):
    # Duplicated grading logic with different thresholds
    if rating >= 90:
        return "Excellent"
    elif rating >= 80:
        return "Good"
    elif rating >= 70:
        return "Average"
    elif rating >= 60:
        return "Below Average"
    else:
        return "Poor"

# God class example (Connascence of Identity)
class DataProcessor:
    """Example of a god class with too many responsibilities."""

    def __init__(self):
        self.data = []
        self.results = []
        self.cache = {}
        self.settings = {}
        self.validators = []
        self.transformers = []
        self.exporters = []

    def load_data(self, source): pass
    def validate_data(self): pass
    def clean_data(self): pass
    def transform_data(self): pass
    def analyze_data(self): pass
    def generate_report(self): pass
    def export_csv(self): pass
    def export_json(self): pass
    def export_xml(self): pass
    def send_email(self): pass
    def log_results(self): pass
    def backup_data(self): pass
    def compress_data(self): pass
    def encrypt_data(self): pass
    def decrypt_data(self): pass
    def authenticate_user(self): pass
    def authorize_action(self): pass
    def handle_errors(self): pass
    def retry_failed_operations(self): pass
    def monitor_performance(self): pass

if __name__ == "__main__":
    # Usage examples - these would normally be in documentation

    print("To analyze this file with connascence:")
    print("  connascence examples/simple_usage.py")
    print()
    print("To analyze current directory:")
    print("  connascence .")
    print()
    print("To use specific policy:")
    print("  connascence --policy=strict-core .")
    print()
    print("To get text output (like flake8):")
    print("  connascence --format=text .")
    print()
    print("To save results to file:")
    print("  connascence --output=results.json .")

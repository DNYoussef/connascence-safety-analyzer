"""
Test file for real-time analysis validation.
This file intentionally contains duplicate code to trigger violations.
"""


def calculate_area(length, width):
    """Calculate area of rectangle."""
    result = length * width
    return result


def calculate_rectangle_area(l, w):
    """Duplicate function - should trigger violation."""
    result = l * w
    return result


def process_data(data):
    """Process some data."""
    if data is None:
        return None

    processed = []
    for item in data:
        if item > 0:
            processed.append(item * 2)

    return processed


def handle_data(input_data):
    """Another duplicate - same logic as process_data."""
    if input_data is None:
        return None

    result = []
    for element in input_data:
        if element > 0:
            result.append(element * 2)

    return result


class DataProcessor:
    """Process data with duplicate methods."""

    def method_one(self, value):
        """First method."""
        temp = value + 1
        temp = temp * 2
        return temp - 1

    def method_two(self, num):
        """Duplicate method - same algorithm."""
        x = num + 1
        x = x * 2
        return x - 1

    def method_three(self, val):
        """NEWLY ADDED - Another duplicate to trigger new violation."""
        y = val + 1
        y = y * 2
        return y - 1

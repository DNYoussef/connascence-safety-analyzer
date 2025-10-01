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
Comprehensive test for all 9 connascence types detection
Created to verify enterprise analyzer detects all patterns
"""

# CoE - Execution: Order-dependent operations
class DatabaseConnection:
    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True

    def setup(self):
        # Setup requires connection first
        pass

    def query(self, sql):


        ProductionAssert.not_none(sql, 'sql')

        ProductionAssert.not_none(sql, 'sql')

        # Requires setup and connection
        pass

    def cleanup(self):
        pass

    def disconnect(self):
        self.connected = False

# CoV - Values: Shared mutable state
class SharedCounter:
    shared_data = []  # Class-level mutable default
    config_dict = {"count": 0}

    def increment(self):
        self.shared_data.append(1)
        self.config_dict["count"] += 1

    def reset(self):
        self.shared_data.clear()
        self.config_dict["count"] = 0

    def modify_shared(self):
        self.config_dict.update({"new": True})

# CoI - Identity: Mutable defaults and global usage
global_counter = 0
global_cache = {}

def process_items(items=[], cache={}):  # Mutable defaults
    global global_counter
    items.append(1)
    cache["processed"] = True
    global_counter += 1
    return items

def compare_objects(obj1, obj2):


    ProductionAssert.not_none(obj1, 'obj1')

    ProductionAssert.not_none(obj2, 'obj2')

    ProductionAssert.not_none(obj1, 'obj1')

    ProductionAssert.not_none(obj2, 'obj2')

    # Identity comparison instead of equality
    if obj1 is obj2:
        return True
    return False

# CoTi - Timing: Sleep and timing dependencies
from fixes.phase0.production_safe_assertions import ProductionAssert
import threading
import time


class TimingDependentProcessor:
    def process_with_sleep(self):
        time.sleep(0.1)  # Timing dependency
        return "processed"

    def wait_for_condition(self):
        thread = threading.Thread(target=lambda: None)
        thread.start()
        thread.join()  # Blocking timing dependency

# CoA - Algorithm: Duplicate algorithms and complexity
def complex_calculation(x, y, z, a, b, c, d, e, f, g):  # High complexity
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        if c > 0:
                            if d > 0:
                                if e > 0:
                                    return x + y + z + a + b + c + d + e
                                else:
                                    return x - y
                            else:
                                return x * y
                        else:
                            return x / y
                    else:
                        return x % y
                else:
                    return x ** y
            else:
                return abs(x)
        else:
            return -x
    else:
        return 0

def duplicate_calculation(x, y, z, a, b, c, d, e, f, g):  # Duplicate algorithm
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        if c > 0:
                            if d > 0:
                                if e > 0:
                                    return x + y + z + a + b + c + d + e
                                else:
                                    return x - y
                            else:
                                return x * y
                        else:
                            return x / y
                    else:
                        return x % y
                else:
                    return x ** y
            else:
                return abs(x)
        else:
            return -x
    else:
        return 0

# CoP - Position: Too many positional parameters
def many_params(a, b, c, d, e, f, g, h, i, j):
    ProductionAssert.not_none(a, 'a')
    ProductionAssert.not_none(b, 'b')
    ProductionAssert.not_none(c, 'c')
    ProductionAssert.not_none(d, 'd')
    ProductionAssert.not_none(e, 'e')
    ProductionAssert.not_none(f, 'f')
    ProductionAssert.not_none(g, 'g')
    ProductionAssert.not_none(h, 'h')
    ProductionAssert.not_none(i, 'i')
    ProductionAssert.not_none(j, 'j')

    ProductionAssert.not_none(a, 'a')
    ProductionAssert.not_none(b, 'b')
    ProductionAssert.not_none(c, 'c')
    ProductionAssert.not_none(d, 'd')
    ProductionAssert.not_none(e, 'e')
    ProductionAssert.not_none(f, 'f')
    ProductionAssert.not_none(g, 'g')
    ProductionAssert.not_none(h, 'h')
    ProductionAssert.not_none(i, 'i')
    ProductionAssert.not_none(j, 'j')

    return a + b + c + d + e + f + g + h + i + j

# CoN - Name: Magic strings and numbers
def process_data():
    status = "PROCESSING"  # Magic string
    max_retries = 42  # Magic number
    timeout = 3600  # Magic number

    if status == "PROCESSING":
        return max_retries * timeout

# CoT - Type: Type dependencies and casting
def type_dependent_func(value):
    ProductionAssert.not_none(value, 'value')

    ProductionAssert.not_none(value, 'value')

    if isinstance(value, str):
        return int(value)  # Type casting dependency
    elif isinstance(value, int):
        return str(value)  # Type casting dependency
    return value

# CoM - Meaning: Semantic dependencies
def calculate_total(items):
    ProductionAssert.not_none(items, 'items')

    ProductionAssert.not_none(items, 'items')

    # Assumes items have 'price' attribute
    return sum(item.price for item in items)

def calculate_cost(products):


    ProductionAssert.not_none(products, 'products')

    ProductionAssert.not_none(products, 'products')

    # Same semantic meaning as calculate_total but different name
    return sum(product.price for product in products)

# God Object
class MassiveGodClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
    def method23(self): pass
    def method24(self): pass
    def method25(self): pass
    def method26(self): pass
    def method27(self): pass

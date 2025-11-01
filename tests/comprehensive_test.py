# Comprehensive test file for ALL analyzer capabilities
# Tests: God Objects, Magic Literals, Duplicate Code, High Complexity, NASA violations, etc.

# 1. GOD OBJECT - Class with too many methods (threshold: 15)
class MassiveGodObject:
    """This class violates Single Responsibility Principle"""
    def __init__(self): pass
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass
    def method_22(self): pass
    def method_23(self): pass
    def method_24(self): pass
    def method_25(self): pass  # Way over threshold


# 2. MAGIC LITERALS - Configuration values that should be constants
def connect_to_database():
    timeout = 30  # Magic number
    retries = 3   # Magic number
    port = 5432   # Magic number
    max_connections = 100  # Magic number

    connection_string = f"localhost:{port}"
    return connection_string


# 3. PARAMETER BOMB - Too many parameters (threshold: 4-5)
def create_user_profile(
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
    salary
):  # 14 parameters - way too many!
    return {
        "name": f"{first_name} {last_name}",
        "contact": email
    }


# 4. HIGH CYCLOMATIC COMPLEXITY
def complex_business_logic(status, type, priority, user_role, is_admin):
    """High complexity function with many branches"""
    if status == "active":
        if type == "premium":
            if priority == "high":
                if user_role == "admin":
                    if is_admin:
                        return "full_access"
                    else:
                        return "limited_admin"
                else:
                    if priority == "urgent":
                        return "escalated"
                    else:
                        return "normal"
            elif priority == "medium":
                if user_role == "manager":
                    return "manager_access"
                else:
                    return "user_access"
            else:
                return "low_priority"
        elif type == "standard":
            if priority == "high":
                return "standard_high"
            else:
                return "standard_low"
        else:
            return "basic"
    elif status == "inactive":
        if type == "premium":
            return "suspended_premium"
        else:
            return "suspended"
    else:
        return "unknown"


# 5. DEEP NESTING - NASA limit is 4 levels
def deeply_nested_function(data):
    """Violates NASA deep nesting rule (max 4 levels)"""
    if data:  # Level 1
        for item in data:  # Level 2
            if item.get("active"):  # Level 3
                for sub in item.get("children", []):  # Level 4
                    if sub.get("enabled"):  # Level 5 - VIOLATION
                        for detail in sub.get("details", []):  # Level 6 - VIOLATION
                            if detail.get("valid"):  # Level 7 - VIOLATION
                                for nested in detail.get("nested", []):  # Level 8 - VIOLATION
                                    print(nested)  # Too deep!


# 6. DUPLICATE CODE - Repeated logic
def calculate_discount_for_premium():
    base_price = 100
    discount = 0.2
    tax = 0.08
    final_price = base_price * (1 - discount) * (1 + tax)
    return final_price


def calculate_discount_for_standard():
    base_price = 100  # Duplicate
    discount = 0.1    # Slightly different
    tax = 0.08        # Duplicate
    final_price = base_price * (1 - discount) * (1 + tax)  # Duplicate logic
    return final_price


def calculate_discount_for_basic():
    base_price = 100  # Duplicate
    discount = 0.05   # Slightly different
    tax = 0.08        # Duplicate
    final_price = base_price * (1 - discount) * (1 + tax)  # Duplicate logic
    return final_price


# 7. LONG FUNCTION - NASA recommends functions under 60 lines
def extremely_long_function():
    """This function is way too long"""
    line_1 = 1
    line_2 = 2
    line_3 = 3
    line_4 = 4
    line_5 = 5
    line_6 = 6
    line_7 = 7
    line_8 = 8
    line_9 = 9
    line_10 = 10
    line_11 = 11
    line_12 = 12
    line_13 = 13
    line_14 = 14
    line_15 = 15
    line_16 = 16
    line_17 = 17
    line_18 = 18
    line_19 = 19
    line_20 = 20
    line_21 = 21
    line_22 = 22
    line_23 = 23
    line_24 = 24
    line_25 = 25
    line_26 = 26
    line_27 = 27
    line_28 = 28
    line_29 = 29
    line_30 = 30
    line_31 = 31
    line_32 = 32
    line_33 = 33
    line_34 = 34
    line_35 = 35
    line_36 = 36
    line_37 = 37
    line_38 = 38
    line_39 = 39
    line_40 = 40
    line_41 = 41
    line_42 = 42
    line_43 = 43
    line_44 = 44
    line_45 = 45
    line_46 = 46
    line_47 = 47
    line_48 = 48
    line_49 = 49
    line_50 = 50
    line_51 = 51
    line_52 = 52
    line_53 = 53
    line_54 = 54
    line_55 = 55
    line_56 = 56
    line_57 = 57
    line_58 = 58
    line_59 = 59
    line_60 = 60
    line_61 = 61  # Over 60 lines
    line_62 = 62
    line_63 = 63
    line_64 = 64
    line_65 = 65
    line_66 = 66
    line_67 = 67
    line_68 = 68
    line_69 = 69
    line_70 = 70
    return line_70


# 8. GLOBAL STATE - Dangerous mutable global
global_counter = 0  # Global mutable state

def increment_global():
    global global_counter
    global_counter += 1


# 9. HARDCODED CREDENTIALS (security violation)
def connect_to_api():
    api_key = "hardcoded_secret_key_12345"  # Security violation
    username = "admin"  # Hardcoded credential
    password = "password123"  # Hardcoded credential
    return f"{username}:{password}@{api_key}"


# 10. DEAD CODE - Unreachable code
def function_with_dead_code(x):
    if x > 0:
        return "positive"
    else:
        return "negative"

    print("This will never execute")  # Dead code
    return "unreachable"  # Dead code


# 11. COMMENTED OUT CODE (code smell)
def old_implementation():
    # result = old_way_of_doing_things()
    # if result:
    #     return process(result)
    # else:
    #     return fallback()

    # New implementation
    return "new_way"

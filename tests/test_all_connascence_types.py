# Test file for all 9 connascence types
# This file intentionally contains connascence violations for testing

# CoN (Connascence of Name) - parameter names must match
def calculate_total(price, quantity):
    return price * quantity

result = calculate_total(10, 5)


# CoT (Connascence of Type) - types must match
def process_data(data: list):
    return len(data)

process_data([1, 2, 3])


# CoM (Connascence of Meaning) - magic numbers with implicit meaning
def set_status(status):
    if status == 1:  # Magic number: 1 = active
        return "Active"
    if status == 2:  # Magic number: 2 = inactive
        return "Inactive"
    if status == 3:  # Magic number: 3 = pending
        return "Pending"

set_status(1)


# CoP (Connascence of Position) - parameter order matters
def create_user(name, email, age):
    return {"name": name, "email": email, "age": age}

create_user("John", "john@example.com", 30)


# CoA (Connascence of Algorithm) - components must use same algorithm
def hash_password(password):
    # Simplified - both must use same algorithm
    return hash(password)


# CoE (Connascence of Execution) - order of execution matters
global_state = 0

def increment():
    global global_state
    global_state += 1

def get_value():
    return global_state

increment()  # Must execute before get_value()
value = get_value()


# CoV (Connascence of Value) - values must be synchronized
CONFIG_TIMEOUT = 30

def connect():
    # Must use same timeout value as CONFIG_TIMEOUT
    timeout = 30
    return f"Connecting with timeout {timeout}"


# CoI (Connascence of Identity) - same object identity required
shared_list = []

def add_to_shared(item):
    shared_list.append(item)

def get_shared():
    return shared_list


# CoId (Connascence of Identity Reference) - reference to same object
class User:
    def __init__(self, name):
        self.name = name

user1 = User("Alice")
user2 = user1  # CoId: both reference same object

# God Object - class with too many methods (>15)
class GodClass:
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
    def method16(self): pass  # Exceeds threshold

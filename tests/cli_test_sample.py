
# Test file with multiple connascence violations

def process_data(user_id, username, email, phone, address, city, state, zip_code):
    '''Function with 8 parameters - CoP violation'''
    MAGIC_NUMBER = 42  # CoM violation
    STATUS = "ACTIVE"  # CoM violation

    if user_id == MAGIC_NUMBER:
        return STATUS
    return None

class GodObject:
    '''Large class - potential god object'''
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass

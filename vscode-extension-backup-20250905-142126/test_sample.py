# Sample Python file for testing the VSCode extension
def calculate_area(length, width, height=1):
    # Magic number example
    if length > 100:
        return length * width * height
    else:
        return 0

# Long parameter list example  
def process_user_data(name, email, phone, address, city, state, zip_code, country, age, gender):
    return f"{name} from {city}, {state}"

# Duplicate code example
def calculate_rectangle_area(l, w):
    return l * w

def calculate_box_area(length, width):  
    return length * width

class DataProcessor:
    def __init__(self):
        pass
    
    def process(self, data):
        # Simple processing logic
        return data.upper() if isinstance(data, str) else str(data)
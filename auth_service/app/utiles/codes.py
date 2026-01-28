import random

def generate_6_digit_code() -> str:
    return f"{random.randint(0, 999999):06d}"

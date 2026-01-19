import re


def validate_password_format(pwd):
    has_letter = bool(re.search("[a-zA-Z]", pwd))
    has_digit = bool(re.search("[0-9]", pwd))
    return has_letter and has_digit and 6 <= len(pwd) <= 20


def validate_age(value):
    try:
        num = int(value)
    except (TypeError, ValueError):
        return False
    return 1 <= num <= 150


def validate_phone(value):
    if value is None:
        return False
    return bool(re.fullmatch(r"\d{11}", str(value)))


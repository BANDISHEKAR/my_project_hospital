"""Common input and validation helper functions for CLI modules."""

from datetime import datetime
import re


def print_line(width: int = 100):
    print("=" * width)


def pause():
    input("\nPress Enter to continue...")


def is_back(value: str) -> bool:
    return value.strip().lower() in {"back", "b", "cancel", "c", "exit", "q"}


def input_required(label: str):
    while True:
        value = input(f"{label}: ").strip()
        if is_back(value):
            return None
        if value:
            return value
        print("This field is required. Enter value or type 'back' to cancel.")


def input_optional(label: str):
    value = input(f"{label}: ").strip()
    if is_back(value):
        return None
    return value if value else None


def validate_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"[6-9][0-9]{9}", phone.strip()))


def input_phone(label: str, required: bool = True):
    while True:
        phone = input_required(label) if required else input_optional(label)
        if phone is None:
            return None
        if validate_phone(phone):
            return phone
        print("Invalid phone number. Enter 10 digits starting with 6, 7, 8, or 9.")


def validate_email(email: str) -> bool:
    if not email:
        return True
    return bool(re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()))


def input_email(label: str, required: bool = False):
    while True:
        email = input_required(label) if required else input_optional(label)
        if email is None:
            return None
        if validate_email(email):
            return email
        print("Invalid email format. Example: name@example.com")


def input_int(label: str, required: bool = True, min_value=None, max_value=None):
    while True:
        raw = input_required(label) if required else input_optional(label)
        if raw is None:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("Enter a valid number.")
            continue
        if min_value is not None and value < min_value:
            print(f"Value must be greater than or equal to {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Value must be less than or equal to {max_value}.")
            continue
        return value


def input_float(label: str, required: bool = True, min_value=None):
    while True:
        raw = input_required(label) if required else input_optional(label)
        if raw is None:
            return None
        try:
            value = float(raw)
        except ValueError:
            print("Enter a valid amount.")
            continue
        if min_value is not None and value < min_value:
            print(f"Value must be greater than or equal to {min_value}.")
            continue
        return value


def input_date(label: str, required: bool = True):
    while True:
        raw = input_required(f"{label} (YYYY-MM-DD)") if required else input_optional(f"{label} (YYYY-MM-DD)")
        if raw is None:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD. Example: 2026-06-29")


def input_gender(required: bool = False):
    while True:
        print("\nGender")
        print("1. Male")
        print("2. Female")
        print("3. Other")
        print("4. Skip" if not required else "")
        choice = input("Enter choice: ").strip()
        if is_back(choice):
            return None
        if choice == "1":
            return "Male"
        if choice == "2":
            return "Female"
        if choice == "3":
            return "Other"
        if choice == "4" and not required:
            return None
        print("Invalid choice.")


def input_status(default: str = "Active"):
    while True:
        print("\nStatus")
        print("1. Active")
        print("2. Inactive")
        choice = input(f"Enter choice [default {default}]: ").strip()
        if not choice:
            return default
        if is_back(choice):
            return None
        if choice == "1":
            return "Active"
        if choice == "2":
            return "Inactive"
        print("Invalid choice.")


def input_payment_method():
    methods = {
        "1": "Cash",
        "2": "UPI",
        "3": "Card",
        "4": "Online",
        "5": "Insurance",
        "6": "Other",
    }
    while True:
        print("\nPayment Method")
        print("1. Cash")
        print("2. UPI")
        print("3. Card")
        print("4. Online")
        print("5. Insurance")
        print("6. Other")
        choice = input("Enter choice: ").strip()
        if is_back(choice):
            return None
        if choice in methods:
            return methods[choice]
        print("Invalid choice.")


def input_day():
    days = {"1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat", "7": "Sun"}
    while True:
        print("\nSelect Day")
        print("1. Mon")
        print("2. Tue")
        print("3. Wed")
        print("4. Thu")
        print("5. Fri")
        print("6. Sat")
        print("7. Sun")
        choice = input("Enter choice: ").strip()
        if is_back(choice):
            return None
        if choice in days:
            return days[choice]
        print("Invalid choice.")


def input_session_type():
    while True:
        print("\nSelect Session")
        print("1. Morning")
        print("2. Evening")
        choice = input("Enter choice: ").strip()
        if is_back(choice):
            return None
        if choice == "1":
            return "Morning"
        if choice == "2":
            return "Evening"
        print("Invalid choice.")


def input_room_no():
    while True:
        print("\nSelect Room")
        print("1. Room-1")
        print("2. Room-2")
        choice = input("Enter choice: ").strip()
        if is_back(choice):
            return None
        if choice == "1":
            return "Room-1"
        if choice == "2":
            return "Room-2"
        print("Invalid choice.")


def validate_12hr_time(value: str) -> bool:
    return bool(re.fullmatch(r"(0[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)", value.strip()))


def normalize_12hr_time(value: str) -> str:
    value = value.strip().upper()
    value = re.sub(r"\s*(AM|PM)$", r" \1", value)
    return value


def input_12hr_time(label: str):
    while True:
        value = input_required(f"{label} (Example: 09:00 AM)")
        if value is None:
            return None
        if validate_12hr_time(value):
            return normalize_12hr_time(value)
        print("Invalid time format. Use 12-hour format like 09:00 AM or 05:00 PM.")

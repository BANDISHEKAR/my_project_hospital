"""
DOCTOR_MANAGEMENT.py
Hospital Management System - Doctor Management + Doctor Availability

Tables used:
1. DOCTOR_MASTER
2. DOCTOR_AVAILABILITY

Required DB connection:
Create db_connection.py with a function get_connection() that returns an Oracle connection.

Example:
    import oracledb

    def get_connection():
        return oracledb.connect(
            user="YOUR_USERNAME",
            password="YOUR_PASSWORD",
            dsn="HOST:PORT/SERVICE_NAME"
        )
"""

import re

try:
    from db_connection import get_connection
except ImportError:
    get_connection = None


# ============================================================
# COMMON HELPERS
# ============================================================

def print_line():
    print("=" * 90)


def pause():
    input("\nPress Enter to continue...")


def is_back(value):
    return value.strip().lower() in ("back", "b", "cancel", "c", "exit")


def input_required(label):
    while True:
        value = input(f"{label}: ").strip()
        if is_back(value):
            return None
        if value:
            return value
        print("This field is required. Enter value or type 'back' to cancel.")


def input_optional(label):
    value = input(f"{label}: ").strip()
    if is_back(value):
        return None
    return value


def validate_phone(phone):
    return bool(re.fullmatch(r"[6-9][0-9]{9}", phone))


def input_phone(label):
    while True:
        phone = input_required(label)
        if phone is None:
            return None
        if validate_phone(phone):
            return phone
        print("Invalid phone number. Enter 10 digits starting with 6, 7, 8, or 9.")


def validate_email(email):
    if not email:
        return True
    return bool(re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def input_email(label):
    while True:
        email = input_optional(label)
        if email is None:
            return None
        if validate_email(email):
            return email
        print("Invalid email format.")


def input_number(label, allow_decimal=False):
    while True:
        value = input_required(label)
        if value is None:
            return None
        try:
            return float(value) if allow_decimal else int(value)
        except ValueError:
            print("Enter a valid number.")


def input_status():
    while True:
        print("\nStatus")
        print("1. Active")
        print("2. Inactive")
        choice = input("Enter choice: ").strip()

        if is_back(choice):
            return None
        if choice == "1":
            return "Active"
        if choice == "2":
            return "Inactive"
        print("Invalid choice.")


def validate_12hr_time(value):
    return bool(re.fullmatch(r"(0[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM|am|pm)", value.strip()))


def normalize_12hr_time(value):
    value = value.strip().upper().replace("  ", " ")
    value = re.sub(r"\s*(AM|PM)$", r" \1", value)
    return value


def input_12hr_time(label):
    while True:
        value = input_required(label + " (Example: 09:00 AM)")
        if value is None:
            return None
        if validate_12hr_time(value):
            return normalize_12hr_time(value)
        print("Invalid time format. Use 12-hour format like 09:00 AM or 05:00 PM.")


def get_next_id(cursor, table_name, id_column, prefix, width=3):
    query = f"""
        SELECT NVL(MAX(TO_NUMBER(SUBSTR({id_column}, {len(prefix) + 1}))), 0) + 1
        FROM {table_name}
        WHERE REGEXP_LIKE({id_column}, '^{prefix}[0-9]+$')
    """
    cursor.execute(query)
    next_num = cursor.fetchone()[0]
    return f"{prefix}{str(next_num).zfill(width)}"


def check_exists(cursor, table_name, column_name, value):
    cursor.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = :value",
        {"value": value}
    )
    return cursor.fetchone()[0] > 0


def get_db_connection():
    if get_connection is None:
        raise ImportError(
            "db_connection.py not found. Create db_connection.py with get_connection() function."
        )
    return get_connection()


# ============================================================
# DOCTOR MASTER HELPERS
# ============================================================

def choose_doctor_id(cursor, active_only=False):
    if active_only:
        cursor.execute("""
            SELECT DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, STATUS
            FROM DOCTOR_MASTER
            WHERE STATUS = 'Active'
            ORDER BY DOCTOR_ID
        """)
    else:
        cursor.execute("""
            SELECT DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, STATUS
            FROM DOCTOR_MASTER
            ORDER BY
                CASE WHEN STATUS = 'Active' THEN 1 ELSE 2 END,
                DOCTOR_ID
        """)

    rows = cursor.fetchall()

    if not rows:
        print("\nNo doctors found.")
        return None

    print("\nDoctor List")
    print_line()
    print(f"{'Doctor ID':<12}{'Doctor Name':<25}{'Specialization':<25}{'Status':<10}")
    print_line()

    for row in rows:
        print(f"{row[0]:<12}{row[1]:<25}{row[2]:<25}{row[3]:<10}")

    print_line()

    while True:
        doctor_id = input("Enter Doctor ID or type 'back': ").strip().upper()
        if is_back(doctor_id):
            return None

        if active_only:
            cursor.execute("""
                SELECT COUNT(*)
                FROM DOCTOR_MASTER
                WHERE DOCTOR_ID = :doctor_id AND STATUS = 'Active'
            """, {"doctor_id": doctor_id})
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM DOCTOR_MASTER
                WHERE DOCTOR_ID = :doctor_id
            """, {"doctor_id": doctor_id})

        if cursor.fetchone()[0] > 0:
            return doctor_id

        print("Invalid Doctor ID. Please select from the list.")


# ============================================================
# DOCTOR MASTER CRUD
# ============================================================

def add_doctor(conn):
    cursor = conn.cursor()

    print("\nADD DOCTOR")
    print_line()
    print("Type 'back' anytime to cancel.")

    doctor_id = get_next_id(cursor, "DOCTOR_MASTER", "DOCTOR_ID", "D", 3)
    print(f"Generated Doctor ID: {doctor_id}")

    doctor_name = input_required("Doctor Name")
    if doctor_name is None:
        return

    doctor_licence_no = input_required("Doctor Licence Number")
    if doctor_licence_no is None:
        return

    if check_exists(cursor, "DOCTOR_MASTER", "DOCTOR_LICENCE_NO", doctor_licence_no):
        print("\nDoctor licence number already exists.")
        return

    specialization = input_required("Specialization")
    if specialization is None:
        return

    phone = input_phone("Phone")
    if phone is None:
        return

    email = input_email("Email Optional")
    if email is None:
        return

    experience_years = input_number("Experience Years")
    if experience_years is None:
        return

    consultation_fee = input_number("Consultation Fee", allow_decimal=True)
    if consultation_fee is None:
        return

    available_days = input_required("Available Days Example: Mon,Tue,Wed")
    if available_days is None:
        return

    available_from = input_12hr_time("Available From")
    if available_from is None:
        return

    available_to = input_12hr_time("Available To")
    if available_to is None:
        return

    max_patients_per_slot = input_number("Max Patients Per Slot")
    if max_patients_per_slot is None:
        return

    status = input_status()
    if status is None:
        return

    try:
        cursor.execute("""
            INSERT INTO DOCTOR_MASTER (
                DOCTOR_ID,
                DOCTOR_NAME,
                DOCTOR_LICENCE_NO,
                SPECIALIZATION,
                PHONE,
                EMAIL,
                EXPERIENCE_YEARS,
                CONSULTATION_FEE,
                AVAILABLE_DAYS,
                AVAILABLE_FROM,
                AVAILABLE_TO,
                MAX_PATIENTS_PER_SLOT,
                STATUS
            )
            VALUES (
                :doctor_id,
                :doctor_name,
                :doctor_licence_no,
                :specialization,
                :phone,
                :email,
                :experience_years,
                :consultation_fee,
                :available_days,
                :available_from,
                :available_to,
                :max_patients_per_slot,
                :status
            )
        """, {
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "doctor_licence_no": doctor_licence_no,
            "specialization": specialization,
            "phone": phone,
            "email": email,
            "experience_years": experience_years,
            "consultation_fee": consultation_fee,
            "available_days": available_days,
            "available_from": available_from,
            "available_to": available_to,
            "max_patients_per_slot": max_patients_per_slot,
            "status": status
        })

        conn.commit()
        print(f"\nDoctor added successfully. Doctor ID: {doctor_id}")

    except Exception as e:
        conn.rollback()
        print("\nError while adding doctor:", e)


def display_doctors(rows):
    if not rows:
        print("\nNo doctor records found.")
        return

    print("\nDOCTOR DETAILS")
    print_line()
    header = (
        f"{'ID':<6}{'Name':<20}{'Licence No':<18}{'Specialization':<22}"
        f"{'Phone':<13}{'Exp':<6}{'Fee':<10}{'Days':<18}{'From':<10}{'To':<10}{'Max':<6}{'Status':<10}"
    )
    print(header)
    print_line()

    for row in rows:
        print(
            f"{row[0]:<6}{row[1]:<20}{row[2]:<18}{row[3]:<22}"
            f"{row[4]:<13}{row[6]:<6}{row[7]:<10}{row[8]:<18}"
            f"{row[9]:<10}{row[10]:<10}{row[11]:<6}{row[12]:<10}"
        )

    print_line()


def view_doctors(conn):
    cursor = conn.cursor()

    while True:
        print("\nVIEW DOCTORS")
        print_line()
        print("1. View All Doctors")
        print("2. View Active Doctors")
        print("3. View Inactive Doctors")
        print("4. View by Doctor ID")
        print("5. View by Specialization")
        print("6. Back")

        choice = input("Enter choice: ").strip()

        base_select = """
            SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION,
                   PHONE, EMAIL, EXPERIENCE_YEARS, CONSULTATION_FEE,
                   AVAILABLE_DAYS, AVAILABLE_FROM, AVAILABLE_TO,
                   MAX_PATIENTS_PER_SLOT, STATUS
            FROM DOCTOR_MASTER
        """

        if choice == "1":
            cursor.execute(base_select + " ORDER BY DOCTOR_ID")
            display_doctors(cursor.fetchall())

        elif choice == "2":
            cursor.execute(base_select + " WHERE STATUS = 'Active' ORDER BY DOCTOR_ID")
            display_doctors(cursor.fetchall())

        elif choice == "3":
            cursor.execute(base_select + " WHERE STATUS = 'Inactive' ORDER BY DOCTOR_ID")
            display_doctors(cursor.fetchall())

        elif choice == "4":
            doctor_id = choose_doctor_id(cursor)
            if doctor_id is None:
                continue
            cursor.execute(base_select + " WHERE DOCTOR_ID = :doctor_id", {"doctor_id": doctor_id})
            display_doctors(cursor.fetchall())

        elif choice == "5":
            specialization = input_required("Enter Specialization")
            if specialization is None:
                continue
            cursor.execute(
                base_select + " WHERE UPPER(SPECIALIZATION) LIKE UPPER(:specialization) ORDER BY DOCTOR_ID",
                {"specialization": f"%{specialization}%"}
            )
            display_doctors(cursor.fetchall())

        elif choice == "6":
            break

        else:
            print("Invalid choice.")

        pause()


def update_doctor(conn):
    cursor = conn.cursor()

    print("\nUPDATE DOCTOR")
    print_line()

    doctor_id = choose_doctor_id(cursor)
    if doctor_id is None:
        return

    update_fields = {
        "1": ("DOCTOR_NAME", "Doctor Name", "text"),
        "2": ("DOCTOR_LICENCE_NO", "Doctor Licence Number", "text"),
        "3": ("SPECIALIZATION", "Specialization", "text"),
        "4": ("PHONE", "Phone", "phone"),
        "5": ("EMAIL", "Email", "email"),
        "6": ("EXPERIENCE_YEARS", "Experience Years", "number"),
        "7": ("CONSULTATION_FEE", "Consultation Fee", "decimal"),
        "8": ("AVAILABLE_DAYS", "Available Days", "text"),
        "9": ("AVAILABLE_FROM", "Available From", "time"),
        "10": ("AVAILABLE_TO", "Available To", "time"),
        "11": ("MAX_PATIENTS_PER_SLOT", "Max Patients Per Slot", "number"),
        "12": ("STATUS", "Status", "status"),
    }

    while True:
        print("\nWhich field do you want to update?")
        print("1. Doctor Name")
        print("2. Doctor Licence Number")
        print("3. Specialization")
        print("4. Phone")
        print("5. Email")
        print("6. Experience Years")
        print("7. Consultation Fee")
        print("8. Available Days")
        print("9. Available From")
        print("10. Available To")
        print("11. Max Patients Per Slot")
        print("12. Status")
        print("13. Back")

        choice = input("Enter choice: ").strip()

        if choice == "13":
            break

        if choice not in update_fields:
            print("Invalid choice.")
            continue

        column_name, label, input_type = update_fields[choice]

        if input_type == "phone":
            new_value = input_phone(f"New {label}")
        elif input_type == "email":
            new_value = input_email(f"New {label}")
        elif input_type == "number":
            new_value = input_number(f"New {label}")
        elif input_type == "decimal":
            new_value = input_number(f"New {label}", allow_decimal=True)
        elif input_type == "time":
            new_value = input_12hr_time(f"New {label}")
        elif input_type == "status":
            new_value = input_status()
        else:
            new_value = input_required(f"New {label}")

        if new_value is None:
            print("Update cancelled.")
            continue

        if column_name == "DOCTOR_LICENCE_NO":
            cursor.execute("""
                SELECT COUNT(*)
                FROM DOCTOR_MASTER
                WHERE DOCTOR_LICENCE_NO = :licence_no
                AND DOCTOR_ID <> :doctor_id
            """, {"licence_no": new_value, "doctor_id": doctor_id})

            if cursor.fetchone()[0] > 0:
                print("This licence number is already used by another doctor.")
                continue

        try:
            cursor.execute(
                f"""
                UPDATE DOCTOR_MASTER
                SET {column_name} = :new_value
                WHERE DOCTOR_ID = :doctor_id
                """,
                {"new_value": new_value, "doctor_id": doctor_id}
            )

            if column_name == "SPECIALIZATION":
                cursor.execute("""
                    UPDATE DOCTOR_AVAILABILITY
                    SET SPECIALIZATION = :specialization
                    WHERE DOCTOR_ID = :doctor_id
                """, {"specialization": new_value, "doctor_id": doctor_id})

            if column_name == "STATUS" and new_value == "Inactive":
                cursor.execute("""
                    UPDATE DOCTOR_AVAILABILITY
                    SET STATUS = 'Inactive'
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

            conn.commit()
            print(f"{label} updated successfully.")

        except Exception as e:
            conn.rollback()
            print("Error while updating doctor:", e)


def delete_doctor(conn):
    cursor = conn.cursor()

    print("\nDELETE / DEACTIVATE DOCTOR")
    print_line()

    doctor_id = choose_doctor_id(cursor)
    if doctor_id is None:
        return

    cursor.execute("""
        SELECT COUNT(*)
        FROM APPOINTMENT
        WHERE DOCTOR_ID = :doctor_id
        AND STATUS IN ('Booked', 'Completed')
    """, {"doctor_id": doctor_id})

    appointment_count = cursor.fetchone()[0]

    if appointment_count > 0:
        print("\nThis doctor has appointment records.")
        print("So doctor cannot be deleted permanently.")
        confirm = input("Do you want to mark doctor as Inactive? (yes/no): ").strip().lower()

        if confirm == "yes":
            try:
                cursor.execute("""
                    UPDATE DOCTOR_MASTER
                    SET STATUS = 'Inactive'
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    UPDATE DOCTOR_AVAILABILITY
                    SET STATUS = 'Inactive'
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                conn.commit()
                print("Doctor and related availability sessions marked as Inactive.")

            except Exception as e:
                conn.rollback()
                print("Error while deactivating doctor:", e)
        else:
            print("Delete cancelled.")

    else:
        confirm = input("Are you sure you want to delete this doctor? (yes/no): ").strip().lower()

        if confirm == "yes":
            try:
                cursor.execute("""
                    DELETE FROM DOCTOR_AVAILABILITY
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    DELETE FROM DOCTOR_MASTER
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                conn.commit()
                print("Doctor deleted successfully.")

            except Exception as e:
                conn.rollback()
                print("Error while deleting doctor:", e)
        else:
            print("Delete cancelled.")


# ============================================================
# DOCTOR AVAILABILITY CRUD
# ============================================================

def input_day():
    days = {
        "1": "Mon",
        "2": "Tue",
        "3": "Wed",
        "4": "Thu",
        "5": "Fri",
        "6": "Sat",
        "7": "Sun"
    }

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
        print("\nSelect Session Type")
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


def add_doctor_availability(conn):
    cursor = conn.cursor()

    print("\nADD DOCTOR AVAILABILITY")
    print_line()
    print("Type 'back' anytime to cancel.")

    availability_id = get_next_id(cursor, "DOCTOR_AVAILABILITY", "AVAILABILITY_ID", "AV", 3)
    print(f"Generated Availability ID: {availability_id}")

    doctor_id = choose_doctor_id(cursor, active_only=True)
    if doctor_id is None:
        return

    cursor.execute("""
        SELECT DOCTOR_NAME, SPECIALIZATION
        FROM DOCTOR_MASTER
        WHERE DOCTOR_ID = :doctor_id
    """, {"doctor_id": doctor_id})
    doctor = cursor.fetchone()

    doctor_name = doctor[0]
    specialization = doctor[1]

    print(f"Selected Doctor: {doctor_name}")
    print(f"Specialization : {specialization}")

    day_name = input_day()
    if day_name is None:
        return

    session_type = input_session_type()
    if session_type is None:
        return

    room_no = input_room_no()
    if room_no is None:
        return

    start_time = input_12hr_time("Start Time")
    if start_time is None:
        return

    end_time = input_12hr_time("End Time")
    if end_time is None:
        return

    max_patients = input_number("Max Patients")
    if max_patients is None:
        return

    status = input_status()
    if status is None:
        return

    cursor.execute("""
        SELECT COUNT(*)
        FROM DOCTOR_AVAILABILITY
        WHERE DAY_NAME = :day_name
        AND ROOM_NO = :room_no
        AND START_TIME = :start_time
        AND END_TIME = :end_time
        AND STATUS = 'Active'
    """, {
        "day_name": day_name,
        "room_no": room_no,
        "start_time": start_time,
        "end_time": end_time
    })

    if cursor.fetchone()[0] > 0:
        print("\nThis room is already assigned for the same day and time.")
        return

    cursor.execute("""
        SELECT COUNT(*)
        FROM DOCTOR_AVAILABILITY
        WHERE DOCTOR_ID = :doctor_id
        AND DAY_NAME = :day_name
        AND START_TIME = :start_time
        AND END_TIME = :end_time
        AND STATUS = 'Active'
    """, {
        "doctor_id": doctor_id,
        "day_name": day_name,
        "start_time": start_time,
        "end_time": end_time
    })

    if cursor.fetchone()[0] > 0:
        print("\nThis doctor already has an active availability session at the same time.")
        return

    try:
        cursor.execute("""
            INSERT INTO DOCTOR_AVAILABILITY (
                AVAILABILITY_ID,
                DAY_NAME,
                SESSION_TYPE,
                ROOM_NO,
                START_TIME,
                END_TIME,
                DOCTOR_ID,
                SPECIALIZATION,
                MAX_PATIENTS,
                STATUS
            )
            VALUES (
                :availability_id,
                :day_name,
                :session_type,
                :room_no,
                :start_time,
                :end_time,
                :doctor_id,
                :specialization,
                :max_patients,
                :status
            )
        """, {
            "availability_id": availability_id,
            "day_name": day_name,
            "session_type": session_type,
            "room_no": room_no,
            "start_time": start_time,
            "end_time": end_time,
            "doctor_id": doctor_id,
            "specialization": specialization,
            "max_patients": max_patients,
            "status": status
        })

        conn.commit()
        print(f"\nDoctor availability added successfully. Availability ID: {availability_id}")

    except Exception as e:
        conn.rollback()
        print("\nError while adding doctor availability:", e)


def display_availability(rows):
    if not rows:
        print("\nNo availability records found.")
        return

    print("\nDOCTOR AVAILABILITY DETAILS")
    print_line()
    print(
        f"{'AV ID':<8}{'Day':<6}{'Session':<10}{'Room':<10}"
        f"{'Start':<10}{'End':<10}{'Doc ID':<8}{'Doctor Name':<22}"
        f"{'Specialization':<22}{'Max':<6}{'Status':<10}"
    )
    print_line()

    for row in rows:
        print(
            f"{row[0]:<8}{row[1]:<6}{row[2]:<10}{row[3]:<10}"
            f"{row[4]:<10}{row[5]:<10}{row[6]:<8}{row[7]:<22}"
            f"{row[8]:<22}{row[9]:<6}{row[10]:<10}"
        )

    print_line()


def view_doctor_availability(conn):
    cursor = conn.cursor()

    while True:
        print("\nVIEW DOCTOR AVAILABILITY")
        print_line()
        print("1. View All Availability")
        print("2. View Active Availability")
        print("3. View by Day")
        print("4. View by Doctor")
        print("5. View by Specialization")
        print("6. Back")

        choice = input("Enter choice: ").strip()

        base_query = """
            SELECT DA.AVAILABILITY_ID, DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO,
                   DA.START_TIME, DA.END_TIME, DA.DOCTOR_ID, DM.DOCTOR_NAME,
                   DA.SPECIALIZATION, DA.MAX_PATIENTS, DA.STATUS
            FROM DOCTOR_AVAILABILITY DA
            JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        """

        order_query = """
            ORDER BY
                CASE DA.DAY_NAME
                    WHEN 'Mon' THEN 1
                    WHEN 'Tue' THEN 2
                    WHEN 'Wed' THEN 3
                    WHEN 'Thu' THEN 4
                    WHEN 'Fri' THEN 5
                    WHEN 'Sat' THEN 6
                    WHEN 'Sun' THEN 7
                END,
                DA.START_TIME,
                DA.ROOM_NO
        """

        if choice == "1":
            cursor.execute(base_query + order_query)
            display_availability(cursor.fetchall())

        elif choice == "2":
            cursor.execute(base_query + " WHERE DA.STATUS = 'Active' " + order_query)
            display_availability(cursor.fetchall())

        elif choice == "3":
            day_name = input_day()
            if day_name is None:
                continue
            cursor.execute(base_query + " WHERE DA.DAY_NAME = :day_name " + order_query, {"day_name": day_name})
            display_availability(cursor.fetchall())

        elif choice == "4":
            doctor_id = choose_doctor_id(cursor)
            if doctor_id is None:
                continue
            cursor.execute(base_query + " WHERE DA.DOCTOR_ID = :doctor_id " + order_query, {"doctor_id": doctor_id})
            display_availability(cursor.fetchall())

        elif choice == "5":
            specialization = input_required("Enter Specialization")
            if specialization is None:
                continue
            cursor.execute(
                base_query + " WHERE UPPER(DA.SPECIALIZATION) LIKE UPPER(:specialization) " + order_query,
                {"specialization": f"%{specialization}%"}
            )
            display_availability(cursor.fetchall())

        elif choice == "6":
            break

        else:
            print("Invalid choice.")

        pause()


def choose_availability_id(cursor):
    cursor.execute("""
        SELECT DA.AVAILABILITY_ID, DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO,
               DA.START_TIME, DA.END_TIME, DA.DOCTOR_ID, DM.DOCTOR_NAME,
               DA.SPECIALIZATION, DA.STATUS
        FROM DOCTOR_AVAILABILITY DA
        JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        ORDER BY
            CASE DA.DAY_NAME
                WHEN 'Mon' THEN 1
                WHEN 'Tue' THEN 2
                WHEN 'Wed' THEN 3
                WHEN 'Thu' THEN 4
                WHEN 'Fri' THEN 5
                WHEN 'Sat' THEN 6
                WHEN 'Sun' THEN 7
            END,
            DA.START_TIME,
            DA.ROOM_NO
    """)

    rows = cursor.fetchall()

    if not rows:
        print("\nNo doctor availability found.")
        return None

    print("\nDoctor Availability List")
    print_line()
    print(
        f"{'AV ID':<8}{'Day':<6}{'Session':<10}{'Room':<10}"
        f"{'Start':<10}{'End':<10}{'Doc ID':<8}{'Doctor Name':<22}"
        f"{'Specialization':<22}{'Status':<10}"
    )
    print_line()

    for row in rows:
        print(
            f"{row[0]:<8}{row[1]:<6}{row[2]:<10}{row[3]:<10}"
            f"{row[4]:<10}{row[5]:<10}{row[6]:<8}{row[7]:<22}"
            f"{row[8]:<22}{row[9]:<10}"
        )

    print_line()

    while True:
        availability_id = input("Enter Availability ID or type 'back': ").strip().upper()
        if is_back(availability_id):
            return None

        cursor.execute("""
            SELECT COUNT(*)
            FROM DOCTOR_AVAILABILITY
            WHERE AVAILABILITY_ID = :availability_id
        """, {"availability_id": availability_id})

        if cursor.fetchone()[0] > 0:
            return availability_id

        print("Invalid Availability ID. Please select from the list.")


def update_doctor_availability(conn):
    cursor = conn.cursor()

    print("\nUPDATE DOCTOR AVAILABILITY")
    print_line()

    availability_id = choose_availability_id(cursor)
    if availability_id is None:
        return

    update_fields = {
        "1": ("DAY_NAME", "Day Name", "day"),
        "2": ("SESSION_TYPE", "Session Type", "session"),
        "3": ("ROOM_NO", "Room No", "room"),
        "4": ("START_TIME", "Start Time", "time"),
        "5": ("END_TIME", "End Time", "time"),
        "6": ("MAX_PATIENTS", "Max Patients", "number"),
        "7": ("STATUS", "Status", "status"),
    }

    while True:
        print("\nWhich field do you want to update?")
        print("1. Day Name")
        print("2. Session Type")
        print("3. Room No")
        print("4. Start Time")
        print("5. End Time")
        print("6. Max Patients")
        print("7. Status")
        print("8. Back")

        choice = input("Enter choice: ").strip()

        if choice == "8":
            break

        if choice not in update_fields:
            print("Invalid choice.")
            continue

        column_name, label, input_type = update_fields[choice]

        if input_type == "day":
            new_value = input_day()
        elif input_type == "session":
            new_value = input_session_type()
        elif input_type == "room":
            new_value = input_room_no()
        elif input_type == "time":
            new_value = input_12hr_time(f"New {label}")
        elif input_type == "number":
            new_value = input_number(f"New {label}")
        elif input_type == "status":
            new_value = input_status()
        else:
            new_value = input_required(f"New {label}")

        if new_value is None:
            print("Update cancelled.")
            continue

        try:
            cursor.execute(
                f"""
                UPDATE DOCTOR_AVAILABILITY
                SET {column_name} = :new_value
                WHERE AVAILABILITY_ID = :availability_id
                """,
                {"new_value": new_value, "availability_id": availability_id}
            )
            conn.commit()
            print(f"{label} updated successfully.")

        except Exception as e:
            conn.rollback()
            print("Error while updating availability:", e)


def delete_doctor_availability(conn):
    cursor = conn.cursor()

    print("\nDELETE / DEACTIVATE DOCTOR AVAILABILITY")
    print_line()

    availability_id = choose_availability_id(cursor)
    if availability_id is None:
        return

    cursor.execute("""
        SELECT COUNT(*)
        FROM APPOINTMENT
        WHERE AVAILABILITY_ID = :availability_id
        AND STATUS IN ('Booked', 'Completed')
    """, {"availability_id": availability_id})

    appointment_count = cursor.fetchone()[0]

    if appointment_count > 0:
        print("\nThis availability has appointment records.")
        print("So it cannot be deleted permanently.")
        confirm = input("Do you want to mark it as Inactive? (yes/no): ").strip().lower()

        if confirm == "yes":
            try:
                cursor.execute("""
                    UPDATE DOCTOR_AVAILABILITY
                    SET STATUS = 'Inactive'
                    WHERE AVAILABILITY_ID = :availability_id
                """, {"availability_id": availability_id})
                conn.commit()
                print("Availability marked as Inactive.")

            except Exception as e:
                conn.rollback()
                print("Error while deactivating availability:", e)
        else:
            print("Delete cancelled.")

    else:
        confirm = input("Are you sure you want to delete this availability? (yes/no): ").strip().lower()

        if confirm == "yes":
            try:
                cursor.execute("""
                    DELETE FROM DOCTOR_AVAILABILITY
                    WHERE AVAILABILITY_ID = :availability_id
                """, {"availability_id": availability_id})
                conn.commit()
                print("Availability deleted successfully.")

            except Exception as e:
                conn.rollback()
                print("Error while deleting availability:", e)
        else:
            print("Delete cancelled.")


# ============================================================
# MENUS
# ============================================================

def doctor_availability_menu(conn):
    while True:
        print("\nDOCTOR AVAILABILITY MENU")
        print_line()
        print("1. Add Doctor Availability")
        print("2. View Doctor Availability")
        print("3. Update Doctor Availability")
        print("4. Delete / Deactivate Doctor Availability")
        print("5. Back to Doctor Management")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_doctor_availability(conn)
            pause()
        elif choice == "2":
            view_doctor_availability(conn)
        elif choice == "3":
            update_doctor_availability(conn)
            pause()
        elif choice == "4":
            delete_doctor_availability(conn)
            pause()
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


def doctor_management_menu():
    try:
        conn = get_db_connection()
    except Exception as e:
        print("Database connection error:", e)
        return

    try:
        while True:
            print("\nDOCTOR MANAGEMENT")
            print_line()
            print("1. Add Doctor")
            print("2. View Doctors")
            print("3. Update Doctor")
            print("4. Delete / Deactivate Doctor")
            print("5. Doctor Availability")
            print("6. Back to Main Menu")

            choice = input("Enter choice: ").strip()

            if choice == "1":
                add_doctor(conn)
                pause()
            elif choice == "2":
                view_doctors(conn)
            elif choice == "3":
                update_doctor(conn)
                pause()
            elif choice == "4":
                delete_doctor(conn)
                pause()
            elif choice == "5":
                doctor_availability_menu(conn)
            elif choice == "6":
                break
            else:
                print("Invalid choice.")

    finally:
        conn.close()


if __name__ == "__main__":
    doctor_management_menu()

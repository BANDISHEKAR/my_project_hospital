"""Patient Management module."""

from utils.id_generator import get_next_id
from utils.input_helper import (
    print_line, pause, input_required, input_optional, input_phone, input_email,
    input_int, input_gender, is_back,
)


def display_patients(rows):
    if not rows:
        print("\nNo patient records found.")
        return
    print("\nPATIENT DETAILS")
    print_line()
    print(f"{'ID':<7}{'Name':<22}{'Age':<5}{'Gender':<8}{'Phone':<13}{'Email':<28}{'City':<15}{'Blood':<7}{'Reg Date':<12}")
    print_line()
    for r in rows:
        reg_date = r[9].strftime('%Y-%m-%d') if r[9] else '-'
        print(f"{r[0]:<7}{r[1]:<22}{str(r[2] or '-'):<5}{str(r[3] or '-'):<8}{r[4]:<13}{str(r[5] or '-'):<28}{str(r[7] or '-'):<15}{str(r[8] or '-'):<7}{reg_date:<12}")
    print_line()


def choose_patient_id(cursor):
    cursor.execute("""
        SELECT PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS, CITY, BLOOD_GROUP, REGISTRATION_DATE
        FROM PATIENT_MASTER ORDER BY PATIENT_ID
    """)
    rows = cursor.fetchall()
    display_patients(rows)
    if not rows:
        return None
    valid = {r[0].upper() for r in rows}
    while True:
        patient_id = input("Enter Patient ID or type 'back': ").strip().upper()
        if is_back(patient_id):
            return None
        if patient_id in valid:
            return patient_id
        print("Invalid Patient ID. Select from the list.")


def add_patient(conn):
    cursor = conn.cursor()
    print("\nADD PATIENT")
    print_line()
    print("Type 'back' anytime to cancel.")
    patient_id = get_next_id(cursor, "PATIENT_MASTER", "PATIENT_ID", "P", 3)
    print(f"Generated Patient ID: {patient_id}")

    name = input_required("Patient Name")
    if name is None: return
    age = input_int("Age Optional", required=False, min_value=0, max_value=120)
    gender = input_gender(required=False)
    phone = input_phone("Phone")
    if phone is None: return
    email = input_email("Email Optional")
    address = input_optional("Address Optional")
    city = input_optional("City Optional")
    blood_group = input_optional("Blood Group Optional")
    emergency_contact = input_phone("Emergency Contact Optional", required=False)

    try:
        cursor.execute("""
            INSERT INTO PATIENT_MASTER (
                PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS, CITY,
                BLOOD_GROUP, EMERGENCY_CONTACT, REGISTRATION_DATE
            ) VALUES (
                :patient_id, :name, :age, :gender, :phone, :email, :address, :city,
                :blood_group, :emergency_contact, SYSDATE
            )
        """, dict(patient_id=patient_id, name=name, age=age, gender=gender, phone=phone, email=email,
                  address=address, city=city, blood_group=blood_group, emergency_contact=emergency_contact))
        conn.commit()
        print(f"\nPatient added successfully. Patient ID: {patient_id}")
    except Exception as exc:
        conn.rollback()
        print("\nError while adding patient:", exc)


def view_patients(conn):
    cursor = conn.cursor()
    while True:
        print("\nVIEW PATIENTS")
        print_line()
        print("1. View All Patients")
        print("2. View by Patient ID")
        print("3. View by Phone")
        print("4. View by City")
        print("5. Back")
        choice = input("Enter choice: ").strip()
        base = """
            SELECT PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS, CITY, BLOOD_GROUP, REGISTRATION_DATE
            FROM PATIENT_MASTER
        """
        if choice == "1":
            cursor.execute(base + " ORDER BY PATIENT_ID")
        elif choice == "2":
            patient_id = choose_patient_id(cursor)
            if not patient_id: continue
            cursor.execute(base + " WHERE PATIENT_ID = :patient_id", {"patient_id": patient_id})
        elif choice == "3":
            phone = input_phone("Enter Phone")
            if not phone: continue
            cursor.execute(base + " WHERE PHONE = :phone", {"phone": phone})
        elif choice == "4":
            city = input_required("Enter City")
            if not city: continue
            cursor.execute(base + " WHERE UPPER(CITY) LIKE UPPER(:city) ORDER BY PATIENT_ID", {"city": f"%{city}%"})
        elif choice == "5":
            break
        else:
            print("Invalid choice.")
            continue
        display_patients(cursor.fetchall())
        pause()


def update_patient(conn):
    cursor = conn.cursor()
    print("\nUPDATE PATIENT")
    print_line()
    patient_id = choose_patient_id(cursor)
    if not patient_id: return
    fields = {
        "1": ("PATIENT_NAME", "Patient Name", "text"),
        "2": ("AGE", "Age", "int"),
        "3": ("GENDER", "Gender", "gender"),
        "4": ("PHONE", "Phone", "phone"),
        "5": ("EMAIL", "Email", "email"),
        "6": ("ADDRESS", "Address", "text_optional"),
        "7": ("CITY", "City", "text_optional"),
        "8": ("BLOOD_GROUP", "Blood Group", "text_optional"),
        "9": ("EMERGENCY_CONTACT", "Emergency Contact", "phone_optional"),
    }
    while True:
        print("\nWhich field do you want to update?")
        print("1. Patient Name")
        print("2. Age")
        print("3. Gender")
        print("4. Phone")
        print("5. Email")
        print("6. Address")
        print("7. City")
        print("8. Blood Group")
        print("9. Emergency Contact")
        print("10. Back")
        choice = input("Enter choice: ").strip()
        if choice == "10": break
        if choice not in fields:
            print("Invalid choice.")
            continue
        column, label, typ = fields[choice]
        if typ == "int": value = input_int(f"New {label}", min_value=0, max_value=120)
        elif typ == "gender": value = input_gender(required=False)
        elif typ == "phone": value = input_phone(f"New {label}")
        elif typ == "phone_optional": value = input_phone(f"New {label} Optional", required=False)
        elif typ == "email": value = input_email(f"New {label}")
        elif typ == "text_optional": value = input_optional(f"New {label} Optional")
        else: value = input_required(f"New {label}")
        if value is None and typ not in {"text_optional", "phone_optional", "email", "gender"}:
            print("Update cancelled.")
            continue
        try:
            cursor.execute(f"UPDATE PATIENT_MASTER SET {column} = :value WHERE PATIENT_ID = :patient_id", {"value": value, "patient_id": patient_id})
            conn.commit()
            print(f"{label} updated successfully.")
        except Exception as exc:
            conn.rollback()
            print("Error while updating patient:", exc)


def delete_patient(conn):
    cursor = conn.cursor()
    print("\nDELETE PATIENT")
    print_line()
    patient_id = choose_patient_id(cursor)
    if not patient_id: return
    cursor.execute("SELECT COUNT(*) FROM APPOINTMENT WHERE PATIENT_ID = :patient_id", {"patient_id": patient_id})
    count = cursor.fetchone()[0]
    if count > 0:
        print("\nThis patient has appointment records, so patient cannot be deleted.")
        return
    confirm = input("Are you sure you want to delete this patient? (yes/no): ").strip().lower()
    if confirm == "yes":
        try:
            cursor.execute("DELETE FROM PATIENT_MASTER WHERE PATIENT_ID = :patient_id", {"patient_id": patient_id})
            conn.commit()
            print("Patient deleted successfully.")
        except Exception as exc:
            conn.rollback()
            print("Error:", exc)


def patient_management_menu(conn):
    while True:
        print("\nPATIENT MANAGEMENT")
        print_line()
        print("1. Add Patient")
        print("2. View Patients")
        print("3. Update Patient")
        print("4. Delete Patient")
        print("5. Back to Main Menu")
        choice = input("Enter choice: ").strip()
        if choice == "1": add_patient(conn); pause()
        elif choice == "2": view_patients(conn)
        elif choice == "3": update_patient(conn); pause()
        elif choice == "4": delete_patient(conn); pause()
        elif choice == "5": break
        else: print("Invalid choice.")

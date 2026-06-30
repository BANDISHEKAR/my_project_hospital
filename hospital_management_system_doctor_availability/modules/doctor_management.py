"""Doctor Management module with Doctor Availability inside it."""

from utils.id_generator import get_next_id
from utils.input_helper import (
    print_line, pause, input_required, input_optional, input_phone, input_email,
    input_int, input_float, input_status, input_day, input_session_type,
    input_room_no, input_12hr_time, is_back,
)


def display_doctors(rows):
    if not rows:
        print("\nNo doctor records found.")
        return
    print("\nDOCTOR DETAILS")
    print_line()
    print(f"{'ID':<7}{'Name':<22}{'Licence No':<18}{'Specialization':<18}{'Phone':<13}{'Email':<28}{'Exp':<5}{'Fee':<10}{'Status':<10}")
    print_line()
    for r in rows:
        print(f"{r[0]:<7}{r[1]:<22}{r[2]:<18}{r[3]:<18}{r[4]:<13}{str(r[5] or '-'):<28}{str(r[6]):<5}{str(r[7]):<10}{r[8]:<10}")
    print_line()


def choose_doctor_id(cursor, active_only=False):
    sql = """
        SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
               EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
        FROM DOCTOR_MASTER
    """
    if active_only:
        sql += " WHERE STATUS = 'Active'"
    sql += " ORDER BY CASE WHEN STATUS = 'Active' THEN 1 ELSE 2 END, DOCTOR_ID"
    cursor.execute(sql)
    rows = cursor.fetchall()
    display_doctors(rows)
    if not rows:
        return None
    valid_ids = {r[0].upper() for r in rows}
    while True:
        doctor_id = input("Enter Doctor ID or type 'back': ").strip().upper()
        if is_back(doctor_id):
            return None
        if doctor_id in valid_ids:
            return doctor_id
        print("Invalid Doctor ID. Select from the list.")


def sync_doctor_availability_status(cursor, doctor_id, status):
    """Keep DOCTOR_AVAILABILITY status same as DOCTOR_MASTER status."""
    cursor.execute("""
        UPDATE DOCTOR_AVAILABILITY
        SET STATUS = :status
        WHERE DOCTOR_ID = :doctor_id
    """, {"status": status, "doctor_id": doctor_id})


def get_doctor_related_record_counts(cursor, doctor_id):
    """Return linked appointment, consultation, billing and availability counts for one doctor."""
    cursor.execute("SELECT COUNT(*) FROM APPOINTMENT WHERE DOCTOR_ID = :doctor_id", {"doctor_id": doctor_id})
    appointment_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM CONSULTATION
        WHERE APPOINTMENT_ID IN (
            SELECT APPOINTMENT_ID
            FROM APPOINTMENT
            WHERE DOCTOR_ID = :doctor_id
        )
    """, {"doctor_id": doctor_id})
    consultation_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM BILLING
        WHERE APPOINTMENT_ID IN (
            SELECT APPOINTMENT_ID
            FROM APPOINTMENT
            WHERE DOCTOR_ID = :doctor_id
        )
    """, {"doctor_id": doctor_id})
    billing_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM DOCTOR_AVAILABILITY WHERE DOCTOR_ID = :doctor_id", {"doctor_id": doctor_id})
    availability_count = cursor.fetchone()[0]

    return {
        "appointments": appointment_count,
        "consultations": consultation_count,
        "billing": billing_count,
        "availability": availability_count,
    }


def mark_doctor_inactive(cursor, doctor_id):
    """Deactivate doctor and all related availability sessions."""
    cursor.execute("""
        UPDATE DOCTOR_MASTER
        SET STATUS = 'Inactive'
        WHERE DOCTOR_ID = :doctor_id
    """, {"doctor_id": doctor_id})
    sync_doctor_availability_status(cursor, doctor_id, "Inactive")


def add_doctor(conn):
    cursor = conn.cursor()
    print("\nADD DOCTOR")
    print_line()
    print("Type 'back' anytime to cancel.")
    doctor_id = get_next_id(cursor, "DOCTOR_MASTER", "DOCTOR_ID", "D", 3)
    print(f"Generated Doctor ID: {doctor_id}")

    name = input_required("Doctor Name")
    if name is None: return
    licence = input_required("Doctor Licence Number")
    if licence is None: return
    specialization = input_required("Specialization")
    if specialization is None: return
    phone = input_phone("Phone")
    if phone is None: return
    email = input_email("Email Optional")
    exp = input_int("Experience Years", min_value=0)
    if exp is None: return
    fee = input_float("Consultation Fee", min_value=0)
    if fee is None: return
    status = input_status("Active")
    if status is None: return

    try:
        cursor.execute("""
            INSERT INTO DOCTOR_MASTER (
                DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS, CREATED_DATE
            ) VALUES (
                :doctor_id, :name, :licence, :specialization, :phone, :email,
                :exp, :fee, :status, SYSDATE
            )
        """, dict(doctor_id=doctor_id, name=name, licence=licence, specialization=specialization,
                  phone=phone, email=email, exp=exp, fee=fee, status=status))
        conn.commit()
        print(f"\nDoctor added successfully. Doctor ID: {doctor_id}")
    except Exception as exc:
        conn.rollback()
        print("\nError while adding doctor:", exc)


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

        if choice == "1":
            cursor.execute("""
                SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                       EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
                FROM DOCTOR_MASTER ORDER BY DOCTOR_ID
            """)
            display_doctors(cursor.fetchall())
        elif choice == "2":
            cursor.execute("""
                SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                       EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
                FROM DOCTOR_MASTER WHERE STATUS = 'Active' ORDER BY DOCTOR_ID
            """)
            display_doctors(cursor.fetchall())
        elif choice == "3":
            cursor.execute("""
                SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                       EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
                FROM DOCTOR_MASTER WHERE STATUS = 'Inactive' ORDER BY DOCTOR_ID
            """)
            display_doctors(cursor.fetchall())
        elif choice == "4":
            doctor_id = choose_doctor_id(cursor)
            if doctor_id:
                cursor.execute("""
                    SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                           EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
                    FROM DOCTOR_MASTER WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})
                display_doctors(cursor.fetchall())
        elif choice == "5":
            specialization = input_required("Enter Specialization")
            if specialization:
                cursor.execute("""
                    SELECT DOCTOR_ID, DOCTOR_NAME, DOCTOR_LICENCE_NO, SPECIALIZATION, PHONE, EMAIL,
                           EXPERIENCE_YEARS, CONSULTATION_FEE, STATUS
                    FROM DOCTOR_MASTER
                    WHERE UPPER(SPECIALIZATION) LIKE UPPER(:specialization)
                    ORDER BY DOCTOR_ID
                """, {"specialization": f"%{specialization}%"})
                display_doctors(cursor.fetchall())
        elif choice == "6":
            break
        else:
            print("Invalid choice.")
            continue
        pause()


def update_doctor(conn):
    cursor = conn.cursor()
    print("\nUPDATE DOCTOR")
    print_line()
    doctor_id = choose_doctor_id(cursor)
    if not doctor_id:
        return

    fields = {
        "1": ("DOCTOR_NAME", "Doctor Name", "text"),
        "2": ("DOCTOR_LICENCE_NO", "Doctor Licence Number", "text"),
        "3": ("SPECIALIZATION", "Specialization", "text"),
        "4": ("PHONE", "Phone", "phone"),
        "5": ("EMAIL", "Email", "email"),
        "6": ("EXPERIENCE_YEARS", "Experience Years", "int"),
        "7": ("CONSULTATION_FEE", "Consultation Fee", "float"),
        "8": ("STATUS", "Status", "status"),
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
        print("8. Status")
        print("9. Back")
        choice = input("Enter choice: ").strip()
        if choice == "9":
            break
        if choice not in fields:
            print("Invalid choice.")
            continue

        column, label, typ = fields[choice]
        if typ == "phone":
            value = input_phone(f"New {label}")
        elif typ == "email":
            value = input_email(f"New {label}")
        elif typ == "int":
            value = input_int(f"New {label}", min_value=0)
        elif typ == "float":
            value = input_float(f"New {label}", min_value=0)
        elif typ == "status":
            value = input_status()
        else:
            value = input_required(f"New {label}")

        if value is None:
            print("Update cancelled.")
            continue

        try:
            cursor.execute(
                f"UPDATE DOCTOR_MASTER SET {column} = :value WHERE DOCTOR_ID = :doctor_id",
                {"value": value, "doctor_id": doctor_id}
            )

            # Important: if doctor status changes, reflect same status in DOCTOR_AVAILABILITY also.
            if column == "STATUS":
                sync_doctor_availability_status(cursor, doctor_id, value)

            conn.commit()
            print(f"{label} updated successfully.")
            if column == "STATUS":
                print(f"Doctor availability records also updated to {value}.")

        except Exception as exc:
            conn.rollback()
            print("Error while updating doctor:", exc)


def delete_doctor(conn):
    cursor = conn.cursor()
    print("\nDELETE DOCTOR")
    print_line()
    doctor_id = choose_doctor_id(cursor)
    if not doctor_id:
        return

    counts = get_doctor_related_record_counts(cursor, doctor_id)
    total_related = sum(counts.values())

    if total_related > 0:
        print("\nThis doctor has related records.")
        print_line()
        print(f"Appointments         : {counts['appointments']}")
        print(f"Consultations        : {counts['consultations']}")
        print(f"Billing Records      : {counts['billing']}")
        print(f"Availability Records : {counts['availability']}")
        print_line()

        print("\nWhat do you want to do?")
        print("1. Delete doctor permanently with all related records")
        print("2. Make doctor inactive")
        print("3. Cancel")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            confirm = input(
                f"\nThis will permanently delete Doctor {doctor_id} with related availability, "
                "appointments, consultations and billing records. Type yes to continue: "
            ).strip().lower()

            if confirm != "yes":
                print("Delete cancelled.")
                return

            try:
                # Delete child records first to avoid ORA-02292 foreign key error.
                cursor.execute("""
                    DELETE FROM BILLING
                    WHERE APPOINTMENT_ID IN (
                        SELECT APPOINTMENT_ID
                        FROM APPOINTMENT
                        WHERE DOCTOR_ID = :doctor_id
                    )
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    DELETE FROM CONSULTATION
                    WHERE APPOINTMENT_ID IN (
                        SELECT APPOINTMENT_ID
                        FROM APPOINTMENT
                        WHERE DOCTOR_ID = :doctor_id
                    )
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    DELETE FROM APPOINTMENT
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    DELETE FROM DOCTOR_AVAILABILITY
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                cursor.execute("""
                    DELETE FROM DOCTOR_MASTER
                    WHERE DOCTOR_ID = :doctor_id
                """, {"doctor_id": doctor_id})

                conn.commit()
                print("\nDoctor and all related records deleted successfully.")

            except Exception as exc:
                conn.rollback()
                print("\nError while deleting doctor:", exc)

        elif choice == "2":
            try:
                mark_doctor_inactive(cursor, doctor_id)
                conn.commit()
                print("\nDoctor marked as Inactive successfully.")
                print("All related doctor availability records are also marked as Inactive.")
            except Exception as exc:
                conn.rollback()
                print("\nError while deactivating doctor:", exc)

        elif choice == "3":
            print("Delete cancelled.")
        else:
            print("Invalid choice. Delete cancelled.")

    else:
        confirm = input(
            f"\nAre you sure you want to permanently delete Doctor {doctor_id}? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Delete cancelled.")
            return

        try:
            cursor.execute("DELETE FROM DOCTOR_MASTER WHERE DOCTOR_ID = :doctor_id", {"doctor_id": doctor_id})
            conn.commit()
            print("\nDoctor deleted successfully.")
        except Exception as exc:
            conn.rollback()
            if "ORA-02292" in str(exc):
                print("\nThis doctor has child records, so direct delete is not possible.")
                print("Run Delete Doctor again and choose permanent delete with related records or inactive option.")
            else:
                print("\nError while deleting doctor:", exc)


def deactivate_doctor(conn):
    cursor = conn.cursor()
    print("\nDEACTIVATE DOCTOR")
    print_line()
    doctor_id = choose_doctor_id(cursor)
    if not doctor_id:
        return

    confirm = input(
        f"Are you sure you want to make Doctor {doctor_id} inactive? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Deactivate cancelled.")
        return

    try:
        mark_doctor_inactive(cursor, doctor_id)
        conn.commit()
        print("\nDoctor marked as Inactive successfully.")
        print("All related doctor availability records are also marked as Inactive.")
    except Exception as exc:
        conn.rollback()
        print("\nError while deactivating doctor:", exc)


def display_availability(rows):
    if not rows:
        print("\nNo doctor availability records found.")
        return
    print("\nDOCTOR AVAILABILITY DETAILS")
    print_line()
    print(f"{'AV ID':<8}{'Day':<6}{'Session':<10}{'Room':<9}{'Start':<10}{'End':<10}{'Doctor ID':<10}{'Doctor Name':<22}{'Spec':<16}{'Max':<5}{'Status':<10}")
    print_line()
    for r in rows:
        print(f"{r[0]:<8}{r[1]:<6}{r[2]:<10}{r[3]:<9}{r[4]:<10}{r[5]:<10}{r[6]:<10}{r[7]:<22}{r[8]:<16}{str(r[9]):<5}{r[10]:<10}")
    print_line()


def choose_availability_id(cursor, active_only=False, day_name=None):
    sql = """
        SELECT DA.AVAILABILITY_ID, DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO, DA.START_TIME, DA.END_TIME,
               DA.DOCTOR_ID, DM.DOCTOR_NAME, DA.SPECIALIZATION, DA.MAX_PATIENTS, DA.STATUS
        FROM DOCTOR_AVAILABILITY DA
        JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        WHERE 1 = 1
    """
    params = {}
    if active_only:
        sql += " AND DA.STATUS = 'Active' AND DM.STATUS = 'Active'"
    if day_name:
        sql += " AND DA.DAY_NAME = :day_name"
        params["day_name"] = day_name
    sql += """
        ORDER BY CASE DA.DAY_NAME WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
                                  WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6 ELSE 7 END,
                 TO_DATE(DA.START_TIME, 'HH:MI AM'), DA.ROOM_NO
    """
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    display_availability(rows)
    if not rows:
        return None
    valid = {r[0].upper() for r in rows}
    while True:
        availability_id = input("Enter Availability ID or type 'back': ").strip().upper()
        if is_back(availability_id):
            return None
        if availability_id in valid:
            return availability_id
        print("Invalid Availability ID. Select from the list.")


def add_doctor_availability(conn):
    cursor = conn.cursor()
    print("\nADD DOCTOR AVAILABILITY")
    print_line()
    availability_id = get_next_id(cursor, "DOCTOR_AVAILABILITY", "AVAILABILITY_ID", "AV", 3)
    print(f"Generated Availability ID: {availability_id}")
    doctor_id = choose_doctor_id(cursor, active_only=True)
    if not doctor_id: return
    cursor.execute("SELECT SPECIALIZATION FROM DOCTOR_MASTER WHERE DOCTOR_ID = :doctor_id", {"doctor_id": doctor_id})
    specialization = cursor.fetchone()[0]
    day_name = input_day()
    if day_name is None: return
    session_type = input_session_type()
    if session_type is None: return
    room_no = input_room_no()
    if room_no is None: return
    start_time = input_12hr_time("Start Time")
    if start_time is None: return
    end_time = input_12hr_time("End Time")
    if end_time is None: return
    max_patients = input_int("Max Patients", min_value=1)
    if max_patients is None: return

    # Doctor availability is automatically Active when created.
    # It will become Inactive only when the doctor is deactivated.
    status = "Active"

    try:
        cursor.execute("""
            INSERT INTO DOCTOR_AVAILABILITY (
                AVAILABILITY_ID, DAY_NAME, SESSION_TYPE, ROOM_NO, START_TIME, END_TIME,
                DOCTOR_ID, SPECIALIZATION, MAX_PATIENTS, STATUS
            ) VALUES (
                :availability_id, :day_name, :session_type, :room_no, :start_time, :end_time,
                :doctor_id, :specialization, :max_patients, :status
            )
        """, dict(availability_id=availability_id, day_name=day_name, session_type=session_type,
                  room_no=room_no, start_time=start_time, end_time=end_time, doctor_id=doctor_id,
                  specialization=specialization, max_patients=max_patients, status=status))
        conn.commit()
        print(f"Doctor availability added successfully. Availability ID: {availability_id}")
    except Exception as exc:
        conn.rollback()
        print("Error while adding availability:", exc)


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
        base = """
            SELECT DA.AVAILABILITY_ID, DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO, DA.START_TIME, DA.END_TIME,
                   DA.DOCTOR_ID, DM.DOCTOR_NAME, DA.SPECIALIZATION, DA.MAX_PATIENTS, DA.STATUS
            FROM DOCTOR_AVAILABILITY DA JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        """
        order = """
            ORDER BY CASE DA.DAY_NAME WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
                                      WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6 ELSE 7 END,
                     TO_DATE(DA.START_TIME, 'HH:MI AM'), DA.ROOM_NO
        """
        if choice == "1":
            cursor.execute(base + order)
        elif choice == "2":
            cursor.execute(base + " WHERE DA.STATUS = 'Active' AND DM.STATUS = 'Active' " + order)
        elif choice == "3":
            day = input_day()
            if day is None: continue
            cursor.execute(base + " WHERE DA.DAY_NAME = :day " + order, {"day": day})
        elif choice == "4":
            doctor_id = choose_doctor_id(cursor)
            if not doctor_id: continue
            cursor.execute(base + " WHERE DA.DOCTOR_ID = :doctor_id " + order, {"doctor_id": doctor_id})
        elif choice == "5":
            spec = input_required("Specialization")
            if not spec: continue
            cursor.execute(base + " WHERE UPPER(DA.SPECIALIZATION) LIKE UPPER(:spec) " + order, {"spec": f"%{spec}%"})
        elif choice == "6":
            break
        else:
            print("Invalid choice.")
            continue
        display_availability(cursor.fetchall())
        pause()


def update_doctor_availability(conn):
    cursor = conn.cursor()
    print("\nUPDATE DOCTOR AVAILABILITY")
    print_line()
    av_id = choose_availability_id(cursor)
    if not av_id:
        return

    fields = {
        "1": ("DAY_NAME", "Day", "day"),
        "2": ("SESSION_TYPE", "Session Type", "session"),
        "3": ("ROOM_NO", "Room No", "room"),
        "4": ("START_TIME", "Start Time", "time"),
        "5": ("END_TIME", "End Time", "time"),
        "6": ("MAX_PATIENTS", "Max Patients", "int"),
    }

    while True:
        print("\nWhich field do you want to update?")
        print("1. Day")
        print("2. Session Type")
        print("3. Room No")
        print("4. Start Time")
        print("5. End Time")
        print("6. Max Patients")
        print("7. Back")

        choice = input("Enter choice: ").strip()

        if choice == "7":
            break

        if choice not in fields:
            print("Invalid choice.")
            continue

        column, label, typ = fields[choice]

        if typ == "day":
            value = input_day()
        elif typ == "session":
            value = input_session_type()
        elif typ == "room":
            value = input_room_no()
        elif typ == "time":
            value = input_12hr_time(f"New {label}")
        elif typ == "int":
            value = input_int(f"New {label}", min_value=1)
        else:
            value = input_required(f"New {label}")

        if value is None:
            print("Update cancelled.")
            continue

        try:
            cursor.execute(
                f"UPDATE DOCTOR_AVAILABILITY SET {column} = :value WHERE AVAILABILITY_ID = :av_id",
                {"value": value, "av_id": av_id}
            )
            conn.commit()
            print(f"{label} updated successfully.")

        except Exception as exc:
            conn.rollback()
            print("Error while updating availability:", exc)




def get_availability_related_record_counts(cursor, availability_id):
    """Return linked appointment, consultation and billing counts for one availability session."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM APPOINTMENT
        WHERE AVAILABILITY_ID = :availability_id
    """, {"availability_id": availability_id})
    appointment_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM CONSULTATION
        WHERE APPOINTMENT_ID IN (
            SELECT APPOINTMENT_ID
            FROM APPOINTMENT
            WHERE AVAILABILITY_ID = :availability_id
        )
    """, {"availability_id": availability_id})
    consultation_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM BILLING
        WHERE APPOINTMENT_ID IN (
            SELECT APPOINTMENT_ID
            FROM APPOINTMENT
            WHERE AVAILABILITY_ID = :availability_id
        )
    """, {"availability_id": availability_id})
    billing_count = cursor.fetchone()[0]

    return {
        "appointments": appointment_count,
        "consultations": consultation_count,
        "billing": billing_count,
    }


def mark_availability_inactive(cursor, availability_id):
    """Deactivate one doctor availability session only."""
    cursor.execute("""
        UPDATE DOCTOR_AVAILABILITY
        SET STATUS = 'Inactive'
        WHERE AVAILABILITY_ID = :availability_id
    """, {"availability_id": availability_id})


def delete_doctor_availability(conn):
    cursor = conn.cursor()
    print("\nDELETE DOCTOR AVAILABILITY")
    print_line()

    av_id = choose_availability_id(cursor)
    if not av_id:
        return

    counts = get_availability_related_record_counts(cursor, av_id)
    total_related = sum(counts.values())

    if total_related > 0:
        print("\nThis doctor availability has related records.")
        print_line()
        print(f"Appointments    : {counts['appointments']}")
        print(f"Consultations   : {counts['consultations']}")
        print(f"Billing Records : {counts['billing']}")
        print_line()

        print("\nWhat do you want to do?")
        print("1. Delete availability permanently with all related records")
        print("2. Make availability inactive")
        print("3. Cancel")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            confirm = input(
                f"\nThis will permanently delete Availability {av_id} with related appointments, "
                "consultations and billing records. Type yes to continue: "
            ).strip().lower()

            if confirm != "yes":
                print("Delete cancelled.")
                return

            try:
                # Delete child records first to avoid ORA-02292 foreign key error.
                cursor.execute("""
                    DELETE FROM BILLING
                    WHERE APPOINTMENT_ID IN (
                        SELECT APPOINTMENT_ID
                        FROM APPOINTMENT
                        WHERE AVAILABILITY_ID = :availability_id
                    )
                """, {"availability_id": av_id})

                cursor.execute("""
                    DELETE FROM CONSULTATION
                    WHERE APPOINTMENT_ID IN (
                        SELECT APPOINTMENT_ID
                        FROM APPOINTMENT
                        WHERE AVAILABILITY_ID = :availability_id
                    )
                """, {"availability_id": av_id})

                cursor.execute("""
                    DELETE FROM APPOINTMENT
                    WHERE AVAILABILITY_ID = :availability_id
                """, {"availability_id": av_id})

                cursor.execute("""
                    DELETE FROM DOCTOR_AVAILABILITY
                    WHERE AVAILABILITY_ID = :availability_id
                """, {"availability_id": av_id})

                conn.commit()
                print("\nDoctor availability and all related records deleted successfully.")

            except Exception as exc:
                conn.rollback()
                print("\nError while deleting doctor availability:", exc)

        elif choice == "2":
            try:
                mark_availability_inactive(cursor, av_id)
                conn.commit()
                print("\nDoctor availability marked as Inactive successfully.")
                print("This session will not appear for new appointment booking.")
            except Exception as exc:
                conn.rollback()
                print("\nError while deactivating doctor availability:", exc)

        elif choice == "3":
            print("Delete cancelled.")
        else:
            print("Invalid choice. Delete cancelled.")

    else:
        confirm = input(
            f"\nAre you sure you want to permanently delete Availability {av_id}? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Delete cancelled.")
            return

        try:
            cursor.execute("""
                DELETE FROM DOCTOR_AVAILABILITY
                WHERE AVAILABILITY_ID = :availability_id
            """, {"availability_id": av_id})
            conn.commit()
            print("\nDoctor availability deleted successfully.")

        except Exception as exc:
            conn.rollback()
            if "ORA-02292" in str(exc):
                print("\nThis availability has child records, so direct delete is not possible.")
                print("Run Delete Doctor Availability again and choose permanent delete with related records or inactive option.")
            else:
                print("\nError while deleting doctor availability:", exc)


def deactivate_doctor_availability(conn):
    cursor = conn.cursor()
    print("\nDEACTIVATE DOCTOR AVAILABILITY")
    print_line()

    av_id = choose_availability_id(cursor)
    if not av_id:
        return

    confirm = input(
        f"Are you sure you want to make Availability {av_id} inactive? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Deactivate cancelled.")
        return

    try:
        mark_availability_inactive(cursor, av_id)
        conn.commit()
        print("\nDoctor availability marked as Inactive successfully.")
        print("This session will not appear for new appointment booking.")

    except Exception as exc:
        conn.rollback()
        print("\nError while deactivating doctor availability:", exc)

def doctor_availability_menu(conn):
    while True:
        print("\nDOCTOR AVAILABILITY MENU")
        print_line()
        print("1. Add Doctor Availability")
        print("2. View Doctor Availability")
        print("3. Update Doctor Availability")
        print("4. Delete Doctor Availability")
        print("5. Deactivate Doctor Availability")
        print("6. Back to Doctor Management")

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
            deactivate_doctor_availability(conn)
            pause()
        elif choice == "6":
            break
        else:
            print("Invalid choice.")


def doctor_management_menu(conn):
    while True:
        print("\nDOCTOR MANAGEMENT")
        print_line()
        print("1. Add Doctor")
        print("2. View Doctors")
        print("3. Update Doctor")
        print("4. Delete Doctor")
        print("5. Deactivate Doctor")
        print("6. Doctor Availability")
        print("7. Back to Main Menu")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            add_doctor(conn); pause()
        elif choice == "2":
            view_doctors(conn)
        elif choice == "3":
            update_doctor(conn); pause()
        elif choice == "4":
            delete_doctor(conn); pause()
        elif choice == "5":
            deactivate_doctor(conn); pause()
        elif choice == "6":
            doctor_availability_menu(conn)
        elif choice == "7":
            break
        else:
            print("Invalid choice.")

"""Consultation Management module.

Final flow:
1. Patient Consultation History
   - Shows all doctors' consultation records based on conditions.
   - Does not ask Doctor ID.
   - Does not start consultation.
2. Doctor Entry
   - Asks Doctor ID.
   - Shows only selected doctor's records.
   - Doctor can start/continue/update consultation.
"""

from utils.id_generator import get_next_id
from utils.input_helper import print_line, pause, input_required, input_optional, input_date, is_back


# -----------------------------------------------------------------------------
# Common formatting helpers
# -----------------------------------------------------------------------------

def format_date(value):
    """Return date as YYYY-MM-DD, safely handling Oracle DATE/datetime/string."""
    if not value:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def format_time(value):
    """Return time as HH:MM, safely handling Oracle DATE/datetime/string."""
    if not value:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)


def clean(value):
    """Display empty database values as '-' instead of None."""
    return str(value) if value not in (None, "") else "-"


def truncate(value, length):
    """Safely truncate long text for table display."""
    text = clean(value)
    return text[: length - 1] if len(text) > length else text


# -----------------------------------------------------------------------------
# Doctor helpers
# -----------------------------------------------------------------------------

def get_doctor_details(cursor, doctor_id):
    cursor.execute(
        """
        SELECT DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, STATUS
        FROM DOCTOR_MASTER
        WHERE UPPER(DOCTOR_ID) = :doctor_id
        """,
        {"doctor_id": doctor_id.upper()},
    )
    return cursor.fetchone()


def choose_doctor_id(cursor):
    """Ask Doctor ID and validate it from DOCTOR_MASTER."""
    while True:
        doctor_id = input("\nEnter Doctor ID or type 'back': ").strip().upper()
        if is_back(doctor_id):
            return None

        doctor = get_doctor_details(cursor, doctor_id)
        if doctor:
            return doctor

        print("Invalid Doctor ID. Please enter a valid Doctor ID.")


def print_doctor_header(doctor):
    print("\nDOCTOR CONSULTATION DASHBOARD")
    print_line()
    print(f"Doctor ID        : {doctor[0]}")
    print(f"Doctor Name      : {doctor[1]}")
    print(f"Specialization   : {doctor[2]}")


# -----------------------------------------------------------------------------
# Display functions
# -----------------------------------------------------------------------------

def display_today_for_doctor(rows):
    print("\nTODAY'S CONSULTATIONS")
    print_line(115)

    if not rows:
        print("No consultations found for today.")
        print_line(115)
        return

    print(
        f"{'Appt ID':<10}"
        f"{'Token':<8}"
        f"{'Time':<9}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Reason/Symptoms':<30}"
        f"{'Status':<12}"
    )
    print_line(115)

    for r in rows:
        # appointment_id, token_no, appointment_time, patient_id,
        # patient_name, reason_for_visit, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{clean(r[1]):<8}"
            f"{format_time(r[2]):<9}"
            f"{clean(r[3]):<12}"
            f"{truncate(r[4], 22):<22}"
            f"{truncate(r[5], 30):<30}"
            f"{clean(r[6]):<12}"
        )
    print_line(115)


def display_today_all_doctors(rows):
    print("\nTODAY'S CONSULTATIONS - ALL DOCTORS")
    print_line(135)

    if not rows:
        print("No consultations found for today.")
        print_line(135)
        return

    print(
        f"{'Appt ID':<10}"
        f"{'Token':<8}"
        f"{'Time':<9}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Doctor Name':<22}"
        f"{'Reason/Symptoms':<30}"
        f"{'Status':<12}"
    )
    print_line(135)

    for r in rows:
        # appointment_id, token_no, appointment_time, patient_id,
        # patient_name, doctor_name, reason_for_visit, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{clean(r[1]):<8}"
            f"{format_time(r[2]):<9}"
            f"{clean(r[3]):<12}"
            f"{truncate(r[4], 22):<22}"
            f"{truncate(r[5], 22):<22}"
            f"{truncate(r[6], 30):<30}"
            f"{clean(r[7]):<12}"
        )
    print_line(135)


def display_remaining_for_doctor(rows):
    print("\nREMAINING CONSULTATIONS - NOT COMPLETED")
    print_line(125)

    if not rows:
        print("No remaining consultations found.")
        print_line(125)
        return

    print(
        f"{'Appt ID':<10}"
        f"{'Date':<13}"
        f"{'Token':<8}"
        f"{'Time':<9}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Reason/Symptoms':<30}"
        f"{'Status':<12}"
    )
    print_line(125)

    for r in rows:
        # appointment_id, appointment_date, token_no, appointment_time,
        # patient_id, patient_name, reason_for_visit, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{format_date(r[1]):<13}"
            f"{clean(r[2]):<8}"
            f"{format_time(r[3]):<9}"
            f"{clean(r[4]):<12}"
            f"{truncate(r[5], 22):<22}"
            f"{truncate(r[6], 30):<30}"
            f"{clean(r[7]):<12}"
        )
    print_line(125)


def display_remaining_all_doctors(rows):
    print("\nREMAINING CONSULTATIONS - ALL DOCTORS")
    print_line(145)

    if not rows:
        print("No remaining consultations found.")
        print_line(145)
        return

    print(
        f"{'Appt ID':<10}"
        f"{'Date':<13}"
        f"{'Token':<8}"
        f"{'Time':<9}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Doctor Name':<22}"
        f"{'Reason/Symptoms':<30}"
        f"{'Status':<12}"
    )
    print_line(145)

    for r in rows:
        # appointment_id, appointment_date, token_no, appointment_time,
        # patient_id, patient_name, doctor_name, reason_for_visit, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{format_date(r[1]):<13}"
            f"{clean(r[2]):<8}"
            f"{format_time(r[3]):<9}"
            f"{clean(r[4]):<12}"
            f"{truncate(r[5], 22):<22}"
            f"{truncate(r[6], 22):<22}"
            f"{truncate(r[7], 30):<30}"
            f"{clean(r[8]):<12}"
        )
    print_line(145)


def display_completed_for_doctor(rows):
    print("\nCOMPLETED CONSULTATIONS")
    print_line(130)

    if not rows:
        print("No completed consultations found.")
        print_line(130)
        return

    print(
        f"{'Cons ID':<10}"
        f"{'Appt ID':<10}"
        f"{'Date':<13}"
        f"{'Token':<8}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Diagnosis':<28}"
        f"{'Status':<12}"
    )
    print_line(130)

    for r in rows:
        # consultation_id, appointment_id, consultation_date, token_no,
        # patient_id, patient_name, diagnosis, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{clean(r[1]):<10}"
            f"{format_date(r[2]):<13}"
            f"{clean(r[3]):<8}"
            f"{clean(r[4]):<12}"
            f"{truncate(r[5], 22):<22}"
            f"{truncate(r[6], 28):<28}"
            f"{clean(r[7]):<12}"
        )
    print_line(130)


def display_completed_all_doctors(rows):
    print("\nCOMPLETED CONSULTATIONS - ALL DOCTORS")
    print_line(150)

    if not rows:
        print("No completed consultations found.")
        print_line(150)
        return

    print(
        f"{'Cons ID':<10}"
        f"{'Appt ID':<10}"
        f"{'Date':<13}"
        f"{'Token':<8}"
        f"{'Patient ID':<12}"
        f"{'Patient Name':<22}"
        f"{'Doctor Name':<22}"
        f"{'Diagnosis':<28}"
        f"{'Status':<12}"
    )
    print_line(150)

    for r in rows:
        # consultation_id, appointment_id, consultation_date, token_no,
        # patient_id, patient_name, doctor_name, diagnosis, consultation_status
        print(
            f"{clean(r[0]):<10}"
            f"{clean(r[1]):<10}"
            f"{format_date(r[2]):<13}"
            f"{clean(r[3]):<8}"
            f"{clean(r[4]):<12}"
            f"{truncate(r[5], 22):<22}"
            f"{truncate(r[6], 22):<22}"
            f"{truncate(r[7], 28):<28}"
            f"{clean(r[8]):<12}"
        )
    print_line(150)


def display_full_consultation(row):
    if not row:
        print("No consultation/appointment details found.")
        return

    print("\nCONSULTATION FULL DETAILS")
    print_line(80)
    print(f"Appointment ID       : {clean(row[0])}")
    print(f"Appointment Date     : {format_date(row[1])}")
    print(f"Appointment Time     : {format_time(row[2])}")
    print(f"Token No             : {clean(row[3])}")
    print(f"Patient ID           : {clean(row[4])}")
    print(f"Patient Name         : {clean(row[5])}")
    print(f"Doctor ID            : {clean(row[6])}")
    print(f"Doctor Name          : {clean(row[7])}")
    print(f"Reason for Visit     : {clean(row[8])}")
    print(f"Consultation ID      : {clean(row[9])}")
    print(f"Consultation Date    : {format_date(row[10])}")
    print(f"Symptoms             : {clean(row[11])}")
    print(f"Diagnosis            : {clean(row[12])}")
    print(f"Prescription         : {clean(row[13])}")
    print(f"Follow-up Date       : {format_date(row[14])}")
    print(f"Doctor Notes         : {clean(row[15])}")
    print(f"Consultation Status  : {clean(row[16])}")
    print_line(80)


# -----------------------------------------------------------------------------
# Query helpers - doctor-wise
# -----------------------------------------------------------------------------

def fetch_today_consultations_for_doctor(cursor, doctor_id):
    """Booked appointments for today should reflect in consultation list."""
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.TOKEN_NO,
               A.APPOINTMENT_TIME,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               A.REASON_FOR_VISIT,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(A.DOCTOR_ID) = :doctor_id
          AND TRUNC(A.APPOINTMENT_DATE) = TRUNC(SYSDATE)
          AND UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
        ORDER BY A.TOKEN_NO, A.APPOINTMENT_TIME
        """,
        {"doctor_id": doctor_id.upper()},
    )
    return cursor.fetchall()


def fetch_remaining_consultations_for_doctor(cursor, doctor_id):
    """All doctor appointments where consultation is not completed."""
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.APPOINTMENT_DATE,
               A.TOKEN_NO,
               A.APPOINTMENT_TIME,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               A.REASON_FOR_VISIT,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(A.DOCTOR_ID) = :doctor_id
          AND UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
          AND UPPER(NVL(C.CONSULTATION_STATUS, 'PENDING')) <> 'COMPLETED'
        ORDER BY A.APPOINTMENT_DATE, A.TOKEN_NO, A.APPOINTMENT_TIME
        """,
        {"doctor_id": doctor_id.upper()},
    )
    return cursor.fetchall()


def fetch_completed_consultations_for_doctor(cursor, doctor_id):
    cursor.execute(
        """
        SELECT C.CONSULTATION_ID,
               A.APPOINTMENT_ID,
               C.CONSULTATION_DATE,
               A.TOKEN_NO,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               C.DIAGNOSIS,
               C.CONSULTATION_STATUS
        FROM CONSULTATION C
        JOIN APPOINTMENT A ON C.APPOINTMENT_ID = A.APPOINTMENT_ID
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        WHERE UPPER(A.DOCTOR_ID) = :doctor_id
          AND UPPER(C.CONSULTATION_STATUS) = 'COMPLETED'
        ORDER BY C.CONSULTATION_DATE DESC, A.TOKEN_NO
        """,
        {"doctor_id": doctor_id.upper()},
    )
    return cursor.fetchall()


# -----------------------------------------------------------------------------
# Query helpers - all doctors / patient history
# -----------------------------------------------------------------------------

def fetch_today_consultations_all(cursor):
    """All today's appointment/consultation records, not doctor-wise."""
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.TOKEN_NO,
               A.APPOINTMENT_TIME,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               D.DOCTOR_NAME,
               A.REASON_FOR_VISIT,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE TRUNC(A.APPOINTMENT_DATE) = TRUNC(SYSDATE)
          AND UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
        ORDER BY D.DOCTOR_NAME, A.TOKEN_NO, A.APPOINTMENT_TIME
        """
    )
    return cursor.fetchall()


def fetch_remaining_consultations_all(cursor):
    """All appointments where consultation is not completed, not doctor-wise."""
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.APPOINTMENT_DATE,
               A.TOKEN_NO,
               A.APPOINTMENT_TIME,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               D.DOCTOR_NAME,
               A.REASON_FOR_VISIT,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
          AND UPPER(NVL(C.CONSULTATION_STATUS, 'PENDING')) <> 'COMPLETED'
        ORDER BY A.APPOINTMENT_DATE, D.DOCTOR_NAME, A.TOKEN_NO, A.APPOINTMENT_TIME
        """
    )
    return cursor.fetchall()


def fetch_completed_consultations_all(cursor):
    cursor.execute(
        """
        SELECT C.CONSULTATION_ID,
               A.APPOINTMENT_ID,
               C.CONSULTATION_DATE,
               A.TOKEN_NO,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               D.DOCTOR_NAME,
               C.DIAGNOSIS,
               C.CONSULTATION_STATUS
        FROM CONSULTATION C
        JOIN APPOINTMENT A ON C.APPOINTMENT_ID = A.APPOINTMENT_ID
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        WHERE UPPER(C.CONSULTATION_STATUS) = 'COMPLETED'
        ORDER BY C.CONSULTATION_DATE DESC, D.DOCTOR_NAME, A.TOKEN_NO
        """
    )
    return cursor.fetchall()


# -----------------------------------------------------------------------------
# Query helpers - single appointment / update / save
# -----------------------------------------------------------------------------

def fetch_full_consultation_by_appointment(cursor, appointment_id, doctor_id=None):
    params = {"appointment_id": appointment_id.upper()}
    doctor_filter = ""

    if doctor_id:
        params["doctor_id"] = doctor_id.upper()
        doctor_filter = " AND UPPER(A.DOCTOR_ID) = :doctor_id"

    cursor.execute(
        f"""
        SELECT A.APPOINTMENT_ID,
               A.APPOINTMENT_DATE,
               A.APPOINTMENT_TIME,
               A.TOKEN_NO,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               A.DOCTOR_ID,
               D.DOCTOR_NAME,
               A.REASON_FOR_VISIT,
               C.CONSULTATION_ID,
               C.CONSULTATION_DATE,
               C.SYMPTOMS,
               C.DIAGNOSIS,
               C.PRESCRIPTION,
               C.FOLLOW_UP_DATE,
               C.DOCTOR_NOTES,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(A.APPOINTMENT_ID) = :appointment_id
        {doctor_filter}
        """,
        params,
    )
    return cursor.fetchone()


def fetch_appointment_for_today_token(cursor, doctor_id, token_no):
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.APPOINTMENT_DATE,
               A.APPOINTMENT_TIME,
               A.TOKEN_NO,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               A.DOCTOR_ID,
               D.DOCTOR_NAME,
               A.REASON_FOR_VISIT,
               C.CONSULTATION_ID,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(A.DOCTOR_ID) = :doctor_id
          AND TRUNC(A.APPOINTMENT_DATE) = TRUNC(SYSDATE)
          AND A.TOKEN_NO = :token_no
          AND UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
        """,
        {"doctor_id": doctor_id.upper(), "token_no": token_no},
    )
    return cursor.fetchone()


def fetch_appointment_for_doctor(cursor, doctor_id, appointment_id):
    cursor.execute(
        """
        SELECT A.APPOINTMENT_ID,
               A.APPOINTMENT_DATE,
               A.APPOINTMENT_TIME,
               A.TOKEN_NO,
               A.PATIENT_ID,
               P.PATIENT_NAME,
               A.DOCTOR_ID,
               D.DOCTOR_NAME,
               A.REASON_FOR_VISIT,
               C.CONSULTATION_ID,
               NVL(C.CONSULTATION_STATUS, 'Pending') AS CONSULTATION_STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        LEFT JOIN CONSULTATION C ON A.APPOINTMENT_ID = C.APPOINTMENT_ID
        WHERE UPPER(A.DOCTOR_ID) = :doctor_id
          AND UPPER(A.APPOINTMENT_ID) = :appointment_id
          AND UPPER(NVL(A.STATUS, 'BOOKED')) <> 'CANCELLED'
        """,
        {"doctor_id": doctor_id.upper(), "appointment_id": appointment_id.upper()},
    )
    return cursor.fetchone()


def resolve_appointment_by_id_or_today_token(cursor, doctor_id, value):
    """Doctor entry only: accept Appointment ID or today's Token No."""
    value = value.strip().upper()

    if value.isdigit():
        return fetch_appointment_for_today_token(cursor, doctor_id, int(value))

    return fetch_appointment_for_doctor(cursor, doctor_id, value)


def get_existing_consultation_id(cursor, appointment_id):
    cursor.execute(
        """
        SELECT CONSULTATION_ID
        FROM CONSULTATION
        WHERE UPPER(APPOINTMENT_ID) = :appointment_id
        """,
        {"appointment_id": appointment_id.upper()},
    )
    row = cursor.fetchone()
    return row[0] if row else None


def update_appointment_status(cursor, appointment_id, consultation_status):
    """Keep appointment status in sync with consultation status."""
    new_status = "Completed" if consultation_status == "Completed" else "Booked"

    cursor.execute(
        """
        UPDATE APPOINTMENT
        SET STATUS = :new_status
        WHERE UPPER(APPOINTMENT_ID) = :appointment_id
          AND UPPER(NVL(STATUS, 'BOOKED')) <> 'CANCELLED'
        """,
        {"new_status": new_status, "appointment_id": appointment_id.upper()},
    )


# -----------------------------------------------------------------------------
# Create / update consultation helpers
# -----------------------------------------------------------------------------

def choose_consultation_status(default="Pending"):
    while True:
        print("\nConsultation Status")
        print("1. Pending")
        print("2. Completed")
        choice = input(f"Enter choice [default {default}]: ").strip()

        if not choice:
            return default
        if choice == "1":
            return "Pending"
        if choice == "2":
            return "Completed"
        if is_back(choice):
            return None

        print("Invalid status choice. Please select 1 or 2.")


def print_start_consultation_header(appointment):
    print("\nSTART CONSULTATION")
    print_line()
    print(f"Appointment ID : {clean(appointment[0])}")
    print(f"Date           : {format_date(appointment[1])}")
    print(f"Time           : {format_time(appointment[2])}")
    print(f"Token No       : {clean(appointment[3])}")
    print(f"Patient ID     : {clean(appointment[4])}")
    print(f"Patient Name   : {clean(appointment[5])}")
    print(f"Doctor ID      : {clean(appointment[6])}")
    print(f"Doctor Name    : {clean(appointment[7])}")
    print(f"Reason         : {clean(appointment[8])}")
    print(f"Current Status : {clean(appointment[10])}")
    print_line()


def save_consultation_form(conn, appointment):
    """Create or update consultation details for an appointment."""
    cursor = conn.cursor()

    appointment_id = appointment[0]
    token_no = appointment[3]
    existing_consultation_id = get_existing_consultation_id(cursor, appointment_id)

    print_start_consultation_header(appointment)

    if str(appointment[10]).upper() == "COMPLETED":
        print("This consultation is already completed. Use Update Consultation if you want to edit it.")
        return

    symptoms = input_required("Symptoms")
    if symptoms is None:
        print("Consultation cancelled.")
        return

    diagnosis = input_required("Diagnosis")
    if diagnosis is None:
        print("Consultation cancelled.")
        return

    prescription = input_optional("Prescription Optional")
    follow_up_date = input_date("Follow-up Date Optional", required=False)
    doctor_notes = input_optional("Doctor Notes Optional")
    status = choose_consultation_status(default="Completed")
    if status is None:
        print("Consultation cancelled.")
        return

    try:
        if existing_consultation_id:
            cursor.execute(
                """
                UPDATE CONSULTATION
                SET TOKEN_NO = :token_no,
                    SYMPTOMS = :symptoms,
                    DIAGNOSIS = :diagnosis,
                    PRESCRIPTION = :prescription,
                    FOLLOW_UP_DATE = :follow_up_date,
                    CONSULTATION_STATUS = :status,
                    DOCTOR_NOTES = :doctor_notes
                WHERE CONSULTATION_ID = :consultation_id
                """,
                {
                    "token_no": token_no,
                    "symptoms": symptoms,
                    "diagnosis": diagnosis,
                    "prescription": prescription,
                    "follow_up_date": follow_up_date,
                    "status": status,
                    "doctor_notes": doctor_notes,
                    "consultation_id": existing_consultation_id,
                },
            )
            consultation_id = existing_consultation_id
        else:
            consultation_id = get_next_id(cursor, "CONSULTATION", "CONSULTATION_ID", "C", 3)
            cursor.execute(
                """
                INSERT INTO CONSULTATION (
                    CONSULTATION_ID,
                    APPOINTMENT_ID,
                    TOKEN_NO,
                    CONSULTATION_DATE,
                    SYMPTOMS,
                    DIAGNOSIS,
                    PRESCRIPTION,
                    FOLLOW_UP_DATE,
                    CONSULTATION_STATUS,
                    DOCTOR_NOTES
                ) VALUES (
                    :consultation_id,
                    :appointment_id,
                    :token_no,
                    SYSDATE,
                    :symptoms,
                    :diagnosis,
                    :prescription,
                    :follow_up_date,
                    :status,
                    :doctor_notes
                )
                """,
                {
                    "consultation_id": consultation_id,
                    "appointment_id": appointment_id,
                    "token_no": token_no,
                    "symptoms": symptoms,
                    "diagnosis": diagnosis,
                    "prescription": prescription,
                    "follow_up_date": follow_up_date,
                    "status": status,
                    "doctor_notes": doctor_notes,
                },
            )

        update_appointment_status(cursor, appointment_id, status)
        conn.commit()
        print(f"Consultation saved successfully. Consultation ID: {consultation_id}")

    except Exception as exc:
        conn.rollback()
        print("Error while saving consultation:", exc)


def update_existing_consultation_fields(conn, appointment_id, doctor_id=None):
    """Update fields of an already started consultation."""
    cursor = conn.cursor()

    row = fetch_full_consultation_by_appointment(cursor, appointment_id, doctor_id)
    if not row:
        print("No matching appointment found.")
        return

    consultation_id = get_existing_consultation_id(cursor, appointment_id)
    if not consultation_id:
        print("Consultation is not started yet. No consultation details available to update.")
        return

    display_full_consultation(row)

    fields = {
        "1": ("SYMPTOMS", "Symptoms", "text"),
        "2": ("DIAGNOSIS", "Diagnosis", "text"),
        "3": ("PRESCRIPTION", "Prescription", "optional"),
        "4": ("FOLLOW_UP_DATE", "Follow-up Date", "date"),
        "5": ("DOCTOR_NOTES", "Doctor Notes", "optional"),
        "6": ("CONSULTATION_STATUS", "Consultation Status", "status"),
    }

    while True:
        print("\nWhich field do you want to update?")
        print("1. Symptoms")
        print("2. Diagnosis")
        print("3. Prescription")
        print("4. Follow-up Date")
        print("5. Doctor Notes")
        print("6. Consultation Status")
        print("7. Back")
        choice = input("Enter choice: ").strip()

        if choice == "7" or is_back(choice):
            break
        if choice not in fields:
            print("Invalid choice.")
            continue

        column, label, value_type = fields[choice]

        if value_type == "date":
            new_value = input_date(f"New {label}", required=False)
        elif value_type == "optional":
            new_value = input_optional(f"New {label} Optional")
        elif value_type == "status":
            new_value = choose_consultation_status(default="Pending")
        else:
            new_value = input_required(f"New {label}")

        if new_value is None and value_type in ("text", "status"):
            print("Update cancelled.")
            continue

        try:
            cursor.execute(
                f"""
                UPDATE CONSULTATION
                SET {column} = :new_value
                WHERE CONSULTATION_ID = :consultation_id
                """,
                {"new_value": new_value, "consultation_id": consultation_id},
            )

            if column == "CONSULTATION_STATUS":
                update_appointment_status(cursor, appointment_id, new_value)

            conn.commit()
            print(f"{label} updated successfully.")

        except Exception as exc:
            conn.rollback()
            print("Error while updating consultation:", exc)


# -----------------------------------------------------------------------------
# Patient Consultation History actions - no Doctor ID, no start consultation
# -----------------------------------------------------------------------------

def history_todays_consultations(conn):
    cursor = conn.cursor()
    rows = fetch_today_consultations_all(cursor)
    display_today_all_doctors(rows)
    pause()


def history_remaining_consultations(conn):
    cursor = conn.cursor()
    rows = fetch_remaining_consultations_all(cursor)
    display_remaining_all_doctors(rows)
    pause()


def history_completed_consultations(conn):
    cursor = conn.cursor()
    rows = fetch_completed_consultations_all(cursor)
    display_completed_all_doctors(rows)
    pause()


def history_view_by_appointment_id(conn):
    cursor = conn.cursor()
    appointment_id = input("\nEnter Appointment ID or type 'back': ").strip().upper()
    if is_back(appointment_id):
        return

    row = fetch_full_consultation_by_appointment(cursor, appointment_id)
    display_full_consultation(row)
    pause()


def history_update_consultation(conn):
    print("\nUPDATE CONSULTATION")
    print_line()
    appointment_id = input("Enter Appointment ID or type 'back': ").strip().upper()
    if is_back(appointment_id):
        return

    update_existing_consultation_fields(conn, appointment_id)
    pause()


def patient_consultation_history_menu(conn):
    """All records view/update. No Doctor ID. No start consultation."""
    while True:
        print("\nPATIENT CONSULTATION HISTORY")
        print_line()
        print("1. Today's Consultations")
        print("2. Remaining Consultations")
        print("3. Completed Consultations")
        print("4. View Consultation by Appointment ID")
        print("5. Update Consultation")
        print("6. Back")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            history_todays_consultations(conn)
        elif choice == "2":
            history_remaining_consultations(conn)
        elif choice == "3":
            history_completed_consultations(conn)
        elif choice == "4":
            history_view_by_appointment_id(conn)
        elif choice == "5":
            history_update_consultation(conn)
        elif choice == "6" or is_back(choice):
            break
        else:
            print("Invalid choice.")
            pause()


# -----------------------------------------------------------------------------
# Doctor Entry actions - doctor-wise with start/continue consultation
# -----------------------------------------------------------------------------

def doctor_todays_consultations(conn, doctor):
    cursor = conn.cursor()
    doctor_id = doctor[0]

    while True:
        rows = fetch_today_consultations_for_doctor(cursor, doctor_id)
        display_today_for_doctor(rows)

        if not rows:
            print("\n1. Back")
            choice = input("Enter choice: ").strip()
            if choice == "1" or is_back(choice):
                break
            print("Invalid choice.")
            pause()
            continue

        print("\n1. Start Consultation")
        print("2. Back")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            token_no = input("Enter Token No or type 'back': ").strip()
            if is_back(token_no):
                continue
            if not token_no.isdigit():
                print("Invalid Token No. Please enter a valid number.")
                pause()
                continue

            appointment = fetch_appointment_for_today_token(cursor, doctor_id, int(token_no))
            if not appointment:
                print("No appointment found for this token number today.")
                pause()
                continue

            save_consultation_form(conn, appointment)
            pause()

        elif choice == "2" or is_back(choice):
            break
        else:
            print("Invalid choice.")
            pause()


def doctor_remaining_consultations(conn, doctor):
    cursor = conn.cursor()
    doctor_id = doctor[0]

    while True:
        rows = fetch_remaining_consultations_for_doctor(cursor, doctor_id)
        display_remaining_for_doctor(rows)

        if not rows:
            print("\n1. Back")
            choice = input("Enter choice: ").strip()
            if choice == "1" or is_back(choice):
                break
            print("Invalid choice.")
            pause()
            continue

        print("\n1. Start / Continue Consultation")
        print("2. Back")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            value = input("Enter Appointment ID / today's Token No or type 'back': ").strip()
            if is_back(value):
                continue

            appointment = resolve_appointment_by_id_or_today_token(cursor, doctor_id, value)
            if not appointment:
                print("No matching appointment found for this doctor.")
                pause()
                continue

            save_consultation_form(conn, appointment)
            pause()

        elif choice == "2" or is_back(choice):
            break
        else:
            print("Invalid choice.")
            pause()


def doctor_completed_consultations(conn, doctor):
    cursor = conn.cursor()
    rows = fetch_completed_consultations_for_doctor(cursor, doctor[0])
    display_completed_for_doctor(rows)
    pause()


def doctor_view_by_appointment_id(conn, doctor):
    cursor = conn.cursor()
    appointment_id = input("\nEnter Appointment ID or type 'back': ").strip().upper()
    if is_back(appointment_id):
        return

    row = fetch_full_consultation_by_appointment(cursor, appointment_id, doctor[0])
    display_full_consultation(row)
    pause()


def doctor_update_consultation(conn, doctor):
    cursor = conn.cursor()
    doctor_id = doctor[0]

    print("\nUPDATE CONSULTATION")
    print_line()
    value = input("Enter Appointment ID / today's Token No or type 'back': ").strip()
    if is_back(value):
        return

    appointment = resolve_appointment_by_id_or_today_token(cursor, doctor_id, value)
    if not appointment:
        print("No matching appointment found for this doctor.")
        return

    update_existing_consultation_fields(conn, appointment[0], doctor_id)


def doctor_consultation_dashboard(conn, doctor):
    while True:
        print_doctor_header(doctor)
        print("\n1. Today's Consultations")
        print("2. Remaining Consultations")
        print("3. Completed Consultations")
        print("4. View Consultation by Appointment ID")
        print("5. Update Consultation")
        print("6. Back")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            doctor_todays_consultations(conn, doctor)
        elif choice == "2":
            doctor_remaining_consultations(conn, doctor)
        elif choice == "3":
            doctor_completed_consultations(conn, doctor)
        elif choice == "4":
            doctor_view_by_appointment_id(conn, doctor)
        elif choice == "5":
            doctor_update_consultation(conn, doctor)
            pause()
        elif choice == "6" or is_back(choice):
            break
        else:
            print("Invalid choice.")
            pause()


def doctor_entry(conn):
    cursor = conn.cursor()
    doctor = choose_doctor_id(cursor)
    if not doctor:
        return
    doctor_consultation_dashboard(conn, doctor)


# -----------------------------------------------------------------------------
# Main consultation management menu
# -----------------------------------------------------------------------------

def consultation_management_menu(conn):
    """Entry point called from main.py."""
    while True:
        print("\nCONSULTATION MANAGEMENT")
        print_line()
        print("1. Patient Consultation History")
        print("2. Doctor Entry")
        print("3. Back to Main Menu")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            patient_consultation_history_menu(conn)
        elif choice == "2":
            doctor_entry(conn)
        elif choice == "3" or is_back(choice):
            break
        else:
            print("Invalid choice.")
            pause()

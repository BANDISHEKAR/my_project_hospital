"""Appointment Management module using DOCTOR_AVAILABILITY.

Final requirements covered:
- Book appointment first asks Patient ID / Mobile Number.
- Before asking patient, only shows Patient ID range like P001 to P010.
- Appointment search options:
  1. Earliest appointment - Any date / Any time
  2. Search by Specialization
  3. Search by Particular Date
  4. Search by Any Date + Particular Time
  5. Search by Particular Date + Particular Time
- Supports 'back' from important input places.
- Shows only Active doctors and Active doctor availability while booking.
- Stores APPOINTMENT_TIME as HH24:MI, for example 09:00, to avoid VARCHAR2(5) errors.
- Displays appointment times in 12-hour AM/PM format.
"""

from datetime import date, datetime, timedelta

from utils.id_generator import get_next_id
from utils.input_helper import (
    print_line,
    pause,
    input_required,
    input_date,
    input_12hr_time,
    is_back,
)
from utils.time_helper import get_day_name


SEARCH_DAYS = 60
PAGE_SIZE = 5


# ============================================================
# TIME HELPERS
# ============================================================

def _parse_12hr_datetime(value):
    """Parse 12-hour time like 09:00 AM."""
    return datetime.strptime(value.strip().upper(), "%I:%M %p")


def _parse_hh24_datetime(value):
    """Parse 24-hour time like 09:00."""
    return datetime.strptime(value.strip(), "%H:%M")


def _time_to_minutes_from_12hr(value):
    dt = _parse_12hr_datetime(value)
    return dt.hour * 60 + dt.minute


def _time_to_minutes_from_hh24(value):
    dt = _parse_hh24_datetime(value)
    return dt.hour * 60 + dt.minute


def _format_hh24_from_minutes(minutes):
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _format_12hr_from_hh24(value):
    """Display HH24:MI as 12-hour AM/PM. Also handles already AM/PM values."""
    if value is None:
        return "-"

    value = str(value).strip()
    if not value:
        return "-"

    try:
        if "AM" in value.upper() or "PM" in value.upper():
            return _parse_12hr_datetime(value).strftime("%I:%M %p")
        return _parse_hh24_datetime(value).strftime("%I:%M %p")
    except ValueError:
        return value


def _generate_token_times(start_time, end_time, max_patients):
    """Return token -> HH24:MI appointment time for one availability session."""
    start_minutes = _time_to_minutes_from_12hr(start_time)
    end_minutes = _time_to_minutes_from_12hr(end_time)

    if end_minutes <= start_minutes:
        end_minutes += 24 * 60

    total_minutes = end_minutes - start_minutes
    interval = max(1, total_minutes // int(max_patients))

    token_times = {}
    for token_no in range(1, int(max_patients) + 1):
        token_minutes = start_minutes + ((token_no - 1) * interval)
        token_times[token_no] = _format_hh24_from_minutes(token_minutes)

    return token_times


def _is_time_inside_session(preferred_time_12hr, start_time, end_time):
    preferred = _time_to_minutes_from_12hr(preferred_time_12hr)
    start = _time_to_minutes_from_12hr(start_time)
    end = _time_to_minutes_from_12hr(end_time)

    if end <= start:
        end += 24 * 60
        if preferred < start:
            preferred += 24 * 60

    return start <= preferred < end


def _time_order_sql(alias="A"):
    """Oracle ORDER BY expression that supports HH24:MI and HH:MI AM values."""
    return f"""
        CASE
            WHEN REGEXP_LIKE({alias}.APPOINTMENT_TIME, '^[0-9]{{2}}:[0-9]{{2}}$')
            THEN TO_DATE({alias}.APPOINTMENT_TIME, 'HH24:MI')
            ELSE TO_DATE({alias}.APPOINTMENT_TIME, 'HH:MI AM')
        END
    """


# ============================================================
# PATIENT SELECTION FOR BOOKING
# ============================================================

def show_patient_id_range(cursor):
    cursor.execute("""
        SELECT PATIENT_ID
        FROM PATIENT_MASTER
        ORDER BY TO_NUMBER(REGEXP_SUBSTR(PATIENT_ID, '[0-9]+')), PATIENT_ID
    """)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo patients found. Please add patient first.")
        return False

    first_id = rows[0][0]
    last_id = rows[-1][0]
    total = len(rows)

    print(f"\nAvailable Patient IDs: {first_id} to {last_id}")
    print(f"Total Patients       : {total}")
    return True


def display_selected_patient(row):
    if not row:
        return

    print("\nSELECTED PATIENT DETAILS")
    print_line()
    print(f"Patient ID   : {row[0]}")
    print(f"Patient Name : {row[1]}")
    print(f"Age          : {row[2] if row[2] is not None else '-'}")
    print(f"Gender       : {row[3] if row[3] else '-'}")
    print(f"Phone        : {row[4]}")
    print(f"Email        : {row[5] if row[5] else '-'}")
    print(f"City         : {row[7] if row[7] else '-'}")
    print(f"Blood Group  : {row[8] if row[8] else '-'}")
    print_line()


def choose_patient_id_or_mobile(cursor):
    if not show_patient_id_range(cursor):
        return None

    while True:
        value = input("\nEnter Patient ID / Mobile Number or type 'back': ").strip()

        if is_back(value):
            return None

        if not value:
            print("Please enter Patient ID or Mobile Number.")
            continue

        value_upper = value.upper()

        cursor.execute("""
            SELECT PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL,
                   ADDRESS, CITY, BLOOD_GROUP, REGISTRATION_DATE
            FROM PATIENT_MASTER
            WHERE UPPER(PATIENT_ID) = :value_upper
               OR PHONE = :value
        """, {"value_upper": value_upper, "value": value})

        patient = cursor.fetchone()

        if patient:
            display_selected_patient(patient)
            return patient[0]

        print("Patient not found. Enter valid Patient ID / Mobile Number or type 'back'.")


# ============================================================
# APPOINTMENT DISPLAY / SELECTION
# ============================================================

def display_appointments(rows):
    if not rows:
        print("\nNo appointment records found.")
        return

    print("\nAPPOINTMENT DETAILS")
    print_line(135)
    print(
        f"{'Appt ID':<9}{'Date':<12}{'Time':<10}{'Token':<7}"
        f"{'Patient':<22}{'Doctor':<22}{'Spec':<16}{'Room':<9}"
        f"{'Session':<10}{'Reason':<25}{'Status':<10}"
    )
    print_line(135)

    for r in rows:
        date_value = r[1].strftime('%Y-%m-%d') if r[1] else '-'
        time_value = _format_12hr_from_hh24(r[2])
        print(
            f"{r[0]:<9}{date_value:<12}{time_value:<10}{str(r[3]):<7}"
            f"{str(r[4]):<22}{str(r[5]):<22}{str(r[6]):<16}{str(r[7]):<9}"
            f"{str(r[8]):<10}{str(r[9] or '-'):<25}{str(r[10]):<10}"
        )

    print_line(135)


def choose_appointment_id(cursor, status_filter=None, without_consultation=False, without_bill=False):
    sql = f"""
        SELECT A.APPOINTMENT_ID, A.APPOINTMENT_DATE, A.APPOINTMENT_TIME, A.TOKEN_NO,
               P.PATIENT_NAME, D.DOCTOR_NAME, D.SPECIALIZATION, DA.ROOM_NO, DA.SESSION_TYPE,
               A.REASON_FOR_VISIT, A.STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        JOIN DOCTOR_AVAILABILITY DA ON A.AVAILABILITY_ID = DA.AVAILABILITY_ID
        WHERE 1 = 1
    """
    params = {}

    if status_filter:
        sql += " AND A.STATUS = :status_filter"
        params["status_filter"] = status_filter

    if without_consultation:
        sql += " AND NOT EXISTS (SELECT 1 FROM CONSULTATION C WHERE C.APPOINTMENT_ID = A.APPOINTMENT_ID)"

    if without_bill:
        sql += " AND NOT EXISTS (SELECT 1 FROM BILLING B WHERE B.APPOINTMENT_ID = A.APPOINTMENT_ID)"

    sql += f" ORDER BY A.APPOINTMENT_DATE, {_time_order_sql('A')}, A.APPOINTMENT_ID"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    display_appointments(rows)

    if not rows:
        return None

    valid = {r[0].upper() for r in rows}

    while True:
        appointment_id = input("Enter Appointment ID or type 'back': ").strip().upper()
        if is_back(appointment_id):
            return None
        if appointment_id in valid:
            return appointment_id
        print("Invalid Appointment ID. Select from the list.")


# ============================================================
# SLOT SEARCH LOGIC
# ============================================================

def _get_used_tokens(cursor, availability_id, appointment_date):
    cursor.execute("""
        SELECT TOKEN_NO
        FROM APPOINTMENT
        WHERE AVAILABILITY_ID = :availability_id
        AND APPOINTMENT_DATE = :appointment_date
    """, {"availability_id": availability_id, "appointment_date": appointment_date})

    return {int(r[0]) for r in cursor.fetchall() if r[0] is not None}


def _get_active_availability(cursor, day_name, specialization=None):
    sql = """
        SELECT DA.AVAILABILITY_ID, DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO,
               DA.START_TIME, DA.END_TIME, DA.DOCTOR_ID, DM.DOCTOR_NAME,
               DA.SPECIALIZATION, DA.MAX_PATIENTS
        FROM DOCTOR_AVAILABILITY DA
        JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        WHERE DA.DAY_NAME = :day_name
          AND DA.STATUS = 'Active'
          AND DM.STATUS = 'Active'
    """
    params = {"day_name": day_name}

    if specialization:
        sql += " AND UPPER(DA.SPECIALIZATION) LIKE UPPER(:specialization)"
        params["specialization"] = f"%{specialization}%"

    sql += """
        ORDER BY TO_DATE(DA.START_TIME, 'HH:MI AM'), DA.ROOM_NO, DA.AVAILABILITY_ID
    """

    cursor.execute(sql, params)
    return cursor.fetchall()


def _build_slot_from_availability(cursor, av, appointment_date, preferred_time=None):
    """Return one available slot for an availability row, or None if full/not matching."""
    availability_id = av[0]
    day_name = av[1]
    session_type = av[2]
    room_no = av[3]
    start_time = av[4]
    end_time = av[5]
    doctor_id = av[6]
    doctor_name = av[7]
    specialization = av[8]
    max_patients = int(av[9])

    if preferred_time and not _is_time_inside_session(preferred_time, start_time, end_time):
        return None

    used_tokens = _get_used_tokens(cursor, availability_id, appointment_date)

    if len(used_tokens) >= max_patients:
        return None

    token_times = _generate_token_times(start_time, end_time, max_patients)

    preferred_minutes = None
    if preferred_time:
        preferred_minutes = _time_to_minutes_from_12hr(preferred_time)

    for token_no in range(1, max_patients + 1):
        if token_no in used_tokens:
            continue

        time_24 = token_times[token_no]

        if preferred_minutes is not None:
            token_minutes = _time_to_minutes_from_hh24(time_24)
            session_start_minutes = _time_to_minutes_from_12hr(start_time)

            # Handle midnight-crossing sessions safely.
            if token_minutes < session_start_minutes:
                token_minutes += 24 * 60
            if preferred_minutes < session_start_minutes:
                preferred_minutes += 24 * 60

            if token_minutes < preferred_minutes:
                continue

        return {
            "date": appointment_date,
            "day": day_name,
            "time_24": time_24,
            "time_12": _format_12hr_from_hh24(time_24),
            "token_no": token_no,
            "availability_id": availability_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "specialization": specialization,
            "room_no": room_no,
            "session_type": session_type,
            "start_time": start_time,
            "end_time": end_time,
            "max_patients": max_patients,
        }

    return None


def search_available_slots(cursor, start_date=None, end_date=None, specialization=None, preferred_time=None):
    """Search available slots from start_date to end_date inclusive."""
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=SEARCH_DAYS - 1)

    slots = []
    current_date = start_date

    while current_date <= end_date:
        day_name = get_day_name(current_date)
        availability_rows = _get_active_availability(cursor, day_name, specialization=specialization)

        for av in availability_rows:
            slot = _build_slot_from_availability(
                cursor,
                av,
                current_date,
                preferred_time=preferred_time,
            )
            if slot:
                slots.append(slot)

        current_date += timedelta(days=1)

    slots.sort(key=lambda s: (s["date"], _time_to_minutes_from_hh24(s["time_24"]), s["room_no"], s["availability_id"]))
    return slots


def display_available_slots(slots, title="AVAILABLE APPOINTMENTS"):
    if not slots:
        print("\nNo available appointment slots found.")
        return

    print(f"\n{title}")
    print_line(135)
    print(
        f"{'No':<4}{'Date':<12}{'Day':<6}{'Time':<10}{'Token':<7}"
        f"{'Doctor Name':<22}{'Specialization':<18}{'Room':<9}{'Session':<10}{'AV ID':<8}"
    )
    print_line(135)

    for idx, slot in enumerate(slots, start=1):
        print(
            f"{idx:<4}{slot['date'].strftime('%Y-%m-%d'):<12}{slot['day']:<6}"
            f"{slot['time_12']:<10}{str(slot['token_no']):<7}"
            f"{slot['doctor_name']:<22}{slot['specialization']:<18}{slot['room_no']:<9}"
            f"{slot['session_type']:<10}{slot['availability_id']:<8}"
        )

    print_line(135)


def choose_slot_from_list(slots, title="AVAILABLE APPOINTMENTS", allow_next=True):
    if not slots:
        print("\nNo available appointment slots found.")
        return None

    page_start = 0

    while True:
        page_slots = slots[page_start:page_start + PAGE_SIZE]
        display_available_slots(page_slots, title)

        print("\nEnter option number to book")
        if allow_next and page_start + PAGE_SIZE < len(slots):
            print("n. Next available appointments")
        print("back. Back to search options")

        choice = input("Enter choice: ").strip().lower()

        if is_back(choice):
            return None

        if choice in {"n", "next"} and allow_next:
            if page_start + PAGE_SIZE < len(slots):
                page_start += PAGE_SIZE
            else:
                print("No more available appointments.")
            continue

        try:
            selected_index = int(choice)
        except ValueError:
            print("Invalid choice.")
            continue

        if 1 <= selected_index <= len(page_slots):
            return page_slots[selected_index - 1]

        print("Invalid option number. Select from displayed list.")


# ============================================================
# BOOKING
# ============================================================

def _recheck_slot_available(cursor, slot):
    cursor.execute("""
        SELECT COUNT(*)
        FROM DOCTOR_AVAILABILITY DA
        JOIN DOCTOR_MASTER DM ON DA.DOCTOR_ID = DM.DOCTOR_ID
        WHERE DA.AVAILABILITY_ID = :availability_id
          AND DA.STATUS = 'Active'
          AND DM.STATUS = 'Active'
    """, {"availability_id": slot["availability_id"]})

    if cursor.fetchone()[0] == 0:
        print("\nSelected doctor availability is not active now.")
        return False

    cursor.execute("""
        SELECT COUNT(*)
        FROM APPOINTMENT
        WHERE AVAILABILITY_ID = :availability_id
          AND APPOINTMENT_DATE = :appointment_date
          AND TOKEN_NO = :token_no
    """, {
        "availability_id": slot["availability_id"],
        "appointment_date": slot["date"],
        "token_no": slot["token_no"],
    })

    if cursor.fetchone()[0] > 0:
        print("\nThis token was already booked. Please select another slot.")
        return False

    return True


def book_selected_slot(conn, patient_id, slot):
    cursor = conn.cursor()

    if not _recheck_slot_available(cursor, slot):
        return

    reason = input_required("Reason for Visit")
    if reason is None:
        print("Booking cancelled.")
        return

    appointment_id = get_next_id(cursor, "APPOINTMENT", "APPOINTMENT_ID", "A", 3)

    try:
        cursor.execute("""
            INSERT INTO APPOINTMENT (
                APPOINTMENT_ID, PATIENT_ID, DOCTOR_ID, AVAILABILITY_ID, APPOINTMENT_DATE,
                APPOINTMENT_TIME, TOKEN_NO, BOOKING_DATE, REASON_FOR_VISIT, STATUS
            ) VALUES (
                :appointment_id, :patient_id, :doctor_id, :availability_id, :appointment_date,
                :appointment_time, :token_no, SYSDATE, :reason, 'Booked'
            )
        """, {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": slot["doctor_id"],
            "availability_id": slot["availability_id"],
            "appointment_date": slot["date"],
            "appointment_time": slot["time_24"],  # Stored as HH24:MI to support VARCHAR2(5)
            "token_no": slot["token_no"],
            "reason": reason,
        })

        conn.commit()

        print("\nAppointment booked successfully.")
        print_line()
        print(f"Appointment ID   : {appointment_id}")
        print(f"Patient ID       : {patient_id}")
        print(f"Doctor           : {slot['doctor_name']}")
        print(f"Specialization   : {slot['specialization']}")
        print(f"Date             : {slot['date'].strftime('%Y-%m-%d')}")
        print(f"Time             : {slot['time_12']}")
        print(f"Token No         : {slot['token_no']}")
        print(f"Room             : {slot['room_no']}")
        print(f"Session          : {slot['session_type']}")
        print(f"Status           : Booked")
        print_line()

    except Exception as exc:
        conn.rollback()
        print("\nError while booking appointment:", exc)


def input_specialization_from_active_doctors(cursor):
    cursor.execute("""
        SELECT DISTINCT SPECIALIZATION
        FROM DOCTOR_MASTER
        WHERE STATUS = 'Active'
        ORDER BY SPECIALIZATION
    """)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo active doctor specializations found.")
        return None

    print("\nAvailable Specializations")
    print_line()
    for idx, row in enumerate(rows, start=1):
        print(f"{idx}. {row[0]}")
    print("back. Back")
    print_line()

    while True:
        choice = input("Enter specialization option/name: ").strip()
        if is_back(choice):
            return None

        try:
            index = int(choice)
            if 1 <= index <= len(rows):
                return rows[index - 1][0]
        except ValueError:
            pass

        if choice:
            return choice

        print("Enter valid specialization or type 'back'.")


def book_appointment_search_menu(conn, patient_id):
    cursor = conn.cursor()

    while True:
        print("\nBOOK APPOINTMENT SEARCH OPTIONS")
        print_line()
        print("1. Earliest appointment - Any date / Any time")
        print("2. Search by Specialization")
        print("3. Search by Particular Date")
        print("4. Search by Any Date + Particular Time")
        print("5. Search by Particular Date + Particular Time")
        print("6. Back to Appointment Management")

        choice = input("Enter choice: ").strip()

        if is_back(choice) or choice == "6":
            break

        selected_slot = None

        if choice == "1":
            slots = search_available_slots(cursor)
            selected_slot = choose_slot_from_list(slots, "EARLIEST AVAILABLE APPOINTMENTS")

        elif choice == "2":
            specialization = input_specialization_from_active_doctors(cursor)
            if specialization is None:
                continue
            slots = search_available_slots(cursor, specialization=specialization)
            selected_slot = choose_slot_from_list(
                slots,
                f"AVAILABLE APPOINTMENTS FOR SPECIALIZATION: {specialization.upper()}",
            )

        elif choice == "3":
            appointment_date = input_date("Appointment Date")
            if appointment_date is None:
                continue
            day_name = get_day_name(appointment_date)
            print(f"Selected date day: {day_name}")
            slots = search_available_slots(cursor, start_date=appointment_date, end_date=appointment_date)
            selected_slot = choose_slot_from_list(
                slots,
                f"AVAILABLE APPOINTMENTS ON {appointment_date.strftime('%Y-%m-%d')}",
                allow_next=False,
            )

        elif choice == "4":
            preferred_time = input_12hr_time("Preferred Time")
            if preferred_time is None:
                continue
            slots = search_available_slots(cursor, preferred_time=preferred_time)
            selected_slot = choose_slot_from_list(
                slots,
                f"AVAILABLE APPOINTMENTS FOR {preferred_time}",
            )

        elif choice == "5":
            appointment_date = input_date("Appointment Date")
            if appointment_date is None:
                continue
            preferred_time = input_12hr_time("Preferred Time")
            if preferred_time is None:
                continue
            day_name = get_day_name(appointment_date)
            print(f"Selected date day: {day_name}")
            slots = search_available_slots(
                cursor,
                start_date=appointment_date,
                end_date=appointment_date,
                preferred_time=preferred_time,
            )
            selected_slot = choose_slot_from_list(
                slots,
                f"AVAILABLE APPOINTMENTS ON {appointment_date.strftime('%Y-%m-%d')} FOR {preferred_time}",
                allow_next=False,
            )

        else:
            print("Invalid choice.")
            continue

        if selected_slot is not None:
            book_selected_slot(conn, patient_id, selected_slot)
            break


def add_appointment(conn):
    cursor = conn.cursor()

    print("\nBOOK APPOINTMENT")
    print_line()
    print("Type 'back' anytime to cancel.")

    patient_id = choose_patient_id_or_mobile(cursor)
    if not patient_id:
        return

    book_appointment_search_menu(conn, patient_id)


# ============================================================
# VIEW / UPDATE / CANCEL
# ============================================================

def view_appointments(conn):
    cursor = conn.cursor()

    while True:
        print("\nVIEW APPOINTMENTS")
        print_line()
        print("1. View All")
        print("2. View by Date")
        print("3. View by Patient ID / Mobile Number")
        print("4. View by Doctor ID")
        print("5. View by Specialization")
        print("6. View by Date + Time")
        print("7. View by Status")
        print("8. Back")

        choice = input("Enter choice: ").strip()

        base = """
            SELECT A.APPOINTMENT_ID, A.APPOINTMENT_DATE, A.APPOINTMENT_TIME, A.TOKEN_NO,
                   P.PATIENT_NAME, D.DOCTOR_NAME, D.SPECIALIZATION, DA.ROOM_NO, DA.SESSION_TYPE,
                   A.REASON_FOR_VISIT, A.STATUS
            FROM APPOINTMENT A
            JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
            JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
            JOIN DOCTOR_AVAILABILITY DA ON A.AVAILABILITY_ID = DA.AVAILABILITY_ID
        """
        order = f" ORDER BY A.APPOINTMENT_DATE, {_time_order_sql('A')}, A.APPOINTMENT_ID"

        if choice == "1":
            cursor.execute(base + order)

        elif choice == "2":
            date_value = input_date("Appointment Date")
            if date_value is None:
                continue
            cursor.execute(base + " WHERE A.APPOINTMENT_DATE = :date_value " + order, {"date_value": date_value})

        elif choice == "3":
            patient_id = choose_patient_id_or_mobile(cursor)
            if patient_id is None:
                continue
            cursor.execute(base + " WHERE A.PATIENT_ID = :patient_id " + order, {"patient_id": patient_id})

        elif choice == "4":
            doctor_id = input_required("Doctor ID")
            if doctor_id is None:
                continue
            cursor.execute(base + " WHERE UPPER(A.DOCTOR_ID) = UPPER(:doctor_id) " + order, {"doctor_id": doctor_id})

        elif choice == "5":
            specialization = input_required("Specialization")
            if specialization is None:
                continue
            cursor.execute(
                base + " WHERE UPPER(D.SPECIALIZATION) LIKE UPPER(:specialization) " + order,
                {"specialization": f"%{specialization}%"},
            )

        elif choice == "6":
            date_value = input_date("Appointment Date")
            if date_value is None:
                continue
            time_value = input_12hr_time("Appointment Time")
            if time_value is None:
                continue
            time_24 = _parse_12hr_datetime(time_value).strftime("%H:%M")
            cursor.execute(
                base + """
                WHERE A.APPOINTMENT_DATE = :date_value
                AND (
                    A.APPOINTMENT_TIME = :time_24
                    OR A.APPOINTMENT_TIME = :time_12
                )
                """ + order,
                {"date_value": date_value, "time_24": time_24, "time_12": time_value},
            )

        elif choice == "7":
            print("\nStatus")
            print("1. Booked")
            print("2. Completed")
            print("3. Cancelled")
            print("back. Back")
            status_choice = input("Enter choice: ").strip()
            if is_back(status_choice):
                continue
            status = {"1": "Booked", "2": "Completed", "3": "Cancelled"}.get(status_choice)
            if not status:
                print("Invalid choice.")
                continue
            cursor.execute(base + " WHERE A.STATUS = :status " + order, {"status": status})

        elif choice == "8" or is_back(choice):
            break

        else:
            print("Invalid choice.")
            continue

        display_appointments(cursor.fetchall())
        pause()


def update_appointment(conn):
    cursor = conn.cursor()

    print("\nUPDATE APPOINTMENT")
    print_line()

    appointment_id = choose_appointment_id(cursor)
    if not appointment_id:
        return

    while True:
        print("\nWhich field do you want to update?")
        print("1. Reason for Visit")
        print("2. Status")
        print("3. Back")

        choice = input("Enter choice: ").strip()

        if choice == "3" or is_back(choice):
            break

        if choice == "1":
            value = input_required("New Reason for Visit")
            column = "REASON_FOR_VISIT"

        elif choice == "2":
            print("\nStatus")
            print("1. Booked")
            print("2. Completed")
            print("3. Cancelled")
            print("back. Back")
            status_choice = input("Enter choice: ").strip()
            if is_back(status_choice):
                continue
            status = {"1": "Booked", "2": "Completed", "3": "Cancelled"}.get(status_choice)
            if not status:
                print("Invalid choice.")
                continue
            value = status
            column = "STATUS"

        else:
            print("Invalid choice.")
            continue

        if value is None:
            print("Update cancelled.")
            continue

        try:
            cursor.execute(
                f"UPDATE APPOINTMENT SET {column} = :value WHERE APPOINTMENT_ID = :appointment_id",
                {"value": value, "appointment_id": appointment_id},
            )
            conn.commit()
            print("Appointment updated successfully.")

        except Exception as exc:
            conn.rollback()
            print("Error while updating appointment:", exc)


def cancel_appointment(conn):
    cursor = conn.cursor()

    print("\nCANCEL APPOINTMENT")
    print_line()

    appointment_id = choose_appointment_id(cursor, status_filter="Booked")
    if not appointment_id:
        return

    confirm = input("Are you sure you want to cancel this appointment? (yes/no): ").strip().lower()

    if confirm == "yes":
        try:
            cursor.execute(
                "UPDATE APPOINTMENT SET STATUS = 'Cancelled' WHERE APPOINTMENT_ID = :appointment_id",
                {"appointment_id": appointment_id},
            )
            conn.commit()
            print("Appointment cancelled successfully.")

        except Exception as exc:
            conn.rollback()
            print("Error:", exc)
    else:
        print("Cancel operation stopped.")


# ============================================================
# MENU
# ============================================================

def appointment_management_menu(conn):
    while True:
        print("\nAPPOINTMENT MANAGEMENT")
        print_line()
        print("1. Book Appointment")
        print("2. View Appointments")
        print("3. Update Appointment")
        print("4. Cancel Appointment")
        print("5. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_appointment(conn)
            pause()
        elif choice == "2":
            view_appointments(conn)
        elif choice == "3":
            update_appointment(conn)
            pause()
        elif choice == "4":
            cancel_appointment(conn)
            pause()
        elif choice == "5" or is_back(choice):
            break
        else:
            print("Invalid choice.")

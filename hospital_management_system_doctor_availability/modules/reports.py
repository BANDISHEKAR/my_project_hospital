"""Reports module."""

from utils.input_helper import print_line, pause, input_date


def doctor_appointment_count(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT D.DOCTOR_ID, D.DOCTOR_NAME, D.SPECIALIZATION, COUNT(A.APPOINTMENT_ID) AS TOTAL_APPOINTMENTS
        FROM DOCTOR_MASTER D
        LEFT JOIN APPOINTMENT A ON D.DOCTOR_ID = A.DOCTOR_ID
        GROUP BY D.DOCTOR_ID, D.DOCTOR_NAME, D.SPECIALIZATION
        ORDER BY D.DOCTOR_ID
    """)
    rows = cursor.fetchall()
    print("\nDOCTOR-WISE APPOINTMENT COUNT")
    print_line()
    print(f"{'Doctor ID':<12}{'Doctor Name':<24}{'Specialization':<18}{'Total Appointments':<20}")
    print_line()
    for r in rows:
        print(f"{r[0]:<12}{r[1]:<24}{r[2]:<18}{r[3]:<20}")


def city_wise_patient_count(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT NVL(CITY, 'Not Provided') AS CITY, COUNT(*) AS TOTAL_PATIENTS
        FROM PATIENT_MASTER
        GROUP BY NVL(CITY, 'Not Provided')
        ORDER BY TOTAL_PATIENTS DESC, CITY
    """)
    rows = cursor.fetchall()
    print("\nCITY-WISE PATIENT COUNT")
    print_line()
    print(f"{'City':<25}{'Total Patients':<15}")
    print_line()
    for r in rows:
        print(f"{r[0]:<25}{r[1]:<15}")


def revenue_doctor_wise(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT D.DOCTOR_ID, D.DOCTOR_NAME, D.SPECIALIZATION,
               COUNT(B.BILL_ID) AS BILL_COUNT,
               NVL(SUM(B.FINAL_AMOUNT), 0) AS TOTAL_REVENUE
        FROM DOCTOR_MASTER D
        LEFT JOIN APPOINTMENT A ON D.DOCTOR_ID = A.DOCTOR_ID
        LEFT JOIN BILLING B ON A.APPOINTMENT_ID = B.APPOINTMENT_ID
        GROUP BY D.DOCTOR_ID, D.DOCTOR_NAME, D.SPECIALIZATION
        ORDER BY D.DOCTOR_ID
    """)
    rows = cursor.fetchall()
    print("\nDOCTOR-WISE REVENUE REPORT")
    print_line()
    print(f"{'Doctor ID':<12}{'Doctor Name':<24}{'Specialization':<18}{'Bill Count':<12}{'Revenue':<12}")
    print_line()
    for r in rows:
        print(f"{r[0]:<12}{r[1]:<24}{r[2]:<18}{r[3]:<12}{float(r[4]):<12.2f}")


def daily_appointment_summary(conn):
    cursor = conn.cursor()
    date_value = input_date("Report Date")
    if not date_value:
        return
    cursor.execute("""
        SELECT A.APPOINTMENT_DATE, A.STATUS, COUNT(*) AS TOTAL
        FROM APPOINTMENT A
        WHERE A.APPOINTMENT_DATE = :date_value
        GROUP BY A.APPOINTMENT_DATE, A.STATUS
        ORDER BY A.STATUS
    """, {"date_value": date_value})
    rows = cursor.fetchall()
    print("\nDAILY APPOINTMENT SUMMARY")
    print_line()
    print(f"{'Date':<12}{'Status':<14}{'Total':<8}")
    print_line()
    for r in rows:
        print(f"{r[0].strftime('%Y-%m-%d'):<12}{r[1]:<14}{r[2]:<8}")


def doctor_availability_report(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DA.DAY_NAME, DA.SESSION_TYPE, DA.ROOM_NO, DA.START_TIME, DA.END_TIME,
               D.DOCTOR_ID, D.DOCTOR_NAME, DA.SPECIALIZATION, DA.MAX_PATIENTS, DA.STATUS
        FROM DOCTOR_AVAILABILITY DA
        JOIN DOCTOR_MASTER D ON DA.DOCTOR_ID = D.DOCTOR_ID
        ORDER BY CASE DA.DAY_NAME WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
                                  WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6 ELSE 7 END,
                 TO_DATE(DA.START_TIME, 'HH:MI AM'), DA.ROOM_NO
    """)
    rows = cursor.fetchall()
    print("\nDOCTOR AVAILABILITY WEEKLY REPORT")
    print_line(120)
    print(f"{'Day':<6}{'Session':<10}{'Room':<9}{'Start':<10}{'End':<10}{'Doc ID':<8}{'Doctor Name':<22}{'Spec':<18}{'Max':<5}{'Status':<10}")
    print_line(120)
    for r in rows:
        print(f"{r[0]:<6}{r[1]:<10}{r[2]:<9}{r[3]:<10}{r[4]:<10}{r[5]:<8}{r[6]:<22}{r[7]:<18}{str(r[8]):<5}{r[9]:<10}")


def reports_menu(conn):
    while True:
        print("\nREPORTS")
        print_line()
        print("1. Doctor-wise Appointment Count")
        print("2. City-wise Patient Count")
        print("3. Doctor-wise Revenue Report")
        print("4. Daily Appointment Summary")
        print("5. Doctor Availability Weekly Report")
        print("6. Back to Main Menu")
        choice = input("Enter choice: ").strip()
        if choice == "1": doctor_appointment_count(conn); pause()
        elif choice == "2": city_wise_patient_count(conn); pause()
        elif choice == "3": revenue_doctor_wise(conn); pause()
        elif choice == "4": daily_appointment_summary(conn); pause()
        elif choice == "5": doctor_availability_report(conn); pause()
        elif choice == "6": break
        else: print("Invalid choice.")

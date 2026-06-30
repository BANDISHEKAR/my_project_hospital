"""Import/Export module."""

import csv
import json
from pathlib import Path
from utils.id_generator import get_next_id
from utils.input_helper import print_line, pause, input_required


def import_patients_csv(conn):
    cursor = conn.cursor()
    print("\nIMPORT PATIENTS FROM CSV")
    print_line()
    print("Required CSV columns: PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS, CITY, BLOOD_GROUP, EMERGENCY_CONTACT")
    file_path = input_required("Enter CSV file path")
    if not file_path:
        return
    path = Path(file_path)
    if not path.exists():
        print("File not found.")
        return
    inserted = 0
    failed = 0
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    patient_id = get_next_id(cursor, "PATIENT_MASTER", "PATIENT_ID", "P", 3)
                    age = int(row.get("AGE") or 0) if row.get("AGE") else None
                    cursor.execute("""
                        INSERT INTO PATIENT_MASTER (
                            PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS,
                            CITY, BLOOD_GROUP, EMERGENCY_CONTACT, REGISTRATION_DATE
                        ) VALUES (
                            :patient_id, :name, :age, :gender, :phone, :email, :address,
                            :city, :blood_group, :emergency_contact, SYSDATE
                        )
                    """, dict(patient_id=patient_id, name=row.get("PATIENT_NAME"), age=age,
                              gender=row.get("GENDER") or None, phone=row.get("PHONE"),
                              email=row.get("EMAIL") or None, address=row.get("ADDRESS") or None,
                              city=row.get("CITY") or None, blood_group=row.get("BLOOD_GROUP") or None,
                              emergency_contact=row.get("EMERGENCY_CONTACT") or None))
                    inserted += 1
                except Exception as exc:
                    failed += 1
                    print("Failed row:", row, "Error:", exc)
        conn.commit()
        print(f"Import completed. Inserted: {inserted}, Failed: {failed}")
    except Exception as exc:
        conn.rollback()
        print("Import failed:", exc)


def export_patients_json(conn):
    cursor = conn.cursor()
    print("\nEXPORT PATIENTS TO JSON")
    print_line()
    file_path = input_required("Enter output JSON file path")
    if not file_path:
        return
    cursor.execute("""
        SELECT PATIENT_ID, PATIENT_NAME, AGE, GENDER, PHONE, EMAIL, ADDRESS, CITY,
               BLOOD_GROUP, EMERGENCY_CONTACT, REGISTRATION_DATE
        FROM PATIENT_MASTER ORDER BY PATIENT_ID
    """)
    columns = [d[0].lower() for d in cursor.description]
    data = []
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        if record.get("registration_date"):
            record["registration_date"] = record["registration_date"].strftime("%Y-%m-%d")
        data.append(record)
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Patients exported successfully to: {path}")


def export_daily_report_txt(conn):
    cursor = conn.cursor()
    print("\nEXPORT DAILY REPORT TO TXT")
    print_line()
    report_date = input_required("Enter report date (YYYY-MM-DD)")
    if not report_date:
        return
    file_path = input_required("Enter output TXT file path")
    if not file_path:
        return
    cursor.execute("""
        SELECT A.APPOINTMENT_ID, TO_DATE(A.APPOINTMENT_TIME, 'HH:MI AM'), A.TOKEN_NO, P.PATIENT_NAME,
               D.DOCTOR_NAME, DA.ROOM_NO, A.STATUS
        FROM APPOINTMENT A
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        JOIN DOCTOR_AVAILABILITY DA ON A.AVAILABILITY_ID = DA.AVAILABILITY_ID
        WHERE TO_CHAR(A.APPOINTMENT_DATE, 'YYYY-MM-DD') = :report_date
        ORDER BY TO_DATE(A.APPOINTMENT_TIME, 'HH:MI AM'), A.TOKEN_NO
    """, {"report_date": report_date})
    rows = cursor.fetchall()
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("DAILY APPOINTMENT REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Report Date: {report_date}\n")
        f.write("=" * 80 + "\n")
        for r in rows:
            f.write(f"{r[0]} | {r[1]} | Token {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Appointments: {len(rows)}\n")
    print(f"Daily report exported successfully to: {path}")


def import_export_menu(conn):
    while True:
        print("\nIMPORT / EXPORT")
        print_line()
        print("1. Import Patients from CSV")
        print("2. Export Patients to JSON")
        print("3. Export Daily Report to TXT")
        print("4. Back to Main Menu")
        choice = input("Enter choice: ").strip()
        if choice == "1": import_patients_csv(conn); pause()
        elif choice == "2": export_patients_json(conn); pause()
        elif choice == "3": export_daily_report_txt(conn); pause()
        elif choice == "4": break
        else: print("Invalid choice.")

"""Reports module with view and download options."""

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from utils.input_helper import print_line, pause, input_date


# -----------------------------------------------------------------------------
# Common helper functions
# -----------------------------------------------------------------------------

def _format_value(value):
    """Convert database values into clean printable/exportable values."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def _value_to_text(value):
    value = _format_value(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _print_report(title, headers, rows):
    """Show report data on screen in table format."""
    print(f"\n{title}")
    if not rows:
        print_line()
        print("No records found.")
        return

    text_rows = [[_value_to_text(value) for value in row] for row in rows]
    widths = []
    for index, header in enumerate(headers):
        max_width = len(header)
        for row in text_rows:
            max_width = max(max_width, len(row[index]))
        widths.append(max_width + 3)

    total_width = sum(widths)
    print_line(total_width)
    print("".join(f"{headers[i]:<{widths[i]}}" for i in range(len(headers))))
    print_line(total_width)
    for row in text_rows:
        print("".join(f"{row[i]:<{widths[i]}}" for i in range(len(row))))


def _rows_to_dicts(headers, rows):
    records = []
    for row in rows:
        record = {}
        for index, header in enumerate(headers):
            record[header] = _format_value(row[index])
        records.append(record)
    return records


def _ask_yes_no(message):
    while True:
        answer = input(message).strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please enter yes or no.")


def _select_download_file(default_filename, window_title):
    """Open Save As window and return selected path."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        file_path = filedialog.asksaveasfilename(
            title=window_title,
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Excel files", "*.xlsx"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        if not file_path:
            return None
        return Path(file_path)
    except Exception as exc:
        print("Could not open save window:", exc)
        return None


def _save_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([_format_value(value) for value in row])


def _save_json(path, headers, rows):
    data = _rows_to_dicts(headers, rows)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False, default=str)


def _save_txt(path, title, headers, rows):
    text_rows = [[_value_to_text(value) for value in row] for row in rows]
    widths = []
    for index, header in enumerate(headers):
        max_width = len(header)
        for row in text_rows:
            max_width = max(max_width, len(row[index]))
        widths.append(max_width + 3)

    total_width = max(sum(widths), len(title) + 4)
    with path.open("w", encoding="utf-8") as file:
        file.write(title + "\n")
        file.write("=" * total_width + "\n")
        if not rows:
            file.write("No records found.\n")
        else:
            file.write("".join(f"{headers[i]:<{widths[i]}}" for i in range(len(headers))) + "\n")
            file.write("=" * total_width + "\n")
            for row in text_rows:
                file.write("".join(f"{row[i]:<{widths[i]}}" for i in range(len(row))) + "\n")
        file.write("=" * total_width + "\n")
        file.write(f"Total Records: {len(rows)}\n")


def _save_excel(path, title, headers, rows):
    try:
        from openpyxl import Workbook
    except ImportError:
        print("Excel download needs openpyxl. Install it using: pip install openpyxl")
        return False

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Report"

    sheet.append([title])
    sheet.append(headers)
    for row in rows:
        sheet.append([_format_value(value) for value in row])

    for column_cells in sheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            max_length = max(max_length, len(str(cell.value)) if cell.value is not None else 0)
        sheet.column_dimensions[column_letter].width = max_length + 3

    workbook.save(path)
    return True


def _download_report(title, headers, rows, default_filename):
    """Ask user whether to download and save report in selected file type."""
    if not _ask_yes_no("\nDo you want to download this report? (yes/no): "):
        return

    print("Opening save location window...")
    path = _select_download_file(default_filename, f"Save {title}")
    if not path:
        print("Download cancelled.")
        return

    if not path.suffix:
        path = path.with_suffix(".csv")

    path.parent.mkdir(parents=True, exist_ok=True)
    extension = path.suffix.lower()

    try:
        if extension == ".csv":
            _save_csv(path, headers, rows)
        elif extension == ".json":
            _save_json(path, headers, rows)
        elif extension == ".xlsx":
            success = _save_excel(path, title, headers, rows)
            if not success:
                return
        elif extension == ".txt":
            _save_txt(path, title, headers, rows)
        else:
            print("Unsupported file type. Please save as .csv, .json, .xlsx, or .txt")
            return

        print(f"Report downloaded successfully to: {path}")
    except Exception as exc:
        print("Report download failed:", exc)


# -----------------------------------------------------------------------------
# Report functions
# -----------------------------------------------------------------------------

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
    title = "DOCTOR-WISE APPOINTMENT COUNT"
    headers = ["Doctor ID", "Doctor Name", "Specialization", "Total Appointments"]
    _print_report(title, headers, rows)
    _download_report(title, headers, rows, "doctor_appointment_count.csv")


def city_wise_patient_count(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT NVL(CITY, 'Not Provided') AS CITY, COUNT(*) AS TOTAL_PATIENTS
        FROM PATIENT_MASTER
        GROUP BY NVL(CITY, 'Not Provided')
        ORDER BY TOTAL_PATIENTS DESC, CITY
    """)
    rows = cursor.fetchall()
    title = "CITY-WISE PATIENT COUNT"
    headers = ["City", "Total Patients"]
    _print_report(title, headers, rows)
    _download_report(title, headers, rows, "city_wise_patient_count.csv")


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
    title = "DOCTOR-WISE REVENUE REPORT"
    headers = ["Doctor ID", "Doctor Name", "Specialization", "Bill Count", "Revenue"]
    _print_report(title, headers, rows)
    _download_report(title, headers, rows, "doctor_wise_revenue_report.csv")


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
    title = "DAILY APPOINTMENT SUMMARY"
    headers = ["Date", "Status", "Total"]
    _print_report(title, headers, rows)
    _download_report(title, headers, rows, "daily_appointment_summary.csv")


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
    title = "DOCTOR AVAILABILITY WEEKLY REPORT"
    headers = ["Day", "Session", "Room", "Start", "End", "Doctor ID", "Doctor Name", "Specialization", "Max", "Status"]
    _print_report(title, headers, rows)
    _download_report(title, headers, rows, "doctor_availability_weekly_report.csv")


# -----------------------------------------------------------------------------
# Reports menu
# -----------------------------------------------------------------------------

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

        if choice == "1":
            doctor_appointment_count(conn)
            pause()
        elif choice == "2":
            city_wise_patient_count(conn)
            pause()
        elif choice == "3":
            revenue_doctor_wise(conn)
            pause()
        elif choice == "4":
            daily_appointment_summary(conn)
            pause()
        elif choice == "5":
            doctor_availability_report(conn)
            pause()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 6.")

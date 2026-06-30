# Hospital Management System - Python + Oracle

This is a GitHub-ready CLI project for a Hospital Management System using Python and Oracle.

## Main Features

1. Doctor Management
   - Add doctor
   - View doctors
   - Update doctor
   - Delete / deactivate doctor
   - Doctor licence number included
   - Doctor Availability is inside Doctor Management

2. Doctor Availability
   - Replaces old `SESSION_MANAGEMENT`
   - Table name: `DOCTOR_AVAILABILITY`
   - Uses 12-hour AM/PM time format, example `09:00 AM`, `05:00 PM`
   - Supports 2 rooms
   - Manages day, session, room, start time, end time, doctor, specialization, max patients, status

3. Patient Management
   - Add patient
   - View patients
   - Update patient
   - Delete patient if no appointments exist
   - Email, blood group, address, city are optional

4. Appointment Management
   - Books appointments using `DOCTOR_AVAILABILITY`
   - Auto-generates appointment ID
   - Auto-generates token number
   - Auto-calculates appointment time based on session start/end and max patients
   - Supports booked, completed, cancelled status

5. Consultation Management
   - Adds consultation only for completed appointments
   - Includes `TOKEN_NO` in consultation table
   - Stores symptoms, diagnosis, prescription, follow-up date, doctor notes

6. Billing Management
   - Shows calculated bill first
   - Asks whether patient paid or not
   - Supports payment method: Cash, UPI, Card, Online, Insurance, Other

7. Reports
   - Doctor-wise appointment count
   - City-wise patient count
   - Doctor-wise revenue report
   - Daily appointment summary
   - Doctor availability weekly report

8. Import / Export
   - Import patients from CSV
   - Export patients to JSON
   - Export daily appointment report to TXT

## Project Structure

```text
hospital_management_system_doctor_availability/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── config/
│   ├── __init__.py
│   └── db_connection.py
├── modules/
│   ├── __init__.py
│   ├── doctor_management.py
│   ├── patient_management.py
│   ├── appointment_management.py
│   ├── consultation_management.py
│   ├── billing_management.py
│   ├── reports.py
│   └── import_export.py
├── utils/
│   ├── __init__.py
│   ├── input_helper.py
│   ├── id_generator.py
│   └── time_helper.py
├── sql/
│   ├── schema_and_sample_data.sql
│   └── select_all_tables.sql
├── sample_files/
│   └── import_patient_data.csv
├── exports/
└── docs/
```

## Setup Steps

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Update Oracle DB connection

Open:

```text
config/db_connection.py
```

Update these values:

```python
USERNAME = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"
HOST = "YOUR_HOST"
PORT = 1521
SERVICE_NAME = "orcl"
```

### 3. Create Oracle tables

Open Oracle SQL Developer and run:

```text
sql/schema_and_sample_data.sql
```

This script drops old tables and creates fresh tables with sample data.

### 4. Run project

```bash
python main.py
```

## Main Tables

1. `DOCTOR_MASTER`
2. `PATIENT_MASTER`
3. `DOCTOR_AVAILABILITY`
4. `APPOINTMENT`
5. `CONSULTATION`
6. `BILLING`

## Important Notes

- `DOCTOR_AVAILABILITY` is the renamed version of `SESSION_MANAGEMENT`.
- `APPOINTMENT` has `AVAILABILITY_ID` to connect appointment with doctor availability.
- `CONSULTATION` has `TOKEN_NO` as requested.
- `DOCTOR_MASTER` has `DOCTOR_LICENCE_NO` as requested.
- Time values are stored in 12-hour format like `08:00 AM`, `04:00 PM`.

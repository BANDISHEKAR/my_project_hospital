-- ============================================================
-- HOSPITAL MANAGEMENT SYSTEM - ORACLE SQL SCRIPT
-- Tables:
--   DOCTOR_MASTER
--   PATIENT_MASTER
--   DOCTOR_AVAILABILITY
--   APPOINTMENT
--   CONSULTATION
--   BILLING
--
-- Important changes included:
--   1) DOCTOR_MASTER has DOCTOR_LICENCE_NO column
--   2) CONSULTATION has TOKEN_NO column
--   3) SESSION_MANAGEMENT renamed to DOCTOR_AVAILABILITY
--   4) Time data stored in 12-hour AM/PM format
--
-- WARNING:
--   This script will DROP existing tables and DELETE old data.
-- ============================================================

SET SERVEROUTPUT ON;
SET DEFINE OFF;

-- ============================================================
-- 1. DROP PREVIOUS TABLES
-- Drop child tables first, then parent tables
-- ============================================================

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE BILLING CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE CONSULTATION CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE APPOINTMENT CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE DOCTOR_AVAILABILITY CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE PATIENT_MASTER CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE DOCTOR_MASTER CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

PROMPT Previous tables dropped successfully.

-- ============================================================
-- 2. CREATE TABLES
-- ============================================================

-- ------------------------------------------------------------
-- DOCTOR_MASTER
-- Stores doctor basic details.
-- Availability/timetable is stored separately in DOCTOR_AVAILABILITY.
-- ------------------------------------------------------------
CREATE TABLE DOCTOR_MASTER (
    DOCTOR_ID            VARCHAR2(10) PRIMARY KEY,
    DOCTOR_NAME          VARCHAR2(100) NOT NULL,
    DOCTOR_LICENCE_NO    VARCHAR2(30)  NOT NULL UNIQUE,
    SPECIALIZATION       VARCHAR2(50)  NOT NULL,
    PHONE                VARCHAR2(15)  NOT NULL UNIQUE,
    EMAIL                VARCHAR2(100),
    EXPERIENCE_YEARS     NUMBER(3) DEFAULT 0,
    CONSULTATION_FEE     NUMBER(10,2) NOT NULL,
    STATUS               VARCHAR2(20) DEFAULT 'Active' NOT NULL,
    CREATED_DATE         DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_DOCTOR_STATUS CHECK (STATUS IN ('Active', 'Inactive')),
    CONSTRAINT CHK_DOCTOR_EXP CHECK (EXPERIENCE_YEARS >= 0),
    CONSTRAINT CHK_DOCTOR_FEE CHECK (CONSULTATION_FEE >= 0)
);

-- ------------------------------------------------------------
-- PATIENT_MASTER
-- Stores patient basic registration details.
-- ------------------------------------------------------------
CREATE TABLE PATIENT_MASTER (
    PATIENT_ID           VARCHAR2(10) PRIMARY KEY,
    PATIENT_NAME         VARCHAR2(100) NOT NULL,
    AGE                  NUMBER(3),
    GENDER               VARCHAR2(10),
    PHONE                VARCHAR2(15) NOT NULL UNIQUE,
    EMAIL                VARCHAR2(100),
    ADDRESS              VARCHAR2(250),
    CITY                 VARCHAR2(50),
    BLOOD_GROUP          VARCHAR2(5),
    EMERGENCY_CONTACT    VARCHAR2(15),
    REGISTRATION_DATE    DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_PATIENT_AGE CHECK (AGE IS NULL OR AGE BETWEEN 0 AND 120),
    CONSTRAINT CHK_PATIENT_GENDER CHECK (GENDER IS NULL OR GENDER IN ('Male', 'Female', 'Other'))
);

-- ------------------------------------------------------------
-- DOCTOR_AVAILABILITY
-- This replaces SESSION_MANAGEMENT.
-- Stores weekly doctor timetable using 2 rooms.
-- ------------------------------------------------------------
CREATE TABLE DOCTOR_AVAILABILITY (
    AVAILABILITY_ID      VARCHAR2(10) PRIMARY KEY,
    DAY_NAME             VARCHAR2(10) NOT NULL,
    SESSION_TYPE         VARCHAR2(20) NOT NULL,
    ROOM_NO              VARCHAR2(20) NOT NULL,
    START_TIME           VARCHAR2(10) NOT NULL,
    END_TIME             VARCHAR2(10) NOT NULL,
    DOCTOR_ID            VARCHAR2(10) NOT NULL,
    SPECIALIZATION       VARCHAR2(50) NOT NULL,
    MAX_PATIENTS         NUMBER(3) DEFAULT 10 NOT NULL,
    STATUS               VARCHAR2(20) DEFAULT 'Active' NOT NULL,
    CONSTRAINT FK_AVAILABILITY_DOCTOR
        FOREIGN KEY (DOCTOR_ID) REFERENCES DOCTOR_MASTER(DOCTOR_ID),
    CONSTRAINT CHK_AVAIL_DAY CHECK (DAY_NAME IN ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')),
    CONSTRAINT CHK_AVAIL_SESSION CHECK (SESSION_TYPE IN ('Morning', 'Evening')),
    CONSTRAINT CHK_AVAIL_STATUS CHECK (STATUS IN ('Active', 'Inactive')),
    CONSTRAINT CHK_AVAIL_MAX_PATIENTS CHECK (MAX_PATIENTS > 0),
    CONSTRAINT UK_ROOM_DAY_TIME UNIQUE (DAY_NAME, ROOM_NO, START_TIME, END_TIME),
    CONSTRAINT UK_DOCTOR_DAY_TIME UNIQUE (DAY_NAME, DOCTOR_ID, START_TIME, END_TIME)
);

-- ------------------------------------------------------------
-- APPOINTMENT
-- Stores patient appointment bookings.
-- AVAILABILITY_ID connects appointment to DOCTOR_AVAILABILITY.
-- ------------------------------------------------------------
CREATE TABLE APPOINTMENT (
    APPOINTMENT_ID       VARCHAR2(10) PRIMARY KEY,
    PATIENT_ID           VARCHAR2(10) NOT NULL,
    DOCTOR_ID            VARCHAR2(10) NOT NULL,
    AVAILABILITY_ID      VARCHAR2(10) NOT NULL,
    APPOINTMENT_DATE     DATE NOT NULL,
    APPOINTMENT_TIME     VARCHAR2(10) NOT NULL,
    TOKEN_NO             NUMBER(3) NOT NULL,
    BOOKING_DATE         DATE DEFAULT SYSDATE,
    REASON_FOR_VISIT     VARCHAR2(250),
    STATUS               VARCHAR2(20) DEFAULT 'Booked' NOT NULL,
    CONSTRAINT FK_APPOINTMENT_PATIENT
        FOREIGN KEY (PATIENT_ID) REFERENCES PATIENT_MASTER(PATIENT_ID),
    CONSTRAINT FK_APPOINTMENT_DOCTOR
        FOREIGN KEY (DOCTOR_ID) REFERENCES DOCTOR_MASTER(DOCTOR_ID),
    CONSTRAINT FK_APPOINTMENT_AVAILABILITY
        FOREIGN KEY (AVAILABILITY_ID) REFERENCES DOCTOR_AVAILABILITY(AVAILABILITY_ID),
    CONSTRAINT CHK_APPOINTMENT_STATUS CHECK (STATUS IN ('Booked', 'Completed', 'Cancelled')),
    CONSTRAINT CHK_APPOINTMENT_TOKEN CHECK (TOKEN_NO > 0),
    CONSTRAINT UK_APPT_AVAIL_DATE_TOKEN UNIQUE (AVAILABILITY_ID, APPOINTMENT_DATE, TOKEN_NO)
);

-- ------------------------------------------------------------
-- CONSULTATION
-- Stores consultation details after appointment.
-- TOKEN_NO added as requested.
-- ------------------------------------------------------------
CREATE TABLE CONSULTATION (
    CONSULTATION_ID       VARCHAR2(10) PRIMARY KEY,
    APPOINTMENT_ID        VARCHAR2(10) NOT NULL UNIQUE,
    TOKEN_NO              NUMBER(3) NOT NULL,
    CONSULTATION_DATE     DATE DEFAULT SYSDATE,
    SYMPTOMS              VARCHAR2(500),
    DIAGNOSIS             VARCHAR2(500),
    PRESCRIPTION          VARCHAR2(1000),
    FOLLOW_UP_DATE        DATE,
    CONSULTATION_STATUS   VARCHAR2(20) DEFAULT 'Completed' NOT NULL,
    DOCTOR_NOTES          VARCHAR2(1000),
    CONSTRAINT FK_CONSULTATION_APPOINTMENT
        FOREIGN KEY (APPOINTMENT_ID) REFERENCES APPOINTMENT(APPOINTMENT_ID),
    CONSTRAINT CHK_CONSULTATION_STATUS CHECK (CONSULTATION_STATUS IN ('Completed', 'Pending')),
    CONSTRAINT CHK_CONSULTATION_TOKEN CHECK (TOKEN_NO > 0)
);

-- ------------------------------------------------------------
-- BILLING
-- Stores billing and payment details.
-- ------------------------------------------------------------
CREATE TABLE BILLING (
    BILL_ID              VARCHAR2(10) PRIMARY KEY,
    APPOINTMENT_ID       VARCHAR2(10) NOT NULL UNIQUE,
    BILL_DATE            DATE DEFAULT SYSDATE,
    CONSULTATION_FEE     NUMBER(10,2) DEFAULT 0 NOT NULL,
    MEDICINE_CHARGES     NUMBER(10,2) DEFAULT 0 NOT NULL,
    TEST_CHARGES         NUMBER(10,2) DEFAULT 0 NOT NULL,
    GROSS_AMOUNT         NUMBER(10,2) DEFAULT 0 NOT NULL,
    DISCOUNT             NUMBER(10,2) DEFAULT 0 NOT NULL,
    FINAL_AMOUNT         NUMBER(10,2) DEFAULT 0 NOT NULL,
    PAYMENT_STATUS       VARCHAR2(20) DEFAULT 'Unpaid' NOT NULL,
    PAYMENT_METHOD       VARCHAR2(30),
    PAYMENT_DATE         DATE,
    CONSTRAINT FK_BILLING_APPOINTMENT
        FOREIGN KEY (APPOINTMENT_ID) REFERENCES APPOINTMENT(APPOINTMENT_ID),
    CONSTRAINT CHK_BILLING_PAYMENT_STATUS CHECK (PAYMENT_STATUS IN ('Paid', 'Unpaid')),
    CONSTRAINT CHK_BILLING_PAYMENT_METHOD CHECK (
        PAYMENT_METHOD IS NULL OR PAYMENT_METHOD IN ('Cash', 'UPI', 'Card', 'Online', 'Insurance', 'Other')
    ),
    CONSTRAINT CHK_BILLING_AMOUNT CHECK (
        CONSULTATION_FEE >= 0 AND MEDICINE_CHARGES >= 0 AND TEST_CHARGES >= 0 AND
        GROSS_AMOUNT >= 0 AND DISCOUNT >= 0 AND FINAL_AMOUNT >= 0
    )
);

PROMPT Tables created successfully.

-- ============================================================
-- 3. INSERT SAMPLE DATA
-- ============================================================

-- ------------------------------------------------------------
-- DOCTOR_MASTER DATA
-- ------------------------------------------------------------
INSERT INTO DOCTOR_MASTER VALUES ('D001', 'Rajesh Kumar',  'LIC-GP-1001',   'GP',          '9000000001', 'rajesh.kumar@hospital.com',  8, 500, 'Active', SYSDATE);
INSERT INTO DOCTOR_MASTER VALUES ('D002', 'Priya Sharma',  'LIC-ENT-1002',  'ENT',         '9000000002', 'priya.sharma@hospital.com',  6, 600, 'Active', SYSDATE);
INSERT INTO DOCTOR_MASTER VALUES ('D003', 'Arjun Reddy',   'LIC-ORT-1003',  'Orthopedic',  '9000000003', 'arjun.reddy@hospital.com',  10, 700, 'Active', SYSDATE);
INSERT INTO DOCTOR_MASTER VALUES ('D004', 'Kavya Rao',     'LIC-GP-1004',   'GP',          '9000000004', 'kavya.rao@hospital.com',     5, 500, 'Active', SYSDATE);
INSERT INTO DOCTOR_MASTER VALUES ('D005', 'Suresh Babu',   'LIC-ENT-1005',  'ENT',         '9000000005', 'suresh.babu@hospital.com',   7, 600, 'Active', SYSDATE);
INSERT INTO DOCTOR_MASTER VALUES ('D006', 'Anjali Mehta',  'LIC-ORT-1006',  'Orthopedic',  '9000000006', 'anjali.mehta@hospital.com',  9, 700, 'Active', SYSDATE);

-- ------------------------------------------------------------
-- PATIENT_MASTER DATA
-- ------------------------------------------------------------
INSERT INTO PATIENT_MASTER VALUES ('P001', 'Ravi Kumar',    28, 'Male',   '9100000001', 'ravi.kumar@example.com',    'MG Road',       'Bengaluru', 'O+',  '9100000101', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P002', 'Sneha Reddy',   24, 'Female', '9100000002', NULL,                        'BTM Layout',    'Bengaluru', 'A+',  '9100000102', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P003', 'Arun Naidu',    35, 'Male',   '9100000003', 'arun.naidu@example.com',    'Indiranagar',   'Bengaluru', NULL,  '9100000103', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P004', 'Meena Kumari',  31, 'Female', '9100000004', 'meena.kumari@example.com',  'Koramangala',   'Bengaluru', 'B+',  '9100000104', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P005', 'Vikram Singh',  42, 'Male',   '9100000005', NULL,                        'Whitefield',    'Bengaluru', 'AB+', '9100000105', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P006', 'Lakshmi Devi',  50, 'Female', '9100000006', 'lakshmi.devi@example.com',  'Jayanagar',     'Bengaluru', 'O-',  '9100000106', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P007', 'Kiran Kumar',   29, 'Male',   '9100000007', 'kiran.kumar@example.com',   'Hebbal',        'Bengaluru', NULL,  '9100000107', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P008', 'Divya Sharma',  26, 'Female', '9100000008', NULL,                        'Electronic City','Bengaluru','A-',  '9100000108', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P009', 'Manoj Gowda',   38, 'Male',   '9100000009', 'manoj.gowda@example.com',   'Yelahanka',     'Bengaluru', 'B-',  '9100000109', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO PATIENT_MASTER VALUES ('P010', 'Pooja Rao',     22, 'Female', '9100000010', 'pooja.rao@example.com',     'Rajajinagar',   'Bengaluru', NULL,  '9100000110', TO_DATE('2026-06-29', 'YYYY-MM-DD'));

-- ------------------------------------------------------------
-- DOCTOR_AVAILABILITY DATA
-- 2 rooms, Monday to Saturday, Morning and Evening.
-- Each doctor has 4 sessions per week.
-- ------------------------------------------------------------

-- Monday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV001', 'Mon', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D001', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV002', 'Mon', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D002', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV003', 'Mon', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D003', 'Orthopedic', 10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV004', 'Mon', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D004', 'GP',         10, 'Active');

-- Tuesday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV005', 'Tue', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D001', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV006', 'Tue', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D005', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV007', 'Tue', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D002', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV008', 'Tue', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D006', 'Orthopedic', 10, 'Active');

-- Wednesday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV009', 'Wed', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D004', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV010', 'Wed', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D002', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV011', 'Wed', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D003', 'Orthopedic', 10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV012', 'Wed', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D006', 'Orthopedic', 10, 'Active');

-- Thursday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV013', 'Thu', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D001', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV014', 'Thu', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D003', 'Orthopedic', 10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV015', 'Thu', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D004', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV016', 'Thu', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D005', 'ENT',        10, 'Active');

-- Friday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV017', 'Fri', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D004', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV018', 'Fri', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D002', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV019', 'Fri', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D005', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV020', 'Fri', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D006', 'Orthopedic', 10, 'Active');

-- Saturday
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV021', 'Sat', 'Morning', 'Room-1', '08:00 AM', '10:00 AM', 'D001', 'GP',         10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV022', 'Sat', 'Morning', 'Room-2', '10:00 AM', '12:00 PM', 'D003', 'Orthopedic', 10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV023', 'Sat', 'Evening', 'Room-1', '04:00 PM', '06:00 PM', 'D005', 'ENT',        10, 'Active');
INSERT INTO DOCTOR_AVAILABILITY VALUES ('AV024', 'Sat', 'Evening', 'Room-2', '06:00 PM', '08:00 PM', 'D006', 'Orthopedic', 10, 'Active');

-- ------------------------------------------------------------
-- APPOINTMENT DATA
-- Appointment date 2026-06-29 is Monday.
-- TOKEN_NO will be copied into CONSULTATION table also.
-- ------------------------------------------------------------
INSERT INTO APPOINTMENT VALUES ('A001', 'P001', 'D001', 'AV001', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '08:00 AM', 1, TO_DATE('2026-06-28', 'YYYY-MM-DD'), 'Fever and body pains',       'Completed');
INSERT INTO APPOINTMENT VALUES ('A002', 'P002', 'D001', 'AV001', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '08:12 AM', 2, TO_DATE('2026-06-28', 'YYYY-MM-DD'), 'Cold and cough',             'Completed');
INSERT INTO APPOINTMENT VALUES ('A003', 'P003', 'D002', 'AV002', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '10:00 AM', 1, TO_DATE('2026-06-28', 'YYYY-MM-DD'), 'Ear pain',                   'Completed');
INSERT INTO APPOINTMENT VALUES ('A004', 'P004', 'D002', 'AV002', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '10:12 AM', 2, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Throat infection',           'Booked');
INSERT INTO APPOINTMENT VALUES ('A005', 'P005', 'D003', 'AV003', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '04:00 PM', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Knee pain',                  'Completed');
INSERT INTO APPOINTMENT VALUES ('A006', 'P006', 'D003', 'AV003', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '04:12 PM', 2, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Back pain',                  'Booked');
INSERT INTO APPOINTMENT VALUES ('A007', 'P007', 'D004', 'AV004', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '06:00 PM', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'General checkup',            'Completed');
INSERT INTO APPOINTMENT VALUES ('A008', 'P008', 'D004', 'AV004', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '06:12 PM', 2, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Headache',                   'Booked');
INSERT INTO APPOINTMENT VALUES ('A009', 'P009', 'D001', 'AV001', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '08:24 AM', 3, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Fever',                      'Cancelled');
INSERT INTO APPOINTMENT VALUES ('A010', 'P010', 'D002', 'AV002', TO_DATE('2026-06-29', 'YYYY-MM-DD'), '10:24 AM', 3, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Nose blockage',              'Booked');

-- ------------------------------------------------------------
-- CONSULTATION DATA
-- Only completed appointments are inserted here.
-- TOKEN_NO column is included.
-- ------------------------------------------------------------
INSERT INTO CONSULTATION VALUES ('C001', 'A001', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Fever and body pains', 'Viral fever',        'Paracetamol 500mg twice daily for 3 days', TO_DATE('2026-07-03', 'YYYY-MM-DD'), 'Completed', 'Drink more water and take rest.');
INSERT INTO CONSULTATION VALUES ('C002', 'A002', 2, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Cold and cough',       'Common cold',        'Cough syrup and steam inhalation',        TO_DATE('2026-07-02', 'YYYY-MM-DD'), 'Completed', 'Avoid cold drinks.');
INSERT INTO CONSULTATION VALUES ('C003', 'A003', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Ear pain',             'Ear infection',      'Antibiotic ear drops for 5 days',         TO_DATE('2026-07-04', 'YYYY-MM-DD'), 'Completed', 'Keep ear dry.');
INSERT INTO CONSULTATION VALUES ('C004', 'A005', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'Knee pain',            'Mild joint strain',  'Pain relief tablet and physiotherapy',    TO_DATE('2026-07-06', 'YYYY-MM-DD'), 'Completed', 'Avoid heavy walking for one week.');
INSERT INTO CONSULTATION VALUES ('C005', 'A007', 1, TO_DATE('2026-06-29', 'YYYY-MM-DD'), 'General checkup',      'Normal condition',   'Multivitamin once daily for 15 days',     NULL,                                      'Completed', 'Patient is stable.');

-- ------------------------------------------------------------
-- BILLING DATA
-- Gross Amount = Consultation Fee + Medicine Charges + Test Charges
-- Final Amount = Gross Amount - Discount
-- ------------------------------------------------------------
INSERT INTO BILLING VALUES ('B001', 'A001', TO_DATE('2026-06-29', 'YYYY-MM-DD'), 500, 300, 700, 1500, 100, 1400, 'Paid',   'UPI',  TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO BILLING VALUES ('B002', 'A002', TO_DATE('2026-06-29', 'YYYY-MM-DD'), 500, 150,   0,  650,  50,  600, 'Paid',   'Cash', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO BILLING VALUES ('B003', 'A003', TO_DATE('2026-06-29', 'YYYY-MM-DD'), 600, 250, 300, 1150,   0, 1150, 'Paid',   'Card', TO_DATE('2026-06-29', 'YYYY-MM-DD'));
INSERT INTO BILLING VALUES ('B004', 'A005', TO_DATE('2026-06-29', 'YYYY-MM-DD'), 700, 200, 500, 1400, 100, 1300, 'Unpaid', NULL,   NULL);
INSERT INTO BILLING VALUES ('B005', 'A007', TO_DATE('2026-06-29', 'YYYY-MM-DD'), 500, 100,   0,  600,   0,  600, 'Paid',   'UPI',  TO_DATE('2026-06-29', 'YYYY-MM-DD'));

COMMIT;

PROMPT Sample data inserted successfully.

-- ============================================================
-- 4. CHECK DATA
-- ============================================================

PROMPT DOCTOR_MASTER count:
SELECT COUNT(*) AS DOCTOR_COUNT FROM DOCTOR_MASTER;

PROMPT PATIENT_MASTER count:
SELECT COUNT(*) AS PATIENT_COUNT FROM PATIENT_MASTER;

PROMPT DOCTOR_AVAILABILITY count:
SELECT COUNT(*) AS AVAILABILITY_COUNT FROM DOCTOR_AVAILABILITY;

PROMPT APPOINTMENT count:
SELECT COUNT(*) AS APPOINTMENT_COUNT FROM APPOINTMENT;

PROMPT CONSULTATION count:
SELECT COUNT(*) AS CONSULTATION_COUNT FROM CONSULTATION;

PROMPT BILLING count:
SELECT COUNT(*) AS BILLING_COUNT FROM BILLING;

-- ============================================================
-- 5. USEFUL SAMPLE QUERIES
-- ============================================================

-- View doctor weekly availability
SELECT
    da.DAY_NAME,
    da.SESSION_TYPE,
    da.ROOM_NO,
    da.START_TIME,
    da.END_TIME,
    da.DOCTOR_ID,
    dm.DOCTOR_NAME,
    dm.DOCTOR_LICENCE_NO,
    da.SPECIALIZATION,
    da.MAX_PATIENTS,
    da.STATUS
FROM DOCTOR_AVAILABILITY da
JOIN DOCTOR_MASTER dm
    ON da.DOCTOR_ID = dm.DOCTOR_ID
ORDER BY
    CASE da.DAY_NAME
        WHEN 'Mon' THEN 1
        WHEN 'Tue' THEN 2
        WHEN 'Wed' THEN 3
        WHEN 'Thu' THEN 4
        WHEN 'Fri' THEN 5
        WHEN 'Sat' THEN 6
        WHEN 'Sun' THEN 7
    END,
    TO_DATE(da.START_TIME, 'HH:MI AM');

-- Check doctor working sessions and hours
SELECT
    dm.DOCTOR_ID,
    dm.DOCTOR_NAME,
    dm.SPECIALIZATION,
    COUNT(da.AVAILABILITY_ID) AS TOTAL_SESSIONS,
    COUNT(da.AVAILABILITY_ID) * 2 AS TOTAL_HOURS
FROM DOCTOR_MASTER dm
LEFT JOIN DOCTOR_AVAILABILITY da
    ON dm.DOCTOR_ID = da.DOCTOR_ID
GROUP BY dm.DOCTOR_ID, dm.DOCTOR_NAME, dm.SPECIALIZATION
ORDER BY dm.DOCTOR_ID;

-- View appointments with token and doctor availability details
SELECT
    a.APPOINTMENT_ID,
    a.APPOINTMENT_DATE,
    a.APPOINTMENT_TIME,
    a.TOKEN_NO,
    p.PATIENT_NAME,
    dm.DOCTOR_NAME,
    dm.DOCTOR_LICENCE_NO,
    da.ROOM_NO,
    da.SESSION_TYPE,
    a.STATUS
FROM APPOINTMENT a
JOIN PATIENT_MASTER p
    ON a.PATIENT_ID = p.PATIENT_ID
JOIN DOCTOR_MASTER dm
    ON a.DOCTOR_ID = dm.DOCTOR_ID
JOIN DOCTOR_AVAILABILITY da
    ON a.AVAILABILITY_ID = da.AVAILABILITY_ID
ORDER BY a.APPOINTMENT_DATE, TO_DATE(a.APPOINTMENT_TIME, 'HH:MI AM');

-- View consultation details with token number
SELECT
    c.CONSULTATION_ID,
    c.APPOINTMENT_ID,
    c.TOKEN_NO,
    c.CONSULTATION_DATE,
    p.PATIENT_NAME,
    dm.DOCTOR_NAME,
    c.SYMPTOMS,
    c.DIAGNOSIS,
    c.PRESCRIPTION,
    c.CONSULTATION_STATUS
FROM CONSULTATION c
JOIN APPOINTMENT a
    ON c.APPOINTMENT_ID = a.APPOINTMENT_ID
JOIN PATIENT_MASTER p
    ON a.PATIENT_ID = p.PATIENT_ID
JOIN DOCTOR_MASTER dm
    ON a.DOCTOR_ID = dm.DOCTOR_ID
ORDER BY c.CONSULTATION_ID;

-- View billing details
SELECT
    b.BILL_ID,
    b.APPOINTMENT_ID,
    p.PATIENT_NAME,
    dm.DOCTOR_NAME,
    b.CONSULTATION_FEE,
    b.MEDICINE_CHARGES,
    b.TEST_CHARGES,
    b.GROSS_AMOUNT,
    b.DISCOUNT,
    b.FINAL_AMOUNT,
    b.PAYMENT_STATUS,
    b.PAYMENT_METHOD
FROM BILLING b
JOIN APPOINTMENT a
    ON b.APPOINTMENT_ID = a.APPOINTMENT_ID
JOIN PATIENT_MASTER p
    ON a.PATIENT_ID = p.PATIENT_ID
JOIN DOCTOR_MASTER dm
    ON a.DOCTOR_ID = dm.DOCTOR_ID
ORDER BY b.BILL_ID;

PROMPT Script completed successfully.

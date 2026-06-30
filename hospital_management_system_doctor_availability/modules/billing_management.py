"""Billing Management module."""

from utils.id_generator import get_next_id
from utils.input_helper import print_line, pause, input_float, input_payment_method, is_back
from modules.appointment_management import choose_appointment_id


def display_bills(rows):
    if not rows:
        print("\nNo billing records found.")
        return
    print("\nBILLING DETAILS")
    print_line(130)
    print(f"{'Bill ID':<8}{'Appt ID':<9}{'Patient':<22}{'Doctor':<22}{'Consult':<10}{'Medicine':<10}{'Tests':<10}{'Gross':<10}{'Discount':<10}{'Final':<10}{'Status':<10}{'Method':<10}")
    print_line(130)
    for r in rows:
        print(f"{r[0]:<8}{r[1]:<9}{r[2]:<22}{r[3]:<22}{str(r[4]):<10}{str(r[5]):<10}{str(r[6]):<10}{str(r[7]):<10}{str(r[8]):<10}{str(r[9]):<10}{r[10]:<10}{str(r[11] or '-'):<10}")
    print_line(130)


def choose_bill_id(cursor):
    cursor.execute("""
        SELECT B.BILL_ID, B.APPOINTMENT_ID, P.PATIENT_NAME, D.DOCTOR_NAME,
               B.CONSULTATION_FEE, B.MEDICINE_CHARGES, B.TEST_CHARGES,
               B.GROSS_AMOUNT, B.DISCOUNT, B.FINAL_AMOUNT, B.PAYMENT_STATUS, B.PAYMENT_METHOD
        FROM BILLING B
        JOIN APPOINTMENT A ON B.APPOINTMENT_ID = A.APPOINTMENT_ID
        JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
        JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        ORDER BY B.BILL_ID
    """)
    rows = cursor.fetchall()
    display_bills(rows)
    if not rows:
        return None
    valid = {r[0].upper() for r in rows}
    while True:
        bill_id = input("Enter Bill ID or type 'back': ").strip().upper()
        if is_back(bill_id):
            return None
        if bill_id in valid:
            return bill_id
        print("Invalid Bill ID. Select from the list.")


def generate_bill(conn):
    cursor = conn.cursor()
    print("\nGENERATE BILL")
    print_line()
    print("Completed appointments without bill are shown.")
    appointment_id = choose_appointment_id(cursor, status_filter="Completed", without_bill=True)
    if not appointment_id: return
    cursor.execute("""
        SELECT D.CONSULTATION_FEE
        FROM APPOINTMENT A JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        WHERE A.APPOINTMENT_ID = :appointment_id
    """, {"appointment_id": appointment_id})
    row = cursor.fetchone()
    consultation_fee = float(row[0]) if row else 0.0
    print(f"Consultation Fee: {consultation_fee:.2f}")
    medicine_charges = input_float("Medicine Charges", min_value=0)
    if medicine_charges is None: return
    test_charges = input_float("Test Charges", min_value=0)
    if test_charges is None: return
    discount = input_float("Discount", min_value=0)
    if discount is None: return
    gross_amount = consultation_fee + medicine_charges + test_charges
    final_amount = max(0, gross_amount - discount)

    print("\nCALCULATED BILL AMOUNT")
    print_line(50)
    print(f"Consultation Fee : {consultation_fee:.2f}")
    print(f"Medicine Charges : {medicine_charges:.2f}")
    print(f"Test Charges     : {test_charges:.2f}")
    print(f"Gross Amount     : {gross_amount:.2f}")
    print(f"Discount         : {discount:.2f}")
    print(f"FINAL PAYABLE AMOUNT : {final_amount:.2f}")
    print_line(50)

    paid = input("\nHas the patient paid the bill? (yes/no): ").strip().lower()
    if paid == "yes":
        payment_status = "Paid"
        payment_method = input_payment_method()
        if payment_method is None: return
        payment_date_expr = "SYSDATE"
    else:
        payment_status = "Unpaid"
        payment_method = None
        payment_date_expr = "NULL"

    bill_id = get_next_id(cursor, "BILLING", "BILL_ID", "B", 3)
    try:
        sql = f"""
            INSERT INTO BILLING (
                BILL_ID, APPOINTMENT_ID, BILL_DATE, CONSULTATION_FEE, MEDICINE_CHARGES,
                TEST_CHARGES, GROSS_AMOUNT, DISCOUNT, FINAL_AMOUNT, PAYMENT_STATUS,
                PAYMENT_METHOD, PAYMENT_DATE
            ) VALUES (
                :bill_id, :appointment_id, SYSDATE, :consultation_fee, :medicine_charges,
                :test_charges, :gross_amount, :discount, :final_amount, :payment_status,
                :payment_method, {payment_date_expr}
            )
        """
        cursor.execute(sql, dict(bill_id=bill_id, appointment_id=appointment_id,
                                consultation_fee=consultation_fee, medicine_charges=medicine_charges,
                                test_charges=test_charges, gross_amount=gross_amount, discount=discount,
                                final_amount=final_amount, payment_status=payment_status,
                                payment_method=payment_method))
        conn.commit()
        print(f"\nBill generated successfully. Bill ID: {bill_id}")
    except Exception as exc:
        conn.rollback()
        print("Error while generating bill:", exc)


def view_bills(conn):
    cursor = conn.cursor()
    while True:
        print("\nVIEW BILLS")
        print_line()
        print("1. View All")
        print("2. View Paid Bills")
        print("3. View Unpaid Bills")
        print("4. View by Bill ID")
        print("5. Back")
        choice = input("Enter choice: ").strip()
        base = """
            SELECT B.BILL_ID, B.APPOINTMENT_ID, P.PATIENT_NAME, D.DOCTOR_NAME,
                   B.CONSULTATION_FEE, B.MEDICINE_CHARGES, B.TEST_CHARGES,
                   B.GROSS_AMOUNT, B.DISCOUNT, B.FINAL_AMOUNT, B.PAYMENT_STATUS, B.PAYMENT_METHOD
            FROM BILLING B
            JOIN APPOINTMENT A ON B.APPOINTMENT_ID = A.APPOINTMENT_ID
            JOIN PATIENT_MASTER P ON A.PATIENT_ID = P.PATIENT_ID
            JOIN DOCTOR_MASTER D ON A.DOCTOR_ID = D.DOCTOR_ID
        """
        if choice == "1":
            cursor.execute(base + " ORDER BY B.BILL_ID")
        elif choice == "2":
            cursor.execute(base + " WHERE B.PAYMENT_STATUS = 'Paid' ORDER BY B.BILL_ID")
        elif choice == "3":
            cursor.execute(base + " WHERE B.PAYMENT_STATUS = 'Unpaid' ORDER BY B.BILL_ID")
        elif choice == "4":
            bill_id = choose_bill_id(cursor)
            if not bill_id: continue
            cursor.execute(base + " WHERE B.BILL_ID = :bill_id", {"bill_id": bill_id})
        elif choice == "5":
            break
        else:
            print("Invalid choice.")
            continue
        display_bills(cursor.fetchall())
        pause()


def update_payment_status(conn):
    cursor = conn.cursor()
    print("\nUPDATE PAYMENT STATUS")
    print_line()
    bill_id = choose_bill_id(cursor)
    if not bill_id: return
    print("1. Paid")
    print("2. Unpaid")
    status = {"1": "Paid", "2": "Unpaid"}.get(input("Enter choice: ").strip())
    if not status:
        print("Invalid choice.")
        return
    method = None
    date_expr = "NULL"
    if status == "Paid":
        method = input_payment_method()
        if method is None: return
        date_expr = "SYSDATE"
    try:
        sql = f"""
            UPDATE BILLING
            SET PAYMENT_STATUS = :status,
                PAYMENT_METHOD = :method,
                PAYMENT_DATE = {date_expr}
            WHERE BILL_ID = :bill_id
        """
        cursor.execute(sql, {"status": status, "method": method, "bill_id": bill_id})
        conn.commit()
        print("Payment status updated successfully.")
    except Exception as exc:
        conn.rollback()
        print("Error:", exc)


def billing_management_menu(conn):
    while True:
        print("\nBILLING MANAGEMENT")
        print_line()
        print("1. Generate Bill")
        print("2. View Bills")
        print("3. Update Payment Status")
        print("4. Back to Main Menu")
        choice = input("Enter choice: ").strip()
        if choice == "1": generate_bill(conn); pause()
        elif choice == "2": view_bills(conn)
        elif choice == "3": update_payment_status(conn); pause()
        elif choice == "4": break
        else: print("Invalid choice.")

"""Hospital Management System - Main Menu."""

from config.db_connection import get_connection
from utils.input_helper import print_line
from modules.doctor_management import doctor_management_menu
from modules.patient_management import patient_management_menu
from modules.appointment_management import appointment_management_menu
from modules.consultation_management import consultation_management_menu
from modules.billing_management import billing_management_menu
from modules.reports import reports_menu
from modules.import_export import import_export_menu


def main_menu():
    try:
        conn = get_connection()
        print("Database connected successfully.")
    except Exception as exc:
        print("Database connection error:", exc)
        print("Update config/db_connection.py with your Oracle DB details and try again.")
        return

    try:
        while True:
            print("\nHOSPITAL MANAGEMENT SYSTEM")
            print_line()
            print("1. Doctor Management")
            print("2. Patient Management")
            print("3. Appointment Management")
            print("4. Consultation Management")
            print("5. Billing Management")
            print("6. Reports")
            print("7. Import / Export")
            print("8. Exit")
            choice = input("Enter choice: ").strip()

            if choice == "1":
                doctor_management_menu(conn)
            elif choice == "2":
                patient_management_menu(conn)
            elif choice == "3":
                appointment_management_menu(conn)
            elif choice == "4":
                consultation_management_menu(conn)
            elif choice == "5":
                billing_management_menu(conn)
            elif choice == "6":
                reports_menu(conn)
            elif choice == "7":
                import_export_menu(conn)
            elif choice == "8":
                print("Thank you. Exiting application.")
                break
            else:
                print("Invalid choice. Please try again.")
    finally:
        conn.close()


if __name__ == "__main__":
    main_menu()

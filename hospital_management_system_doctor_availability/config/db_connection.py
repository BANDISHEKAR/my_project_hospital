"""Oracle database connection file.

Update USERNAME, PASSWORD, HOST, PORT, and SERVICE_NAME with your Oracle DB details.
No .env file is used, because this project keeps connection configuration here.
"""

import oracledb

USERNAME = "team40_shekar"
PASSWORD = "team40_shekar"
HOST = "ec2-3-111-0-185.ap-south-1.compute.amazonaws.com"
PORT = 1521
SERVICE_NAME = "orcl"

DSN = f"{HOST}:{PORT}/{SERVICE_NAME}"


def get_connection():
    """Return an Oracle DB connection."""
    return oracledb.connect(user=USERNAME, password=PASSWORD, dsn=DSN)


def test_connection():
    """Test DB connectivity."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 'Oracle connection successful' FROM dual")
        print(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return True
    except Exception as exc:
        print("Database connection failed:", exc)
        return False


if __name__ == "__main__":
    test_connection()

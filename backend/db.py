import os
import mysql.connector


def get_db_connection():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD environment variable is not set!")
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=password,
        database=os.environ.get("DB_NAME", "crop_system"),
    )

import os 
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST","localhost"),
        port=os.getenv("DB_PORT","5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def create_table():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    instructor VARCHAR(100) NOT NULL,
                    duration INTEGER NOT NULL CHECK (duration > 0)
                    );
                    """)

            
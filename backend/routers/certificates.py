from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter(tags=["Certificates"])

@router.get("/certificates")
def get_certificates(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, course_id, issued_at
                FROM certificates
                WHERE user_id = %s;
            """, (user_id,))

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "course_id": row[1],
                    "issued_at": row[2],
                }
                for row in rows
            ]
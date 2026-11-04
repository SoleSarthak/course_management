from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter(tags=["Enrollments"])

@router.post("/enrollments")
def enroll_in_course(user_id: int, course_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO enrollments (user_id, course_id)
                VALUES (%s, %s)
                RETURNING id;
            """, (user_id, course_id))

            enrollment = cursor.fetchone()

            return {
                "message": "Enrolled successfully",
                "enrollment_id": enrollment[0],
            }

@router.get("/enrollments")
def get_my_enrollments(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.instructor, c.duration
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id
                WHERE e.user_id = %s;
            """, (user_id,))

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "instructor": row[2],
                    "duration": row[3],
                }
                for row in rows
]
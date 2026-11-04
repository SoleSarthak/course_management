from fastapi import APIRouter, HTTPException
from backend.database import get_connection

router = APIRouter(tags=["Lessons"])

@router.post("/modules/{module_id}/lessons")
def create_lesson(module_id: int,title: str,lesson_order: int,):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO lessons (module_id, title, lesson_order)
                VALUES (%s, %s, %s)
                RETURNING id, title, lesson_order;
            """, (module_id, title, lesson_order))

            lesson = cursor.fetchone()

            return {
                "message": "Lesson created successfully",
                "lesson_id": lesson[0],
                "title": lesson[1],
                "lesson_order": lesson[2],
            }

@router.get("/modules/{module_id}/lessons")
def get_lessons(module_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title
                FROM lessons
                WHERE module_id = %s
                ORDER BY id;
            """, (module_id,))

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                }
                for row in rows ]

@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, module_id, title
                FROM lessons
                WHERE id = %s;
            """, (lesson_id,))

            lesson = cursor.fetchone()

            if lesson is None:
                raise HTTPException(
                    status_code=404,
                    detail="Lesson not found", )
            return {
                "id": lesson[0],
                "module_id": lesson[1],
                "title": lesson[2],
            }
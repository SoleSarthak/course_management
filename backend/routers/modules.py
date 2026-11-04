from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter(tags=["Modules"])

@router.post("/courses/{course_id}/modules")
def create_module(course_id: int,title: str,module_order: int,):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO modules (course_id, title, module_order)
                VALUES (%s, %s, %s)
                RETURNING id, title, module_order;
            """, (course_id, title, module_order))

            module = cursor.fetchone()

            return {
                "message": "Module created successfully",
                "module_id": module[0],
                "course_id": course_id,
                "title": module[1],
                "module_order": module[2],
            }


@router.get("/courses/{course_id}/modules")
def get_modules(course_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title
                FROM modules
                WHERE course_id = %s
                ORDER BY id;
            """, (course_id,))

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                }
                for row in rows ]
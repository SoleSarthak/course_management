from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter(tags=["Progress"])

@router.post("/progress/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int, user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO progress (
                    user_id,
                    lesson_id,
                    completed,
                    completed_at
                )
                VALUES (%s, %s, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, lesson_id)
                DO UPDATE SET
                completed = TRUE,
                completed_at = CURRENT_TIMESTAMP
                RETURNING id;""",
                (user_id, lesson_id))

            progress = cursor.fetchone()

            return {
                "message": "Lesson completed",
                "progress_id": progress[0],
                "lesson_id": lesson_id,
            }


@router.get("/progress/courses/{course_id}")
def get_progress_for_course(course_id: int, user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                COUNT(l.id),
                COUNT(p.lesson_id)
                FROM modules m
                JOIN lessons l ON l.module_id = m.id
                LEFT JOIN progress p
                    ON p.lesson_id = l.id
                    AND p.user_id = %s
                    AND p.completed = TRUE
                WHERE m.course_id = %s;
            """, (user_id, course_id))

            result = cursor.fetchone()

            total_lessons = result[0]
            completed_lessons = result[1]

            return {
                "course_id": course_id,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "progress": (
                    round(completed_lessons / total_lessons * 100, 2)
                    if total_lessons
                    else 0 ),
            }
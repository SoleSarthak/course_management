from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.database import get_connection

router = APIRouter(prefix="/courses",tags=["Courses"])

class Course(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    instructor: str = Field(min_length=1, max_length=100)
    duration: int = Field(gt=0)

@router.get("/mine")
def get_my_courses(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.instructor, c.duration
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id
                WHERE e.user_id = %s
                ORDER BY c.id;
            """, (user_id,))

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "instructor": row[2],
                    "duration": row[3],
                }
                for row in rows ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(course: Course):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO courses (title, instructor, duration)
                VALUES (%s, %s, %s)
                RETURNING id, title, instructor, duration;
            """, (
                course.title,
                course.instructor,
                course.duration, ))

            row = cursor.fetchone()

            return {
                "id": row[0],
                "title": row[1],
                "instructor": row[2],
                "duration": row[3],
            }


@router.get("")
def get_courses():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, instructor, duration
                FROM courses
                ORDER BY id;
            """)

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


@router.get("/{course_id}")
def get_course(course_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, instructor, duration
                FROM courses
                WHERE id = %s;
            """, (course_id,))

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found",
                )

            return {
                "id": row[0],
                "title": row[1],
                "instructor": row[2],
                "duration": row[3],
            }


@router.put("/{course_id}")
def update_course(course_id: int, course: Course):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE courses
                SET title = %s, instructor = %s, duration = %s
                WHERE id = %s
                RETURNING id, title, instructor, duration;
            """, (
                course.title,
                course.instructor,
                course.duration,
                course_id, ))

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found",)

            return {
                "id": row[0],
                "title": row[1],
                "instructor": row[2],
                "duration": row[3],
            }


@router.delete("/{course_id}")
def delete_course(course_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM courses
                WHERE id = %s
                RETURNING id;
            """, (course_id,))

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found", )

            return {
                "message": "Course deleted successfully",
                "id": row[0],
            }
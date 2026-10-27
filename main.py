from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from database import create_table, get_connection



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield



app = FastAPI(
    title="course management api",
    lifespan=lifespan,
)



class Course(BaseModel):
    title: str = Field(min_length=1,max_length=150)
    instructor: str = Field(min_length=1, max_length=100)
    duration: int = Field(gt=0)

@app.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(course: Course):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO courses (title, instructor, duration)
                VALUES (%s,%s,%s)
                RETURNING id, title, instructor, duration;
                """,
                (course.title, course.instructor, course.duration),
            )
            row = cursor.fetchone()

            return dict(zip(
                ["id", "title", "instructor", "duration"],
                row,
            )
            )


@app.get("/courses")
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
                dict(zip(
                    ["id", "title", "instructor", "duration"],
                    row,
                ))
                for row in rows
            ]        


@app.get("/courses/{course_id}")
def get_course(course_id: int):
     with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, instructor, duration
                FROM courses
                WHERE id = %s;
                """,
                (course_id,),
            )

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found",
                )

            return dict(zip(
                ["id", "title", "instructor", "duration"],
                row,
            ))


@app.put("/courses/{course_id}")
def update_course(course_id: int, course: Course):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE courses
                SET title = %s, instructor = %s, duration = %s
                WHERE id = %s
                RETURNING id, title, instructor, duration;
                """,
                (
                    course.title,
                    course.instructor,
                    course.duration,
                    course_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found",
                )

            return dict(zip(
                ["id", "title", "instructor", "duration"],
                row,
            ))



@app.delete("/courses/{course_id}")
def delete_course(course_id: int):
     with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM courses
                WHERE id = %s
                RETURNING id;
                """,
                (course_id,),
            )

            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found",
                )

            return {
                "message": "Course deleted successfully",
                "id": row[0],
            }

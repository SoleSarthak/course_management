from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status , APIRouter
from pydantic import BaseModel, Field , EmailStr

from database import create_table, get_connection

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from passlib.context import CryptContext




@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield



app = FastAPI(
    title="course management api",
    lifespan=lifespan,
)

course_router = APIRouter(prefix="/courses", tags=["Courses"])

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR.parent / "static"),
    name="static",
)


@app.get("/")
def home():
    return FileResponse(BASE_DIR.parent / "static" / "index.html")



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
            ))


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
                for row in rows]        


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
                ),)

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
                (course_id,),)

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



#auth

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/register")
def register(user: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (user.email,))

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Email already registered")

        hashed_password = pwd_context.hash(user.password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING id, name, email, role
            """,
            (user.name, user.email, hashed_password))

        new_user = cursor.fetchone()
        conn.commit()

        return {
            "message": "Registration successful",
            "user": new_user
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Something went wrong")

    finally:
        cursor.close()
        conn.close()


@app.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, email, password, role
            FROM users
            WHERE email = %s
            """,
            (user.email,))

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password")

        if not pwd_context.verify(
            user.password,
            existing_user["password"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password")

        return {
            "message": "Login successful",
            "user": {
                "id": existing_user["id"],
                "name": existing_user["name"],
                "email": existing_user["email"],
                "role": existing_user["role"]
            }
        }

    finally:
        cursor.close()
        conn.close()


@app.get("/me")
def get_current_user():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, email, role
            FROM users
            WHERE id = %s
            """,
            (1,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found")

        return {
            "message": "Current user details",
            "user": user}

    finally:
        cursor.close()
        conn.close()



#courses

@course_router.get("/mine")
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

            courses = cursor.fetchall()

            return [
                {
                    "id": course[0],
                    "title": course[1],
                    "instructor": course[2],
                    "duration": course[3],
                }
                for course in courses
            ]



app.include_router(course_router)


#certificates

@app.get("/certificate")
def get_my_certificates(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cert.id, c.title, cert.issued_at
                FROM certificates cert
                JOIN courses c ON c.id = cert.course_id
                WHERE cert.user_id = %s
                ORDER BY cert.issued_at DESC;
            """, (user_id,))

            certificates = cursor.fetchall()

            return [
                {
                    "certificate_id": certificate[0],
                    "course_title": certificate[1],
                    "issued_at": certificate[2],
                }
                for certificate in certificates
            ]


# #enrollments

@app.post("/enrollments")
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
                "enrollment_id": enrollment[0]
            }


@app.get("/enrollments")
def get_my_enrollments(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.instructor, c.duration
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id
                WHERE e.user_id = %s;
            """, (user_id,))

            enrollments = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "instructor": row[2],
                    "duration": row[3]
                }
                for row in enrollments
            ]

#lessons
@app.post("/modules/{module_id}/lessons")
def create_lesson(module_id: int, title: str, lesson_order: int):
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
                "lesson_order": lesson[2]
            }

@app.get("/modules/{module_id}/lessons")
def get_lessons(module_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title
                FROM lessons
                WHERE module_id = %s
                ORDER BY id;
            """, (module_id,))

            lessons = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1]
                }
                for row in lessons]


@app.get("/lessons/{lesson_id}")
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
                    detail="Lesson not found")

            return {
                "id": lesson[0],
                "module_id": lesson[1],
                "title": lesson[2]
            }


#modules

@app.post("/courses/{course_id}/modules")
def create_module(course_id: int, title: str, module_order: int):
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
                "module_order": module[2]
            }


@app.get("/courses/{course_id}/modules")
def get_modules(course_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title
                FROM modules
                WHERE course_id = %s
                ORDER BY id;
            """, (course_id,))

            modules = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1]
                }
                for row in modules
            ]


# progress

@app.post("/progress/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int,):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO progress (user_id, lesson_id, completed, completed_at)
                VALUES (%s, %s, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, lesson_id)
                DO UPDATE SET
                    completed = TRUE,
                    completed_at = CURRENT_TIMESTAMP
                RETURNING id;
            """, ( lesson_id))

            progress = cursor.fetchone()

            return {
                "message": "Lesson completed",
                "progress_id": progress[0],
                "lesson_id": lesson_id
            }


@app.get("/progress/courses/{course_id}")
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
                    if total_lessons else 0)
            }


#certificates

@app.get("/certificates")
def get_my_certificates(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, course_id, issued_at
                FROM certificates
                WHERE user_id = %s;
            """, (user_id,))

            certificates = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "course_id": row[1],
                    "issued_at": row[2]
                }
                for row in certificates
            ]
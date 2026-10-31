from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field , EmailStr

from backend.database import create_table, get_connection

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
            (user.email,)
        )

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
            (user.name, user.email, hashed_password)
        )

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
            detail="Something went wrong"
        )

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
            (user.email,)
        )

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not pwd_context.verify(
            user.password,
            existing_user["password"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

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
            (1,)
        )

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

app.get("/")
def get_courses():
    return {
        "message":"list of all courses"
    }

app.get("/mine")
def get_my_courses():
    return {
        "message":"my courses"
    }

app.get("/{course_id}")
def get_course(course_id:int):
    return {
        "message":"course details",
        "course_id": course_id
    }

app.get("/{course_id}/outline")
def get_course_outline(course_id:int):
    return {
        "message":"course outline",
        "course_id":course_id
    }

app.post("/")
def create_course():
    return {
        "message":"course created successfully"
    }


@app.put("/{course_id}")
def update_course(course_id: int):
    return {
        "message": "Course updated successfully",
        "course_id": course_id
    }

@app.delete("/{course_id}")
def delete_course(course_id: int):
    return {
        "message": "Course deleted successfully",
        "course_id": course_id
    }


#certificates

@app.get("certificate")
def get_my_certificates():
    return{
        "message":"certificates received"
    }


#enrollments

@app.post()
def enroll_in_course():
    return {
        "message":"enrolled"
    }

@app.get("")
def get_my_enrollments():
    return {
        "message":"enrolled courses"
    }

#lessons
@app.post("/modules/{module_id}/lessons")
def create_lesson():
    return {"message": "Lesson created successfully"}


@app.get("/modules/{module_id}/lessons")
def get_lessons(module_id: int):
    return {"message": "List of lessons"}


@app.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int):
    return {
        "message": "Lesson details",
        "lesson_id": lesson_id
    }


#modules

@app.post("/courses/{course_id}/modules")
def create_module(course_id:int):
    return {
        "message": "Module created successfully",
        "course_id": course_id
    }


@app.get("/courses/{course_id}/modules")
def get_modules(course_id: int):
    return {
        "message": "List of modules",
        "course_id": course_id
    }


#progress

@app.post("/progress/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int):
    return {
        "message": "Lesson completed",
        "lesson_id": lesson_id
    }


@app.get("/progress/courses/{course_id}")
def get_progress_for_course(course_id: int):
    return {
        "message": "Course progress",
        "course_id": course_id
    }


#quizzes

@app.post("/quizzes/courses/{course_id}")
def create_quiz(course_id: int):
    return {
        "message": "Quiz created successfully",
        "course_id": course_id
    }


@app.get("/quizzes/courses/{course_id}")
def get_course_quizzes(course_id: int):
    return {
        "message": "List of course quizzes",
        "course_id": course_id
    }


@app.post("/quizzes/{quiz_id}/questions")
def create_question(quiz_id: int):
    return {
        "message": "Question created successfully",
        "quiz_id": quiz_id
    }


@app.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int):
    return {
        "message": "Quiz details",
        "quiz_id": quiz_id
    }


@app.get("/quizzes/{quiz_id}/questions")
def get_questions(quiz_id: int):
    return {
        "message": "List of quiz questions",
        "quiz_id": quiz_id
    }


@app.get("/quizzes/{quiz_id}/attempts")
def get_my_attempts(quiz_id: int):
    return {
        "message": "Quiz attempts",
        "quiz_id": quiz_id
    }


@app.post("/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: int):
    return {
        "message": "Quiz submitted",
        "quiz_id": quiz_id
    }

#certificates

@app.get("/certificates")
def get_my_certificates():
    return {
        "message": "My certificates"
    }
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from backend.database import get_connection

router = APIRouter(tags=["Auth"])

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto", )

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (user.email,),
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Email already registered", )

        hashed_password = pwd_context.hash(user.password)

        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING id, name, email, role;
        """, (
            user.name,
            user.email,
            hashed_password, ))

        new_user = cursor.fetchone()
        conn.commit()

        return {
            "message": "Registration successful",
            "user": {
                "id": new_user[0],
                "name": new_user[1],
                "email": new_user[2],
                "role": new_user[3],
            }, }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Something went wrong", )

    finally:
        cursor.close()
        conn.close()


@router.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, email, password, role
            FROM users
            WHERE email = %s;
        """, (user.email,))

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password", )

        if not pwd_context.verify(
            user.password,
            existing_user[3], ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password", )

        return {
            "message": "Login successful",
            "user": {
                "id": existing_user[0],
                "name": existing_user[1],
                "email": existing_user[2],
                "role": existing_user[4],
            }, }

    finally:
        cursor.close()
        conn.close()


@router.get("/me")
def get_current_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, email, role
            FROM users
            WHERE id = %s;
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found", )

        return {
            "message": "Current user details",
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3],
            }, }

    finally:
        cursor.close()
        conn.close()
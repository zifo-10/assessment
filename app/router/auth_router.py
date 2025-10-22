# app/auth/routes.py

from fastapi import APIRouter, HTTPException, status
from app.auth.security import hash_password, verify_password, create_access_token
from app.container import mongo_client
from app.schema.user_schema import UserCreate, UserLogin, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=Token)
def signup(user: UserCreate):
    if mongo_client.find_one("users", {"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # ✅ Hash once
    hashed_pw = hash_password(user.password)

    new_user = {
        "email": user.email,
        "hashed_password": hashed_pw,
        "role": user.role.value,
    }
    mongo_client.insert_one("users", new_user)

    # ✅ Create token
    access_token = create_access_token({"sub": user.email, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = mongo_client.find_one("users", {"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ Verify password (do NOT hash again)
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"]})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=db_user["role"]
    )

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DB, CurrentUser
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: DB):
    if auth_service.get_by_email(db, body.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email đã tồn tại")
    return auth_service.create_user(db, body)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: DB):
    user = auth_service.authenticate(db, body.email, body.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu")
    return TokenOut(access_token=auth_service.issue_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user

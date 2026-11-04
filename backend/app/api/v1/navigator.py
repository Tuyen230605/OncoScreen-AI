"""Navigator công khai: người dùng chưa đăng nhập vẫn tư vấn được; token phiên thay cho tài khoản."""

from ai_core.schemas import CancerType, EducationContent, Questionnaire
from fastapi import APIRouter, Request, status

from app.api.deps import DB, ConsultToken, OptionalUser, Patient
from app.schemas.navigator import ConsultationCreated, ConsultationOut, NavigatorMessageIn, ServiceOut
from app.services import agent_service, navigator_service

router = APIRouter()
catalog_router = APIRouter()


@router.get("/questionnaire", response_model=Questionnaire)
def questionnaire():
    return agent_service.navigator_questionnaire()


@router.post("/consultations", response_model=ConsultationCreated, status_code=status.HTTP_201_CREATED)
def create_consultation(request: Request, db: DB, user: OptionalUser):
    # Theo tài khoản nếu đăng nhập, ngược lại theo IP kết nối (không tin X-Forwarded-For: client tự đặt được).
    key = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    navigator_service.check_create_rate(key)
    return navigator_service.create(db, user)


@router.get("/consultations/{consult_id}", response_model=ConsultationOut)
def get_consultation(consult_id: str, db: DB, user: OptionalUser, token: ConsultToken = None):
    return navigator_service.to_out(navigator_service.authorize(db, consult_id, token, user))


@router.post("/consultations/{consult_id}/messages", response_model=ConsultationOut)
async def post_message(
    consult_id: str, body: NavigatorMessageIn, db: DB, user: OptionalUser, token: ConsultToken = None
):
    consult = navigator_service.authorize(db, consult_id, token, user)
    return await navigator_service.post_message(db, consult, body)


@router.post("/consultations/{consult_id}/claim", response_model=ConsultationOut)
def claim(consult_id: str, user: Patient, db: DB, token: ConsultToken = None):
    return navigator_service.claim(db, consult_id, token, user)


@catalog_router.get("/services", response_model=list[ServiceOut])
def services():
    return agent_service.list_services()


@catalog_router.get("/education")
def list_topics() -> list[dict]:
    from ai_core.api import CANCER_LABEL_VI

    return [
        {"cancer_type": c.value, "title": f"Tầm soát {CANCER_LABEL_VI[c]}"} for c in CancerType if c != CancerType.other
    ]


@catalog_router.get("/education/{cancer_type}", response_model=EducationContent)
async def get_topic(cancer_type: CancerType):
    return await agent_service.get_education(cancer_type)

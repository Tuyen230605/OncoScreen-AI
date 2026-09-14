from ai_core.schemas import CancerType, EducationContent
from fastapi import APIRouter

from app.services import agent_service

router = APIRouter()


@router.get("")
def list_topics() -> list[dict]:
    return [
        {"cancer_type": c.value, "title": f"Tầm soát ung thư {c.value}"} for c in CancerType if c != CancerType.other
    ]


@router.get("/{cancer_type}", response_model=EducationContent)
async def get_topic(cancer_type: CancerType):
    return await agent_service.get_education(cancer_type)

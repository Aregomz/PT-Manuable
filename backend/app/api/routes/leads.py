from fastapi import APIRouter

from app.api.dependencies import CommercialUser
from app.db import get_connection
from app.repositories.lead_repository import LeadRepository
from app.schemas.leads import CapturedLeadsResponse
from app.services.lead_service import LeadService

router = APIRouter(prefix="/api/admin/leads", tags=["leads"])


@router.get("", response_model=CapturedLeadsResponse)
def get_captured_leads(_: CommercialUser) -> CapturedLeadsResponse:
    with get_connection() as connection:
        result = LeadService(LeadRepository(connection)).list_captured_leads()
    return CapturedLeadsResponse.model_validate(result)


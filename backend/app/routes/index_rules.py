from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.index_rules import IndexRule, IndexRuleService, get_index_rule_service
from app.utils.logging import logger


class IndexRuleResponse(BaseModel):
    name: str
    pattern: str
    description: str = ""
    enabled: bool = True

    @classmethod
    def from_dataclass(cls, rule: IndexRule) -> "IndexRuleResponse":
        return cls(**rule.to_dict())


router = APIRouter(prefix="/index-rules", tags=["index-rules"])


@router.get("/", response_model=List[IndexRuleResponse])
async def list_index_rules(
    service: IndexRuleService = Depends(get_index_rule_service),
):
    try:
        rules = await service.list_rules()
    except RuntimeError as exc:
        # Missing optional dependency or database unreachable
        logger.error("Failed to load index rules: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unexpected error while loading index rules: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load index rules",
        ) from exc

    return [IndexRuleResponse.from_dataclass(rule) for rule in rules]

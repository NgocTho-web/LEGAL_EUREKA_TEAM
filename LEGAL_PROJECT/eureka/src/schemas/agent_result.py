from pydantic import BaseModel, Field
from typing import List
from src.schemas.citation import LegalCitation

class AgentResult(BaseModel):
    agent_name: str = Field(..., description="Tên Agent (LegalText / Procedure / Case)")
    draft_answer: str = Field(..., description="Câu trả lời nháp từ Agent")
    citations: List[LegalCitation] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0)
    status: str = Field("SUCCESS", description="SUCCESS | TIMEOUT | ERROR")
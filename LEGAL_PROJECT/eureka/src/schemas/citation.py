from pydantic import BaseModel, Field
from typing import Optional

class LegalCitation(BaseModel):
    document_id: str = Field(..., description="Mã văn bản (VD: 31/2024/QH15)")
    document_title: str = Field(..., description="Tên văn bản (VD: Luật Đất đai 2024)")
    article: str = Field(..., description="Mã Điều (VD: Điều 188)")
    clause: Optional[str] = Field(None, description="Khoản (VD: Khoản 1)")
    point: Optional[str] = Field(None, description="Điểm (VD: Điểm a)")
    content_snippet: str = Field(..., description="Đoạn trích dẫn nội dung gốc")
    is_active: bool = Field(True, description="Còn hiệu lực pháp lý hay không")
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
from src.orchestration.crew_pipeline import run_parallel_legal_crew
from src.harness.citation_verifier import CitationVerifier

router = APIRouter()
verifier = CitationVerifier()

async def chat_event_generator(query: str):
    yield f"data: {json.dumps({'status': 'Kích hoạt Agent A quét Luật gốc...'}, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0.2)

    yield f"data: {json.dumps({'status': 'Song song chạy Agent B (Nghị định) & Agent C (Án lệ)...'}, ensure_ascii=False)}\n\n"

    # Chạy CrewAI trong thread riêng để không block luồng SSE của FastAPI
    final_answer = await asyncio.to_thread(run_parallel_legal_crew, query)

    # Kiểm định trích dẫn
    verification = verifier.verify_answer_citations(final_answer)

    yield f"data: {json.dumps({'answer': final_answer, 'verification': verification}, ensure_ascii=False)}\n\n"

@router.post("/chat/stream")
async def chat_stream(payload: dict):
    user_query = payload.get("message", "")
    return StreamingResponse(chat_event_generator(user_query), media_type="text/event-stream")
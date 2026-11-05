
import re

from crewai import Crew, Task, Process

from src.agents.crew_agents import (
    legal_text_agent,
    procedure_agent,
    case_agent,
    aggregator_agent,
)
from src.agents.safe_legal_formatter import (
    format_safe_legal_answer,
)

from src.agents.mcp.servers.graph_server import (
    search_legal_articles,
)

from src.agents.citation_verifier import (
    verify_legal_answer,
)


def extract_article_id(source_text: str):
    """Lấy ID điều luật từ kết quả Neo4j."""
    match = re.search(
        r"^ID:\s*(vn_law_[a-zA-Z0-9_]+)",
        source_text,
        flags=re.MULTILINE,
    )
    return match.group(1) if match else None


def run_legal_crew(question: str) -> dict:
    """
    Xử lý câu hỏi pháp luật bằng 4 Agent.

    Trả về:
    {
        "question": ...,
        "answer": ...,
        "article_id": ...,
        "verified": ...,
        "errors": ...
    }
    """

    question = question.strip()

    if not question:
        return {
            "question": question,
            "answer": "Vui lòng nhập câu hỏi pháp luật.",
            "article_id": None,
            "verified": False,
            "errors": ["Câu hỏi trống."],
        }

    # 1. Tra cứu KG
    source_text = search_legal_articles(question)
    article_id = extract_article_id(source_text)

    if not article_id:
        return {
            "question": question,
            "answer": (
                "Chưa tìm thấy điều luật phù hợp "
                "trong Knowledge Graph. "
                "Vui lòng cung cấp số điều luật "
                "và tên văn bản cụ thể."
            ),
            "article_id": None,
            "verified": False,
            "errors": ["Không tìm thấy ID điều luật."],
        }

    # 2. Agent A

    task_a = Task(
        description=(
            f"Câu hỏi: {question}\n"
            f"ID điều luật: {article_id}\n"
            "BẮT BUỘC gọi get_article_ocr_text "
            "với đúng article_id đã cung cấp.\n"
            "Sử dụng nội dung OCR được truy xuất "
            "để xác định chủ đề của điều luật.\n"
            "Không được tự tạo hoặc sửa nội dung OCR.\n"
            "Phải nêu rõ OCR chưa được xác minh.\n"
            "Không được khẳng định hiệu lực hiện hành."
        ),
        expected_output=(
            "Tên điều luật, ID, nội dung OCR liên quan, "
            "các khoản, điểm và trạng thái xác minh."
        ),
        agent=legal_text_agent,
    )

    # 3. Agent B
    task_b = Task(
        description=(
            f"ID điều luật chính xác: {article_id}\n"
            "Gọi get_guiding_decrees bằng đúng ID này. "
            "Không suy đoán văn bản hướng dẫn."
        ),
        expected_output=(
            "Văn bản hướng dẫn được xác minh "
            "hoặc thông báo thiếu dữ liệu."
        ),
        agent=procedure_agent,
        context=[task_a],
    )

    # 4. Agent C
    task_c = Task(
        description=(
            f"ID điều luật chính xác: {article_id}\n"
            "Gọi get_related_cases bằng đúng ID này. "
            "Không tự tạo án lệ hoặc bản án."
        ),
        expected_output=(
            "Án lệ được xác minh "
            "hoặc thông báo thiếu dữ liệu."
        ),
        agent=case_agent,
        context=[task_a],
    )

    # 5. Aggregator
    task_d = Task(
        description=(
            f"Câu hỏi: {question}\n"
            f"ID bắt buộc: {article_id}\n"
            "Tổng hợp kết quả Agent A, B, C.\n"
            "Phải dẫn chính xác ID điều luật.\n"
            "Giữ lại các khoản đã truy xuất.\n"
            "Không tự tạo nội dung pháp luật.\n"
            "Không dùng placeholder.\n"
            "Không khẳng định hiệu lực hiện hành "
            "nếu chưa có nguồn xác minh.\n"
            "Nêu rõ những dữ liệu còn thiếu."
        ),
        expected_output=(
            "Câu trả lời tiếng Việt có trích dẫn, "
            "các khoản và giới hạn dữ liệu."
        ),
        agent=aggregator_agent,
        context=[task_a, task_b, task_c],
    )

    # 6. Chạy CrewAI
    crew = Crew(
        agents=[
            legal_text_agent,
            procedure_agent,
            case_agent,
            aggregator_agent,
        ],
        tasks=[task_a, task_b, task_c, task_d],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    answer = str(result)

    # 7. Kiểm chứng
    verification = verify_legal_answer(
        answer=answer,
        article_id=article_id,
        source_text=source_text,
    )


    # 8. Không xuất trực tiếp nội dung LLM trong bản demo.
    # Chỉ xuất dữ liệu cấu trúc đã truy xuất từ KG.
    answer = format_safe_legal_answer(
        source_text=source_text,
        article_id=article_id,
    )

    return {
        "question": question,
        "answer": answer,
        "article_id": article_id,
        "verified": False,
        "errors": verification["errors"],
    }


from src.agents.mcp.servers.graph_server import get_article_ocr_data


def format_safe_legal_answer(
    source_text: str,
    article_id: str
) -> str:
    """
    Hiển thị nội dung OCR từ Knowledge Graph Neo4j.

    Giữ nguyên chữ OCR đã lưu, không dùng LLM
    để tự tạo hoặc sửa nội dung pháp luật.
    """

    data = get_article_ocr_data(article_id)

    if not data:
        return (
            "Không tìm thấy nội dung điều luật "
            "trong Knowledge Graph."
        )

    article_content = data.get("content") or ""
    source_file = data.get("source_file") or "Chưa xác định"
    status = data.get("verification_status") or "unknown"
    start_page = data.get("start_page")
    end_page = data.get("end_page")

    output = [
        "## A. Văn bản pháp luật",
        "",
        f"**Điều luật:** {data.get('name') or 'Chưa xác định'}",
        f"**ID:** `{article_id}`",
        f"**Nguồn PDF:** `{source_file}`",
        f"**Trạng thái OCR:** `{status}`",
    ]

    if start_page is not None:
        page_info = str(start_page)

        if end_page is not None and end_page != start_page:
            page_info += f"–{end_page}"

        output.append(f"**Trang PDF:** {page_info}")

    output.extend([
        "",
        "### Nội dung OCR cấp Điều",
        "",
        article_content or "Chưa có nội dung OCR.",
        "",
        "### Cấu trúc Khoản và Điểm",
    ])

    clauses = data.get("clauses") or []

    for clause in clauses:
        clause_id = clause.get("id") or ""
        clause_number = clause_id.rsplit("_clause_", 1)[-1]

        output.extend([
            "",
            f"#### Khoản {clause_number}",
            "",
            clause.get("content") or "Chưa có nội dung OCR.",
            "",
            f"ID: `{clause_id}`",
        ])

        for point in clause.get("points") or []:
            point_id = point.get("id") or ""
            point_letter = point_id.rsplit("_point_", 1)[-1]

            output.extend([
                "",
                f"**Điểm {point_letter}**",
                "",
                point.get("content") or "Chưa có nội dung OCR.",
                "",
                f"ID: `{point_id}`",
            ])

    output.extend([
        "",
        "## B. Văn bản hướng dẫn",
        "",
        "Chưa có dữ liệu liên kết nghị định hoặc "
        "thông tư được xác minh trong Knowledge Graph.",
        "",
        "## C. Án lệ và bản án",
        "",
        "Chưa có dữ liệu liên kết án lệ hoặc "
        "bản án được xác minh trong Knowledge Graph.",
        "",
        "## D. Giới hạn dữ liệu",
        "",
        "**Cảnh báo:** Nội dung trên được trích xuất "
        "bằng OCR và chưa được đối chiếu, xác minh "
        "đầy đủ với văn bản pháp luật gốc.",
        "",
        "Dữ liệu thuộc Luật Đất đai 2013. "
        "Không coi đây là quy định pháp luật hiện hành. "
        "Cần kiểm tra văn bản đang có hiệu lực "
        "và quy định chuyển tiếp trước khi áp dụng.",
    ])

    return "\n".join(output)

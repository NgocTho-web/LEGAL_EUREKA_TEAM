
import re


def verify_legal_answer(
    answer: str,
    article_id: str,
    source_text: str
) -> dict:
    """
    Kiểm tra sơ bộ câu trả lời của Aggregator.

    Không coi đây là kiểm chứng pháp lý đầy đủ.
    """

    errors = []

    # 1. Kiểm tra ID điều luật
    if article_id not in source_text:
        errors.append(
            "Không tìm thấy ID điều luật trong nguồn."
        )

    if article_id not in answer:
        errors.append(
            "Câu trả lời không dẫn ID điều luật."
        )

    # 2. Chặn placeholder
    placeholders = [
        r"\[Nội dung khoản\s*\d+\]",
        r"\[Nội dung điều luật\]",
        r"\[Chưa cập nhật\]",
    ]

    for pattern in placeholders:
        if re.search(pattern, answer, re.IGNORECASE):
            errors.append(
                "Câu trả lời chứa nội dung placeholder."
            )
            break

    # 3. Chặn khẳng định hiệu lực chưa xác minh
    forbidden_patterns = [
        r"vẫn đang có hiệu lực",
        r"đây là quy định hiện hành",
        r"vẫn còn hiệu lực",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            errors.append(
                "Có khẳng định hiệu lực pháp luật "
                "chưa được xác minh."
            )
            break

    # 4. Kiểm tra các ID được trích dẫn
    cited_ids = set(
        re.findall(
            r"vn_law_[a-zA-Z0-9_]+",
            answer
        )
    )

    for cited_id in cited_ids:
        if cited_id not in source_text:
            errors.append(
                f"ID không tồn tại trong dữ liệu nguồn: "
                f"{cited_id}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }

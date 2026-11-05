from neo4j import GraphDatabase
from langchain_core.tools import StructuredTool
from src.settings import settings


def get_driver():
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )



def search_legal_articles(keyword: str) -> str:
    """
    Tra cứu điều luật từ Knowledge Graph Neo4j.

    Hỗ trợ:
    - 188
    - Điều 188
    - Điều 188 Luật Đất đai 2013
    """
    import re

    keyword = keyword.strip()

    if not keyword:
        return "Vui lòng cung cấp từ khóa hoặc mã điều luật."

    original_keyword = keyword

    # Lấy số điều luật từ câu hỏi tự nhiên.
    # Ví dụ: "Điều 188 Luật Đất đai 2013" -> "188"
    match = re.search(
        r"(?:điều|dieu)\s+(\d+[a-zA-Z]?)",
        keyword,
        flags=re.IGNORECASE
    )

    if match:
        keyword = match.group(1)

    query = """
    MATCH (a:LegalEntity)
    WHERE a.type = 'LegalArticle'
      AND (
        toLower(coalesce(a.name, '')) CONTAINS toLower($kw)
        OR toLower(coalesce(a.id, '')) CONTAINS toLower($kw)
      )

    OPTIONAL MATCH (a)-[r:LEGAL_RELATION]->(c:LegalEntity)
    WHERE r.relation = 'HAS_CLAUSE'
      AND c.type = 'LegalClause'

    WITH a, collect(DISTINCT c) AS clauses

    RETURN a.id AS id,
           a.name AS name,
           [c IN clauses WHERE c IS NOT NULL |
             {id: c.id, name: c.name}
           ] AS clauses

    ORDER BY a.id
    LIMIT 5
    """

    driver = get_driver()

    try:
        with driver.session(database="neo4j") as session:
            records = list(session.run(query, kw=keyword))
    finally:
        driver.close()

    if not records:
        return (
            f"Không tìm thấy điều luật khớp với "
            f"'{original_keyword}'."
        )

    output = []

    for record in records:
        output.append(
            f"Điều luật: {record['name']}\n"
            f"ID: {record['id']}"
        )

        for clause in sorted(
            record["clauses"],
            key=lambda c: c["id"] or ""
        ):
            output.append(
                f"  - Khoản: {clause['name']} "
                f"[{clause['id']}]"
            )

    return "\n".join(output)

def get_article_structure(article_id: str) -> str:
    """
    Truy xuất cấu trúc điều -> khoản -> điểm.
    """
    query = """
    MATCH (a:LegalEntity {id: $article_id})
    WHERE a.type = 'LegalArticle'

    OPTIONAL MATCH (a)-[r1:LEGAL_RELATION]->(c:LegalEntity)
    WHERE r1.relation = 'HAS_CLAUSE'

    OPTIONAL MATCH (c)-[r2:LEGAL_RELATION]->(p:LegalEntity)
    WHERE r2.relation = 'HAS_POINT'

    RETURN a.id AS article_id,
           a.name AS article_name,
           c.id AS clause_id,
           c.name AS clause_name,
           p.id AS point_id,
           p.name AS point_name
    ORDER BY clause_id, point_id
    """

    with get_driver() as driver:
        with driver.session(database="neo4j") as session:
            records = list(
                session.run(query, article_id=article_id)
            )

    if not records:
        return "Không tìm thấy điều luật với ID đã cung cấp."

    output = []
    seen_clauses = set()

    for record in records:
        if not output:
            output.append(
                f"Điều luật: {record['article_name']}\n"
                f"ID: {record['article_id']}"
            )

        clause_id = record["clause_id"]

        if clause_id and clause_id not in seen_clauses:
            output.append(
                f"  Khoản: {record['clause_name']} "
                f"[{clause_id}]"
            )
            seen_clauses.add(clause_id)

        if record["point_id"]:
            output.append(
                f"    Điểm: {record['point_name']} "
                f"[{record['point_id']}]"
            )

    return "\n".join(output)


def get_guiding_decrees(article_id: str) -> str:
    """
    Chưa có quan hệ hướng dẫn được xác minh trong KG hiện tại.
    """
    return (
        f"Chưa có dữ liệu liên kết nghị định hoặc thông tư "
        f"được xác minh cho điều luật {article_id}. "
        "Không được suy đoán văn bản hướng dẫn từ các "
        "quan hệ UNKNOWN."
    )


def get_related_cases(article_id: str) -> str:
    """
    Chưa có quan hệ án lệ được xác minh trong KG hiện tại.
    """
    return (
        f"Chưa có dữ liệu liên kết án lệ hoặc bản án "
        f"được xác minh cho điều luật {article_id}."
    )


search_legal_articles_tool = StructuredTool.from_function(
    func=search_legal_articles,
    name="search_legal_articles",
    description=(
        "Tìm điều luật trong Knowledge Graph Neo4j "
        "theo mã điều hoặc từ khóa."
    ),
)

get_article_structure_tool = StructuredTool.from_function(
    func=get_article_structure,
    name="get_article_structure",
    description=(
        "Truy xuất các khoản và điểm thuộc một điều luật "
        "theo article_id."
    ),
)

get_guiding_decrees_tool = StructuredTool.from_function(
    func=get_guiding_decrees,
    name="get_guiding_decrees",
    description=(
        "Kiểm tra tình trạng dữ liệu liên kết nghị định "
        "và thông tư hướng dẫn."
    ),
)

get_related_cases_tool = StructuredTool.from_function(
    func=get_related_cases,
    name="get_related_cases",
    description=(
        "Kiểm tra tình trạng dữ liệu liên kết án lệ "
        "và bản án."
    ),
)


def get_article_ocr_data(article_id: str) -> dict:
    """
    Lấy nội dung OCR của Điều, Khoản, Điểm từ Neo4j.
    Chỉ đọc dữ liệu, không chỉnh sửa Knowledge Graph.
    """
    if not isinstance(article_id, str) or not article_id.startswith(
        "vn_law_2013_45_2013_qh13_article_"
    ):
        raise ValueError("Article ID không hợp lệ.")

    article_query = """
    MATCH (a:LegalEntity {id: $article_id})
    WHERE a.type = 'LegalArticle'
    RETURN a.id AS id,
           a.name AS name,
           a.ocr_heading AS heading,
           a.ocr_content AS content,
           a.ocr_source_file AS source_file,
           a.ocr_start_page AS start_page,
           a.ocr_end_page AS end_page,
           a.ocr_verification_status AS verification_status
    """

    structure_query = """
    MATCH (a:LegalEntity {id: $article_id})
          -[r1:LEGAL_RELATION]->(c:LegalEntity)
    WHERE a.type = 'LegalArticle'
      AND r1.relation = 'HAS_CLAUSE'
      AND c.type = 'LegalClause'

    OPTIONAL MATCH (c)-[r2:LEGAL_RELATION]->(p:LegalEntity)
    WHERE r2.relation = 'HAS_POINT'
      AND p.type = 'LegalPoint'

    RETURN c.id AS clause_id,
           c.ocr_content AS clause_content,
           c.ocr_verification_status AS clause_status,
           p.id AS point_id,
           p.ocr_content AS point_content,
           p.ocr_verification_status AS point_status

    ORDER BY clause_id, point_id
    """

    with get_driver() as driver:
        with driver.session(database="neo4j") as session:
            article_record = session.run(
                article_query,
                article_id=article_id
            ).single()

            if article_record is None:
                return {}

            article = dict(article_record)

            rows = [
                dict(row)
                for row in session.run(
                    structure_query,
                    article_id=article_id
                )
            ]

    clauses_by_id = {}

    for row in rows:
        clause_id = row["clause_id"]

        if clause_id not in clauses_by_id:
            clauses_by_id[clause_id] = {
                "id": clause_id,
                "content": row["clause_content"],
                "verification_status": row["clause_status"],
                "points": []
            }

        if row["point_id"] is not None:
            clauses_by_id[clause_id]["points"].append({
                "id": row["point_id"],
                "content": row["point_content"],
                "verification_status": row["point_status"]
            })

    article["clauses"] = list(clauses_by_id.values())

    return article


def get_article_ocr_text(article_id: str) -> str:
    """
    Công cụ chỉ đọc OCR dành cho Agent A.
    Không thay đổi dữ liệu Neo4j.
    """
    data = get_article_ocr_data(article_id)

    if not data:
        return "Không tìm thấy nội dung OCR cho điều luật này."

    output = [
        f"Điều luật: {data.get('name') or 'Không rõ'}",
        f"ID: {data.get('id')}",
        f"Nguồn PDF: {data.get('source_file') or 'Không rõ'}",
        f"Trạng thái xác minh: {data.get('verification_status') or 'unknown'}",
        "",
        "Nội dung OCR cấp Điều:",
        data.get("content") or "Không có nội dung.",
    ]

    for clause in data.get("clauses") or []:
        output.extend([
            "",
            f"Khoản ID: {clause['id']}",
            clause.get("content") or "Không có nội dung.",
        ])

        for point in clause.get("points") or []:
            output.extend([
                "",
                f"Điểm ID: {point['id']}",
                point.get("content") or "Không có nội dung.",
            ])

    output.extend([
        "",
        "CẢNH BÁO: OCR chưa được xác minh với PDF gốc.",
        "Không được khẳng định đây là quy định hiện hành.",
    ])

    return "\n".join(output)


get_article_ocr_text_tool = StructuredTool.from_function(
    func=get_article_ocr_text,
    name="get_article_ocr_text",
    description=(
        "Truy xuất nội dung OCR của một điều luật, "
        "bao gồm các khoản và điểm, bằng article_id. "
        "Dữ liệu OCR chưa được xác minh."
    ),
)

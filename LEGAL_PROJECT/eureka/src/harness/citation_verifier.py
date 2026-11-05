import re
from neo4j import GraphDatabase
from src.settings import settings

class CitationVerifier:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def verify_answer_citations(self, answer_text: str) -> dict:
        # Bắt các cụm như "Điều 188", "Điều 105"
        found_articles = re.findall(r"Điều\s+\d+", answer_text, flags=re.IGNORECASE)
        verified_results = {}

        with self.driver.session() as session:
            for art in set(found_articles):
                art_num = re.search(r"\d+", art).group(0)
                # Kiểm tra linh hoạt cả định dạng 'Dieu_188', 'article188', hoặc 'Điều 188' trong KG của bạn
                query = """
                MATCH (a)
                WHERE toLower(coalesce(a.id, '')) CONTAINS $num 
                   OR toLower(coalesce(a.title, '')) CONTAINS $art_lower
                RETURN a LIMIT 1
                """
                res = session.run(query, num=art_num, art_lower=art.lower())
                verified_results[art] = res.single() is not None

        valid_count = sum(1 for v in verified_results.values() if v)
        total = len(verified_results) if verified_results else 1
        accuracy_score = valid_count / total if verified_results else 1.0

        return {
            "accuracy_score": round(accuracy_score, 2),
            "details": verified_results
        }
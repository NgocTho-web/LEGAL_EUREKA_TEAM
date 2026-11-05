import json
import os
from collections import Counter
from pathlib import Path

from neo4j import GraphDatabase

KG_PATH = Path("data/kg/legal_kg_matched.json")

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD chưa được thiết lập")

with KG_PATH.open("r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg["nodes"]
edges = kg["edges"]

ids = [n.get("id") for n in nodes]
id_set = set(ids)

if any(not isinstance(i, str) or not i for i in ids):
    raise ValueError("Có node thiếu ID hợp lệ")

if len(id_set) != len(ids):
    raise ValueError("Có node ID trùng lặp")

if any(
    e.get("source") not in id_set or e.get("target") not in id_set
    for e in edges
):
    raise ValueError("Có quan hệ tham chiếu node không tồn tại")

# Bảo toàn cả các quan hệ trùng bộ ba source-target-relation.
# Mỗi edge có một ID dựa trên vị trí trong file JSON.
prepared_edges = [
    {
        **edge,
        "import_id": f"matched:{index}",
    }
    for index, edge in enumerate(edges)
]

def chunks(items, size=200):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def import_nodes(tx, batch):
    tx.run(
        """
        UNWIND $batch AS row
        MERGE (n:LegalEntity {id: row.id})
        SET n.name = row.name,
            n.type = row.type,
            n.source = row.source
        """,
        batch=batch,
    ).consume()


def import_edges(tx, batch):
    tx.run(
        """
        UNWIND $batch AS row
        MATCH (a:LegalEntity {id: row.source})
        MATCH (b:LegalEntity {id: row.target})
        MERGE (a)-[r:LEGAL_RELATION {import_id: row.import_id}]->(b)
        SET r.relation = row.relation,
            r.source_file = row.source_file
        """,
        batch=batch,
    ).consume()


print("=== EUREKA LEGAL KG IMPORT ===")
print("Source:", KG_PATH)
print("Nodes:", len(nodes))
print("Edges:", len(edges))

with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:
        session.run(
            """
            CREATE CONSTRAINT legal_entity_id IF NOT EXISTS
            FOR (n:LegalEntity)
            REQUIRE n.id IS UNIQUE
            """
        ).consume()

        for batch in chunks(nodes):
            session.execute_write(import_nodes, batch)

        for batch in chunks(prepared_edges):
            session.execute_write(import_edges, batch)

        node_count = session.run(
            """
            MATCH (n:LegalEntity)
            RETURN count(n) AS total
            """
        ).single()["total"]

        edge_count = session.run(
            """
            MATCH ()-[r:LEGAL_RELATION]->()
            RETURN count(r) AS total
            """
        ).single()["total"]

print("\n=== IMPORT RESULT ===")
print("Nodes:", node_count)
print("Edges:", edge_count)

print("\nNode types:")
print(dict(Counter(n.get("type") for n in nodes)))

print("\nRelation types:")
print(dict(Counter(e.get("relation") for e in edges)))

if node_count != len(nodes) or edge_count != len(edges):
    raise RuntimeError(
        "Số lượng dữ liệu trong Neo4j không khớp với JSON. "
        "Hãy kiểm tra trước khi tiếp tục."
    )

print("\nSUCCESS: Knowledge Graph imported successfully.")

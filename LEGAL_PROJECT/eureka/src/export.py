"""
export.py
Exports parsed documents, provisions, text versions, and relationships
to Neo4j-compatible CSV files according to Ontology v2 specifications.
"""

import os
import csv
from typing import List, Dict, Any, Set
import pandas as pd

RELATION_MAP = {
    # AMENDS (outbound)
    "Thay thế": ("AMENDS", False),
    "Bãi bỏ": ("AMENDS", False),
    "Sửa đổi, bổ sung": ("AMENDS", False),
    "Đính chính": ("AMENDS", False),
    "Tạm ngưng hiệu lực": ("AMENDS", False),
    "Đình chỉ thi hành": ("AMENDS", False),
    "Văn bản hết hiệu lực": ("AMENDS", False),
    "Văn bản bị hết hiệu lực 1 phần": ("AMENDS", False),
    "Văn bản được sửa đổi": ("AMENDS", False),
    "Văn bản được bổ sung": ("AMENDS", False),
    "Văn bản bị đình chỉ": ("AMENDS", False),
    "Văn bản bị đình chỉ 1 phần": ("AMENDS", False),

    # GUIDES (outbound)
    "Quy định chi tiết, hướng dẫn thi hành": ("GUIDES", False),
    "Hướng dẫn áp dụng": ("GUIDES", False),
    "Văn bản được HD, QĐ chi tiết": ("GUIDES", False),

    # REFERENCES (outbound)
    "Căn cứ": ("REFERENCES", False),
    "Dẫn chiếu": ("REFERENCES", False),
    "Văn bản căn cứ": ("REFERENCES", False),
    "Văn bản dẫn chiếu": ("REFERENCES", False),
    "Giải thích": ("REFERENCES", False),
    "Công bố": ("REFERENCES", False),
    "Bản dịch": ("REFERENCES", False),
    "Hợp nhất": ("REFERENCES", False),
    "Văn bản liên quan khác": ("REFERENCES", False),

    # Inbound (reversed: other_doc acts on doc)
    "Văn bản quy định hết hiệu lực": ("AMENDS", True),
    "Văn bản quy định hết hiệu lực 1 phần": ("AMENDS", True),
    "Văn bản sửa đổi": ("AMENDS", True),
    "Văn bản bổ sung": ("AMENDS", True),
    "Văn bản đình chỉ": ("AMENDS", True),
    "Văn bản đình chỉ 1 phần": ("AMENDS", True),
    "Văn bản HD, QĐ chi tiết": ("GUIDES", True),
}


def export_kg_csv(
    parsed_results: List[Dict[str, Any]],
    relationships_df: pd.DataFrame,
    id_to_doc_id_map: Dict[str, str],
    export_dir: str = "data/export"
) -> Dict[str, int]:
    """
    Exports KG nodes and relationships to data/export/:
    1. documents.csv
    2. components.csv (with Graph-RAG fields: document_id, component_id, type, title, text)
    3. text_versions.csv
    4. contains.csv
    5. legal_relations.csv
    """
    os.makedirs(export_dir, exist_ok=True)

    doc_rows = []
    comp_rows = []
    text_ver_rows = []
    contains_rows = []
    seen_contains = set()

    for item in parsed_results:
        doc = item["document"]
        provisions = item["provisions"]
        d_id = doc["id"]

        doc_rows.append({
            "id:ID": d_id,
            "official_number": doc.get("official_number", ""),
            "title": doc.get("title", ""),
            "doc_type": doc.get("doc_type", ""),
            "effective_from": doc.get("effective_from", ""),
            "signed_on": doc.get("signed_on", ""),
            "expired_on": doc.get("expired_on", ""),
            "force_status": doc.get("force_status", ""),
            "issuing_body": doc.get("issuing_body", ""),
            "source": doc.get("source", "th1nhng0"),
            "source_url": doc.get("source_url", ""),
            "status": doc.get("status", "parsed"),
            ":LABEL": "Document"
        })

        for p in provisions:
            p_id = p["id"]
            p_kind = p.get("kind", "")
            p_heading = p.get("heading", "")
            p_text = p.get("text", "")
            parent_id = p.get("parent_id") or d_id

            # Graph-RAG fields: document_id, component_id, type, title, text
            comp_rows.append({
                "id:ID": p_id,
                "document_id": d_id,
                "component_id": p_id,
                "type": p_kind,
                "title": p_heading,
                "text": p_text,
                "kind": p_kind,
                "number": p.get("number", ""),
                "heading": p_heading,
                "position:int": p.get("position", 0),
                ":LABEL": "Component"
            })

            # CONTAINS edge: parent -> child
            if (parent_id, p_id) not in seen_contains and parent_id != p_id:
                seen_contains.add((parent_id, p_id))
                contains_rows.append({
                    ":START_ID": parent_id,
                    ":END_ID": p_id,
                    ":TYPE": "CONTAINS"
                })

            # TextVersion node if text is present
            if p_text:
                t_hash = p.get("text_hash", "")
                v_id = f"{p_id}:{t_hash[:8]}" if t_hash else f"{p_id}:v1"
                caption = p_text[:80].replace("\n", " ") + "..." if len(p_text) > 80 else p_text.replace("\n", " ")
                text_ver_rows.append({
                    "id:ID": v_id,
                    "component_id": p_id,
                    "text": p_text,
                    "text_hash": t_hash,
                    "from_date": doc.get("effective_from", ""),
                    "to_date": doc.get("expired_on", ""),
                    "caption": caption,
                    ":LABEL": "TextVersion"
                })

    # Legal Relations (AMENDS, GUIDES, REFERENCES)
    legal_rel_rows = []
    seen_relations = set()

    if relationships_df is not None and not relationships_df.empty:
        for _, row in relationships_df.iterrows():
            src_raw = str(row["doc_id"])
            tgt_raw = str(row["other_doc_id"])
            label = str(row.get("relationship", "")).strip()

            src_stable = id_to_doc_id_map.get(src_raw)
            tgt_stable = id_to_doc_id_map.get(tgt_raw)

            if not src_stable or not tgt_stable or src_stable == tgt_stable:
                continue

            rel_type, inbound = RELATION_MAP.get(label, ("REFERENCES", False))

            if inbound:
                start_node, end_node = tgt_stable, src_stable
            else:
                start_node, end_node = src_stable, tgt_stable

            edge_key = (start_node, end_node, rel_type)
            if edge_key not in seen_relations:
                seen_relations.add(edge_key)
                legal_rel_rows.append({
                    ":START_ID": start_node,
                    ":END_ID": end_node,
                    ":TYPE": rel_type,
                    "label": label,
                    "source_doc_id": src_raw,
                    "target_doc_id": tgt_raw
                })

    # Write CSV files
    _write_csv(os.path.join(export_dir, "documents.csv"), doc_rows)
    _write_csv(os.path.join(export_dir, "components.csv"), comp_rows)
    _write_csv(os.path.join(export_dir, "text_versions.csv"), text_ver_rows)
    _write_csv(os.path.join(export_dir, "contains.csv"), contains_rows)
    _write_csv(os.path.join(export_dir, "legal_relations.csv"), legal_rel_rows)

    stats = {
        "documents_count": len(doc_rows),
        "components_count": len(comp_rows),
        "text_versions_count": len(text_ver_rows),
        "contains_edges_count": len(contains_rows),
        "legal_relations_count": len(legal_rel_rows),
        "total_nodes": len(doc_rows) + len(comp_rows) + len(text_ver_rows),
        "total_edges": len(contains_rows) + len(legal_rel_rows),
    }

    return stats


def _write_csv(filepath: str, rows: List[Dict[str, Any]]):
    if not rows:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            pass
        return

    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

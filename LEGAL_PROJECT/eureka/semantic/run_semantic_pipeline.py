"""
run_semantic_pipeline.py
Executes the Phase 2 Semantic Extraction Pipeline:
1. Loads Base Legal KG components from Phase 1.
2. Loads Controlled Vocabulary.
3. Extracts semantic links (REGULATES, APPLIES_TO, HAS_CONDITION, DEFINES).
4. Validates all IDs and relationship uniqueness.
5. Generates semantic_nodes.csv and semantic_relations.csv.
"""

import os
import csv
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd  # type: ignore[import-not-found]
from tqdm import tqdm  # type: ignore[import-not-found]

from .vocabulary_loader import VocabularyLoader, normalize_text
from .semantic_extractor import SemanticExtractor
from .semantic_validator import SemanticValidator


def run_semantic_pipeline(
    components_path: str = "data/export/components.csv",
    vocab_path: str = "real_estate_controlled_vocabulary.json",
    export_dir: str = "data/export",
    limit_docs: Optional[int] = None
) -> Dict[str, Any]:
    print("=" * 70)
    print("  PHASE 2: REAL ESTATE LEGAL KG — SEMANTIC EXTRACTION")
    print("=" * 70)
    start_time = time.time()

    # 1. Load Controlled Vocabulary
    print("\n[Step 1/4] Loading Controlled Vocabulary...")
    vocab = VocabularyLoader(vocab_path)
    extractor = SemanticExtractor(vocab)
    validator = SemanticValidator(vocab)
    print(f"  Loaded {len(vocab.concepts)} Concepts, {len(vocab.subjects)} Subjects, "
          f"{len(vocab.conditions)} Conditions, {len(vocab.procedures)} Procedures.")

    # 2. Load Components from Phase 1
    print(f"\n[Step 2/4] Loading Base Legal KG components from {components_path}...")
    df_comp = pd.read_csv(components_path, low_memory=False)
    print(f"  Total components in Phase 1: {len(df_comp):,}")

    # Focus on articles and clauses that have text or headings
    # Filter for relevant components (articles, clauses, points)
    meaningful_mask = (df_comp["type"].isin(["article", "clause", "point"])) & (
        df_comp["text"].notna() | df_comp["title"].notna()
    )
    target_components = df_comp[meaningful_mask].copy()
    print(f"  Target components to process: {len(target_components):,}")

    # 3. Semantic Extraction
    print("\n[Step 3/4] Extracting semantic concepts, subjects, conditions, and procedures...")
    records = target_components.to_dict(orient="records")
    validated_items = []
    total_validations = 0
    validation_errors = []

    # Track distinct stats
    linked_concepts: Set[str] = set()
    linked_subjects: Set[str] = set()
    linked_conditions: Set[str] = set()
    linked_procedures: Set[str] = set()
    articles_processed_set: Set[str] = set()

    # Special handling for "Giải thích từ ngữ" (DEFINES)
    defines_relations: List[Dict[str, str]] = []
    seen_defines: Set[Tuple[str, str, str]] = set()

    for row in tqdm(records, desc="Extracting semantic links"):
        raw_result = extractor.extract(row)
        is_valid, errors, clean_item = validator.validate_item(raw_result)
        total_validations += 1
        if not is_valid:
            validation_errors.extend(errors)

        comp_id = clean_item["component_id"]
        comp_type = row.get("type", "")
        title = str(row.get("title") or row.get("heading") or "")
        text = str(row.get("text") or "")

        # Count articles processed
        if comp_type == "article":
            articles_processed_set.add(comp_id)
        else:
            # Add parent article
            parts = comp_id.split(":clause-")[0].split(":point-")[0]
            articles_processed_set.add(parts)

        # Detect DEFINES in "Giải thích từ ngữ" clauses
        if "giải thích từ ngữ" in title.lower() or "giải thích từ ngữ" in text[:60].lower():
            for cid in clean_item["regulates_concepts"]:
                c_name = vocab.concepts[cid]["name_vi"].lower()
                if c_name in text.lower() or c_name in title.lower():
                    edge = (comp_id, cid, "DEFINES")
                    if edge not in seen_defines:
                        seen_defines.add(edge)
                        defines_relations.append({":START_ID": comp_id, ":END_ID": cid, ":TYPE": "DEFINES"})

        # Only keep items that have at least one semantic link
        if (clean_item["regulates_concepts"] or
            clean_item["applies_to_subjects"] or
            clean_item["conditions"] or
            clean_item["procedures"]):
            validated_items.append(clean_item)
            linked_concepts.update(clean_item["regulates_concepts"])
            linked_subjects.update(clean_item["applies_to_subjects"])
            linked_conditions.update(clean_item["conditions"])
            linked_procedures.update(clean_item["procedures"])

    print(f"  Processed {len(records):,} components ({len(articles_processed_set):,} distinct articles).")
    print(f"  Found semantic links in {len(validated_items):,} components.")
    print(f"  Linked {len(linked_concepts)} unique Concepts, {len(linked_subjects)} unique Subjects, "
          f"{len(linked_conditions)} unique Conditions, {len(linked_procedures)} unique Procedures.")

    # 4. Generate Semantic CSVs
    print(f"\n[Step 4/4] Generating semantic_nodes.csv and semantic_relations.csv in {export_dir}...")
    os.makedirs(export_dir, exist_ok=True)

    # Build semantic relations
    base_relations = validator.build_unique_relations(validated_items)
    all_relations = base_relations + defines_relations

    # Deduplicate all relations
    dedup_relations = []
    seen_rel = set()
    rel_type_counts = {}
    for r in all_relations:
        key = (r[":START_ID"], r[":END_ID"], r[":TYPE"])
        if key not in seen_rel:
            seen_rel.add(key)
            dedup_relations.append(r)
            rel_type_counts[r[":TYPE"]] = rel_type_counts.get(r[":TYPE"], 0) + 1

    # Build semantic nodes (all entities from vocabulary that are linked or declared)
    semantic_nodes_rows = []
    all_active_entities = linked_concepts | linked_subjects | linked_conditions | linked_procedures

    for cid, c_data in vocab.concepts.items():
        semantic_nodes_rows.append({
            "id:ID": cid,
            "name_vi": c_data.get("name_vi", ""),
            "domain": c_data.get("domain", ""),
            "description": c_data.get("description", ""),
            "entity_type": "LegalConcept",
            ":LABEL": "LegalConcept"
        })

    for sid, s_data in vocab.subjects.items():
        semantic_nodes_rows.append({
            "id:ID": sid,
            "name_vi": s_data.get("name_vi", ""),
            "domain": s_data.get("subject_type", ""),
            "description": s_data.get("description", ""),
            "entity_type": "LegalSubject",
            ":LABEL": "LegalSubject"
        })

    for cond_id, cond_data in vocab.conditions.items():
        semantic_nodes_rows.append({
            "id:ID": cond_id,
            "name_vi": cond_data.get("name_vi", ""),
            "domain": cond_data.get("condition_type", ""),
            "description": cond_data.get("description", ""),
            "entity_type": "LegalCondition",
            ":LABEL": "LegalCondition"
        })

    for pid, p_data in vocab.procedures.items():
        semantic_nodes_rows.append({
            "id:ID": pid,
            "name_vi": p_data.get("name_vi", ""),
            "domain": p_data.get("authority", ""),
            "description": p_data.get("description", ""),
            "entity_type": "LegalProcedure",
            ":LABEL": "LegalProcedure"
        })

    # Write semantic_nodes.csv
    nodes_csv_path = os.path.join(export_dir, "semantic_nodes.csv")
    with open(nodes_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id:ID", "name_vi", "domain", "description", "entity_type", ":LABEL"],
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(semantic_nodes_rows)

    # Write semantic_relations.csv
    relations_csv_path = os.path.join(export_dir, "semantic_relations.csv")
    with open(relations_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[":START_ID", ":END_ID", ":TYPE"],
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(dedup_relations)

    elapsed = time.time() - start_time

    metrics = {
        "execution_time_seconds": round(elapsed, 2),
        "articles_processed_count": len(articles_processed_set),
        "components_linked_count": len(validated_items),
        "unique_concepts_linked": len(linked_concepts),
        "unique_subjects_linked": len(linked_subjects),
        "unique_conditions_linked": len(linked_conditions),
        "unique_procedures_linked": len(linked_procedures),
        "total_semantic_nodes": len(semantic_nodes_rows),
        "total_semantic_relations": len(dedup_relations),
        "relation_breakdown": rel_type_counts,
        "sample_triples": dedup_relations[:10],
        "validation_errors_count": len(validation_errors)
    }

    print("\n" + "=" * 70)
    print("  PHASE 2 SEMANTIC EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total execution time: {elapsed:.2f}s")
    print(f"Articles processed: {len(articles_processed_set):,}")
    print(f"Components linked:  {len(validated_items):,}")
    print(f"Semantic Nodes generated: {len(semantic_nodes_rows)}")
    print(f"  - LegalConcept:   {len(vocab.concepts)}")
    print(f"  - LegalSubject:   {len(vocab.subjects)}")
    print(f"  - LegalCondition: {len(vocab.conditions)}")
    print(f"  - LegalProcedure: {len(vocab.procedures)}")
    print(f"Semantic Relationships generated: {len(dedup_relations):,}")
    for rtype, count in rel_type_counts.items():
        print(f"  - {rtype:<15}: {count:,}")
    print(f"\nFiles generated:")
    print(f"  - {nodes_csv_path} ({os.path.getsize(nodes_csv_path) / 1024:.1f} KB)")
    print(f"  - {relations_csv_path} ({os.path.getsize(relations_csv_path) / 1024:.1f} KB)")
    print("=" * 70)

    return metrics


if __name__ == "__main__":
    run_semantic_pipeline()

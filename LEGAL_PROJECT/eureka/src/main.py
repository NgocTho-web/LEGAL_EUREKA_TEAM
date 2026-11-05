"""
main.py
Main entry point for Phase 1 Base Legal Knowledge Graph construction.

Pipeline:
metadata.parquet
   ↓
filter_real_estate_documents
   ↓
select document IDs
   ↓
load matching content only
   ↓
reuse/adapt luatdo parser
   ↓
generate KG CSV (Neo4j import ready)
"""

import os
import sys
import time
import argparse
from tqdm import tqdm
import pandas as pd

from src.fetch import ensure_metadata_downloaded, load_matching_content
from src.filter import filter_real_estate_documents
from src.parser_adapter import parse_document
from src.export import export_kg_csv


def run_pipeline(
    raw_dir: str = "data/raw",
    export_dir: str = "data/export",
    limit: int = None
):
    print("=" * 70)
    print("  PHASE 1: REAL ESTATE LEGAL KNOWLEDGE GRAPH CONSTRUCTION")
    print("=" * 70)
    start_total_time = time.time()

    # 1. Fetch metadata & relationships
    print("\n[Step 1/5] Checking and downloading metadata & relationships...")
    meta_path, rel_path = ensure_metadata_downloaded(raw_dir)
    print(f"  Metadata path: {meta_path}")
    print(f"  Relationships path: {rel_path}")

    # 2. Filter Real Estate documents
    print("\n[Step 2/5] Filtering Real Estate documents from metadata...")
    filtered_meta, selected_ids, filtered_rels, filter_stats = filter_real_estate_documents(
        metadata_path=meta_path,
        relationships_path=rel_path,
        include_keywords=True
    )
    print(f"  Initial total documents: {filter_stats['initial_total_documents']:,}")
    print(f"  Filtered target documents: {filter_stats['total_filtered_documents']:,}")
    print(f"  Filtered inter-document relationships: {filter_stats['total_filtered_relationships']:,}")

    if limit and limit < len(filtered_meta):
        print(f"  Applying limit: restricting to first {limit} documents for processing...")
        filtered_meta = filtered_meta.head(limit)
        selected_ids = set(filtered_meta["id"].astype(str))
        filtered_rels = filtered_rels[
            filtered_rels["doc_id"].isin(selected_ids) & filtered_rels["other_doc_id"].isin(selected_ids)
        ]

    # 3. Load matching content only
    print("\n[Step 3/5] Loading matching content for selected document IDs only...")
    content_map = load_matching_content(selected_ids, raw_dir=raw_dir)

    # Build mapping from raw id to stable doc_id
    id_to_doc_id_map = {}
    records = filtered_meta.to_dict(orient="records")

    # 4. Parse documents using parser_adapter
    print(f"\n[Step 4/5] Parsing {len(records)} documents with parser adapter...")
    parsed_items = []
    status_counts = {"parsed": 0, "quarantined": 0, "metadata": 0}
    quarantine_reasons = {}

    parse_start = time.time()
    for row in tqdm(records, desc="Parsing documents"):
        raw_id = str(row["id"])
        row_content = content_map.get(raw_id, "")
        doc_input = dict(row)
        doc_input["content_html"] = row_content

        result = parse_document(doc_input)
        parsed_doc = result["document"]
        parsed_items.append(result)

        doc_status = parsed_doc["status"]
        status_counts[doc_status] = status_counts.get(doc_status, 0) + 1
        if doc_status == "quarantined":
            q_reason = parsed_doc.get("quarantine", "unknown")
            quarantine_reasons[q_reason] = quarantine_reasons.get(q_reason, 0) + 1

        id_to_doc_id_map[raw_id] = parsed_doc["id"]

    print(f"  Parsed {len(records)} documents in {time.time() - parse_start:.2f}s")
    print(f"  Document status breakdown: {status_counts}")
    if quarantine_reasons:
        print("  Top quarantine reasons:")
        for r, count in sorted(quarantine_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {r}: {count}")

    # 5. Export KG CSVs
    print(f"\n[Step 5/5] Exporting Knowledge Graph CSV files to {export_dir}...")
    export_stats = export_kg_csv(
        parsed_results=parsed_items,
        relationships_df=filtered_rels,
        id_to_doc_id_map=id_to_doc_id_map,
        export_dir=export_dir
    )

    print("\n" + "=" * 70)
    print("  PHASE 1 EXECUTION SUMMARY & METRICS")
    print("=" * 70)
    print(f"Total processing time: {time.time() - start_total_time:.2f}s")
    print(f"Total documents filtered: {len(records):,}")
    print("\nKnowledge Graph Nodes:")
    print(f"  - Document nodes:     {export_stats['documents_count']:,}")
    print(f"  - Component nodes:    {export_stats['components_count']:,}")
    print(f"  - TextVersion nodes:  {export_stats['text_versions_count']:,}")
    print(f"  TOTAL NODES:          {export_stats['total_nodes']:,}")

    print("\nKnowledge Graph Relationships:")
    print(f"  - CONTAINS edges:         {export_stats['contains_edges_count']:,}")
    print(f"  - Legal relation edges:   {export_stats['legal_relations_count']:,}")
    print(f"  TOTAL EDGES:              {export_stats['total_edges']:,}")

    print("\nExported Files in " + export_dir + ":")
    for fname in ["documents.csv", "components.csv", "text_versions.csv", "contains.csv", "legal_relations.csv"]:
        fpath = os.path.join(export_dir, fname)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"  - {fname:<22}: {size_kb:8.1f} KB")

    print("\nPipeline finished successfully!")
    return export_stats, status_counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Real Estate Legal Knowledge Graph (Phase 1)")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Directory containing raw parquet data")
    parser.add_argument("--export_dir", type=str, default="data/export", help="Directory to export CSV files")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents to parse (optional)")
    args = parser.parse_args()

    run_pipeline(
        raw_dir=args.raw_dir,
        export_dir=args.export_dir,
        limit=args.limit
    )

"""
fetch.py
Handles downloading datasets from Hugging Face and loading matching content only.
Ensures we do not load unnecessary 3.5GB content into memory.
"""

import os
import time
from typing import Set, Dict, Optional
import pyarrow.parquet as pq
import pandas as pd
from huggingface_hub import hf_hub_download

REPO_ID = "th1nhng0/vietnamese-legal-documents"


def ensure_metadata_downloaded(raw_dir: str = "data/raw") -> Tuple_paths:
    """
    Ensures metadata.parquet and relationships.parquet are downloaded locally.
    Does NOT download content.parquet here.
    """
    os.makedirs(raw_dir, exist_ok=True)
    meta_path = os.path.join(raw_dir, "data", "metadata.parquet")
    rel_path = os.path.join(raw_dir, "data", "relationships.parquet")

    if not os.path.exists(meta_path):
        print("Downloading metadata.parquet from Hugging Face...")
        hf_hub_download(
            repo_id=REPO_ID,
            filename="data/metadata.parquet",
            repo_type="dataset",
            local_dir=raw_dir
        )

    if not os.path.exists(rel_path):
        print("Downloading relationships.parquet from Hugging Face...")
        hf_hub_download(
            repo_id=REPO_ID,
            filename="data/relationships.parquet",
            repo_type="dataset",
            local_dir=raw_dir
        )

    return meta_path, rel_path


def load_matching_content(
    selected_doc_ids: Set[str],
    raw_dir: str = "data/raw",
    cache_matching: bool = True
) -> Dict[str, str]:
    """
    Loads content_html ONLY for the selected document IDs.
    Returns:
        dict: { doc_id: content_html }
    """
    matching_cache_path = os.path.join(raw_dir, "matching_content.parquet")
    if os.path.exists(matching_cache_path):
        print(f"Loading pre-filtered matching content from {matching_cache_path}...")
        t = pq.read_table(matching_cache_path)
        df = t.to_pandas()
        return dict(zip(df["id"].astype(str), df["content_html"].fillna("")))

    content_path = os.path.join(raw_dir, "data", "content.parquet")
    if not os.path.exists(content_path):
        print("Downloading content.parquet from Hugging Face...")
        content_path = hf_hub_download(
            repo_id=REPO_ID,
            filename="data/content.parquet",
            repo_type="dataset",
            local_dir=raw_dir
        )

    print(f"Extracting matching content for {len(selected_doc_ids)} documents...")
    start_time = time.time()
    
    # Read table with predicate pushdown on 'id'
    id_list = list(selected_doc_ids)
    table = pq.read_table(content_path, filters=[("id", "in", id_list)])
    df = table.to_pandas()

    content_map = dict(zip(df["id"].astype(str), df["content_html"].fillna("")))
    print(f"Successfully loaded content for {len(content_map)} documents in {time.time() - start_time:.2f}s")

    if cache_matching:
        print(f"Caching matching content ({len(df)} rows) to {matching_cache_path}...")
        pq.write_table(table, matching_cache_path, compression="zstd")

    return content_map

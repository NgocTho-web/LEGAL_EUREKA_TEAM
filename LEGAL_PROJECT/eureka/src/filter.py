"""
filter.py
Filters the raw Vietnamese Legal Documents dataset for the Real Estate domain.
Focuses on:
1. Luật Đất đai
2. Luật Nhà ở
3. Luật Kinh doanh bất động sản
4. Luật Đầu tư
Plus their central guiding, amending, and referencing instruments.
"""

import pandas as pd
from typing import Set, Tuple, Dict, Any, List

# Core Law Official Numbers
CORE_LAW_NUMBERS = [
    "31/2024/QH15",  # Luật Đất đai 2024
    "45/2013/QH13",  # Luật Đất đai 2013
    "27/2023/QH15",  # Luật Nhà ở 2023
    "65/2014/QH13",  # Luật Nhà ở 2014
    "29/2023/QH15",  # Luật Kinh doanh BĐS 2023
    "66/2014/QH13",  # Luật Kinh doanh BĐS 2014
    "61/2020/QH14",  # Luật Đầu tư 2020
    "67/2014/QH13",  # Luật Đầu tư 2014
    "43/2024/QH15",  # Luật Sửa đổi bổ sung 4 luật Đất đai, Nhà ở, KDBĐS, TCTD 2024
]

# Central ministries & authorities involved in real estate, land, housing, and investment
CENTRAL_ISSUERS_REGEX = (
    r"Quốc hội|Ủy ban Thường vụ Quốc hội|Chính phủ|Thủ tướng Chính phủ|"
    r"Bộ Tài nguyên và Môi trường|Bộ Xây dựng|Bộ Kế hoạch và Đầu tư|"
    r"Bộ Tài chính|Bộ Tư pháp|Ngân hàng Nhà nước"
)

LOCAL_PATTERNS = r"UBND|HĐND|Ủy ban nhân dân|Hội đồng nhân dân"
LOCAL_SCOPES = r"Địa phương|Tỉnh|Huyện|Xã|Thành phố"

REAL_ESTATE_KEYWORDS_REGEX = (
    r"đất đai|nhà ở|bất động sản|kinh doanh bất động sản|"
    r"quy hoạch đô thị|nhà chung cư|thu tiền sử dụng đất|"
    r"bồi thường, hỗ trợ, tái định cư|cấp giấy chứng nhận quyền sử dụng đất|"
    r"đăng ký biến động đất đai|đầu tư xây dựng|dự án đầu tư"
)

ALLOWED_DOC_TYPES = {
    "Luật", "Bộ luật", "Nghị định", "Nghị quyết",
    "Thông tư", "Thông tư liên tịch", "Quyết định", "Văn bản hợp nhất"
}


def filter_real_estate_documents(
    metadata_path: str,
    relationships_path: str = None,
    include_keywords: bool = True
) -> Tuple[pd.DataFrame, Set[str], pd.DataFrame, Dict[str, Any]]:
    """
    Filters metadata and relationships for real estate legal knowledge graph.
    Returns:
        filtered_metadata_df,
        selected_doc_ids,
        filtered_relationships_df,
        stats_dict
    """
    meta_df = pd.read_parquet(metadata_path)
    initial_total_docs = len(meta_df)

    # 1. Base cleanings: Central only, exclude local issuers and translations
    is_not_translation = meta_df["loai_van_ban"] != "Bản dịch văn bản"
    is_allowed_type = meta_df["loai_van_ban"].isin(ALLOWED_DOC_TYPES)

    pham_vi_str = meta_df["pham_vi"].astype(str)
    co_quan_str = meta_df["co_quan_ban_hanh"].astype(str)

    not_local_scope = ~pham_vi_str.str.contains(LOCAL_SCOPES, case=False, na=False)
    not_local_issuer = ~co_quan_str.str.contains(LOCAL_PATTERNS, case=False, na=False)
    central_issuer = (
        meta_df["pham_vi"].isin(["Trung ương", "Toàn quốc"]) |
        co_quan_str.str.contains(CENTRAL_ISSUERS_REGEX, case=False, na=False)
    )

    clean_central_mask = is_not_translation & is_allowed_type & not_local_scope & not_local_issuer & central_issuer

    # 2. Identify Core Laws
    core_mask = meta_df["so_ky_hieu"].isin(CORE_LAW_NUMBERS) & (meta_df["loai_van_ban"] == "Luật")
    core_df = meta_df[core_mask]
    core_ids = set(core_df["id"].astype(str))

    # 3. Relationships traversal
    rels_df = None
    connected_ids = set()
    filtered_rels_df = pd.DataFrame()

    if relationships_path:
        rels_df = pd.read_parquet(relationships_path)
        # Find relations where either doc_id or other_doc_id is one of our core laws
        direct_mask = rels_df["doc_id"].isin(core_ids) | rels_df["other_doc_id"].isin(core_ids)
        core_connected_rels = rels_df[direct_mask]
        connected_ids = set(core_connected_rels["doc_id"]).union(set(core_connected_rels["other_doc_id"]))

    # 4. Keyword relevance
    keyword_mask = pd.Series(False, index=meta_df.index)
    if include_keywords:
        title_match = meta_df["title"].str.contains(REAL_ESTATE_KEYWORDS_REGEX, case=False, na=False)
        field_match = meta_df["linh_vuc"].str.contains(r"Đất đai|Xây dựng|Nhà ở|Bất động sản|Đầu tư", case=False, na=False)
        keyword_mask = title_match | field_match

    # Final combined condition:
    # Must pass clean central filter AND (be a core law OR connected via official relation OR match domain keywords)
    selected_mask = clean_central_mask & (meta_df["id"].isin(core_ids) | meta_df["id"].isin(connected_ids) | keyword_mask)
    filtered_meta = meta_df[selected_mask].copy()

    # Drop duplicate stable document numbers if any, keeping lowest row id
    filtered_meta["clean_number"] = filtered_meta["so_ky_hieu"].str.strip().str.upper()
    filtered_meta = filtered_meta.sort_values(by="id").drop_duplicates(subset=["clean_number", "co_quan_ban_hanh"])
    filtered_meta = filtered_meta.drop(columns=["clean_number"])

    selected_doc_ids = set(filtered_meta["id"].astype(str))

    # Filter relationships between the selected documents
    if rels_df is not None:
        both_in_corpus = rels_df["doc_id"].isin(selected_doc_ids) & rels_df["other_doc_id"].isin(selected_doc_ids)
        filtered_rels_df = rels_df[both_in_corpus].copy()

    stats = {
        "initial_total_documents": initial_total_docs,
        "core_laws_found": len(core_ids),
        "total_filtered_documents": len(filtered_meta),
        "total_filtered_relationships": len(filtered_rels_df),
        "doc_type_distribution": filtered_meta["loai_van_ban"].value_counts().to_dict(),
        "top_issuing_bodies": filtered_meta["co_quan_ban_hanh"].value_counts().head(5).to_dict(),
    }

    return filtered_meta, selected_doc_ids, filtered_rels_df, stats

"""
semantic_extractor.py
Extracts semantic entities and relationships from Component text (Articles, Clauses, Points).
Strictly adheres to the requirement:
- Selects ONLY existing IDs from the Controlled Vocabulary.
- Never creates new entity IDs.
"""

import re
from typing import Dict, List, Set, Any, Optional
from .vocabulary_loader import VocabularyLoader, normalize_text


def _find_keyword_matches(text_norm: str, lookup_dict: Dict[str, str]) -> Set[str]:
    """
    Finds all vocabulary IDs whose name or alias appears as a whole phrase in normalized text.
    Sorted by phrase length in descending order to prioritize specific multi-word entities.
    """
    matched_ids = set()
    # Sort phrases by word count / length descending
    sorted_phrases = sorted(lookup_dict.keys(), key=lambda x: len(x.split()), reverse=True)

    # Pad with spaces for word boundary matching
    padded_text = f" {text_norm} "

    for phrase in sorted_phrases:
        if len(phrase) < 3:
            continue
        # Check boundary
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, padded_text):
            matched_ids.add(lookup_dict[phrase])

    return matched_ids


class SemanticExtractor:
    def __init__(self, vocab: VocabularyLoader):
        self.vocab = vocab

    def extract(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts semantic references for a single component.
        Component dict must contain:
          - component_id (str)
          - text (str, optional)
          - title (str, optional)
          - heading (str, optional)
        """
        comp_id = str(component.get("component_id") or component.get("id") or "").strip()
        heading = str(component.get("title") or component.get("heading") or "").strip()
        body = str(component.get("text") or "").strip()

        combined_text = f"{heading} {body}".strip()
        norm_text = normalize_text(combined_text)

        # 1. Extract Concepts (REGULATES / DEFINES)
        concept_ids = _find_keyword_matches(norm_text, self.vocab.concept_lookup)

        # 2. Extract Subjects (APPLIES_TO)
        subject_ids = _find_keyword_matches(norm_text, self.vocab.subject_lookup)

        # 3. Extract Conditions (HAS_CONDITION)
        condition_ids = _find_keyword_matches(norm_text, self.vocab.condition_lookup)
        
        # Rule-based contextual enhancement for conditions based on common legal phrasing
        if "không có tranh chấp" in norm_text or "không tranh chấp" in norm_text:
            condition_ids.add("cond:dat_khong_co_tranh_chap")
        if "không bị kê biên" in norm_text:
            condition_ids.add("cond:quyen_su_dung_dat_khong_bi_ke_bien")
        if "trong thời hạn sử dụng" in norm_text:
            condition_ids.add("cond:trong_thoi_han_su_dung_dat")
        if "giấy phép xây dựng" in norm_text:
            condition_ids.add("cond:co_giay_phep_xay_dung")
        if "phần móng" in norm_text or "xây dựng móng" in norm_text:
            condition_ids.add("cond:nghiem_thu_hoan_thanh_xay_dung_mong")
        if "bảo lãnh" in norm_text and ("ngân hàng" in norm_text or "tài chính" in norm_text):
            condition_ids.add("cond:bao_lanh_ngan_hang_nghia_vu_tai_chinh")
        if "đặt cọc" in norm_text and "5%" in norm_text:
            condition_ids.add("cond:tien_dat_coc_khong_qua_5_phan_tram")
        if "30%" in norm_text and ("lần đầu" in norm_text or "thanh toán" in norm_text):
            condition_ids.add("cond:thanh_toan_lan_dau_khong_qua_30_phan_tram")
        if "70%" in norm_text and ("bàn giao" in norm_text or "thu tiền" in norm_text):
            condition_ids.add("cond:thanh_toan_truoc_ban_giao_khong_qua_70_phan_tram")
        if "95%" in norm_text and ("giấy chứng nhận" in norm_text or "sổ" in norm_text):
            condition_ids.add("cond:thanh_toan_truoc_khi_cap_so_khong_qua_95_phan_tram")
        if "chưa có nhà ở" in norm_text:
            condition_ids.add("cond:chua_co_nha_o_thuoc_so_huu")
        if "thu nhập" in norm_text and "không phải nộp thuế" in norm_text:
            condition_ids.add("cond:thu_nhap_thuoc_dien_khong_phai_nop_thue")
        if "05 năm" in norm_text or "5 năm" in norm_text:
            if "nhà ở xã hội" in norm_text:
                condition_ids.add("cond:thoi_han_han_che_chuyen_nhuong_noxh_5_nam")

        # 4. Extract Procedures
        procedure_ids = _find_keyword_matches(norm_text, self.vocab.procedure_lookup)
        if "chấp thuận chủ trương đầu tư" in norm_text:
            if "thủ tướng" in norm_text:
                procedure_ids.add("proc:chap_thuan_chu_truong_dau_tu_thu_tuong")
            else:
                procedure_ids.add("proc:chap_thuan_chu_truong_dau_tu_ubnd_tinh")
        if "chuyển nhượng quyền sử dụng đất" in norm_text and ("thủ tục" in norm_text or "trình tự" in norm_text or "đăng ký" in norm_text):
            procedure_ids.add("proc:chuyen_nhuong_quyen_su_dung_dat")
        if "đăng ký biến động" in norm_text:
            procedure_ids.add("proc:dang_ky_bien_dong_dat_dai")
        if "đủ điều kiện được bán" in norm_text or "đủ điều kiện bán" in norm_text:
            procedure_ids.add("proc:thong_bao_nha_o_du_dieu_kien_duoc_ban")

        # STRICT FILTERING: Ensure only valid existing IDs from vocabulary are returned
        valid_concepts = sorted([cid for cid in concept_ids if cid in self.vocab.concepts])
        valid_subjects = sorted([sid for sid in subject_ids if sid in self.vocab.subjects])
        valid_conditions = sorted([cond_id for cond_id in condition_ids if cond_id in self.vocab.conditions])
        valid_procedures = sorted([pid for pid in procedure_ids if pid in self.vocab.procedures])

        return {
            "component_id": comp_id,
            "regulates_concepts": valid_concepts,
            "applies_to_subjects": valid_subjects,
            "conditions": valid_conditions,
            "procedures": valid_procedures,
        }

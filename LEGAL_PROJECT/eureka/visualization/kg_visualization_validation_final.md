# Bảng Đối chiếu Độ chính xác của Đồ thị (Validation Final)

## NODE VALIDATION

| Node ID | Node Type | Cypher | Renderer | Match |
|:---|:---|:---:|:---:|:---:|
| `vn:law:2013:45-2013-qh13` | `Document` | Có | Có | MATCH |
| `vn:law:2013:45-2013-qh13:article-188` | `Component` (`Article`) | Có | Có | MATCH |
| `vn:law:2013:45-2013-qh13:article-188:clause-1` | `Component` (`Clause`) | Có | Có | MATCH |
| `subject:nguoi_su_dung_dat` | `LegalSubject` | Có | Có | MATCH |
| `concept:quyen_su_dung_dat` | `LegalConcept` | Có | Có | MATCH |
| `concept:chuyen_nhuong_quyen_su_dung_dat` | `LegalConcept` | Có | Có | MATCH |
| `concept:giay_chung_nhan_quyen_su_dung_dat` | `LegalConcept` | Có | Có | MATCH |
| `cond:co_giay_chung_nhan_qsd_dat` | `LegalCondition` | Có | Có | MATCH |
| `cond:dat_khong_co_tranh_chap` | `LegalCondition` | Có | Có | MATCH |
| `cond:quyen_su_dung_dat_khong_bi_ke_bien` | `LegalCondition` | Có | Có | MATCH |
| `cond:trong_thoi_han_su_dung_dat` | `LegalCondition` | Có | Có | MATCH |
| `proc:chuyen_nhuong_quyen_su_dung_dat` | `LegalProcedure` | Có | Có | MATCH |
| `proc:dang_ky_bien_dong_dat_dai` | `LegalProcedure` | Có | Có | MATCH |

## EDGE VALIDATION

| Source | Relationship | Target | Direction | Cypher | Renderer | Match |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| `Document` (Luật ĐĐ) | `CONTAINS` | `Article` (Điều 188) | `->` | Có | Có | MATCH |
| `Article` (Điều 188) | `CONTAINS` | `Clause` (Khoản 1) | `->` | Có | Có | MATCH |
| `Clause` (Khoản 1) | `APPLIES_TO` | `LegalSubject` (Người SDĐ) | `->` | Có | Có | MATCH |
| `Article` (Điều 188) | `REGULATES` | `LegalConcept` (Quyền SDĐ) | `->` | Có | Có | MATCH |
| `Clause` (Khoản 1) | `REGULATES` | `LegalConcept` (Quyền SDĐ) | `->` | Có | Có | MATCH |
| `Clause` (Khoản 1) | `REGULATES` | `LegalConcept` (Chuyển nhượng QSDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Quyền SDĐ) | `REGULATES` | `LegalConcept` (Giấy CN QSDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Quyền SDĐ) | `HAS_CONDITION` | `LegalCondition` (Có GCN QSDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Quyền SDĐ) | `HAS_CONDITION` | `LegalCondition` (Đất không có tranh chấp) | `->` | Có | Có | MATCH |
| `LegalConcept` (Quyền SDĐ) | `HAS_CONDITION` | `LegalCondition` (QSDĐ không bị kê biên) | `->` | Có | Có | MATCH |
| `LegalConcept` (Quyền SDĐ) | `HAS_CONDITION` | `LegalCondition` (Trong thời hạn SDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Giấy CN QSDĐ) | `HAS_CONDITION` | `LegalCondition` (Có GCN QSDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Chuyển nhượng QSDĐ) | `HAS_CONDITION` | `LegalCondition` (Có GCN QSDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Chuyển nhượng QSDĐ) | `HAS_CONDITION` | `LegalCondition` (Trong thời hạn SDĐ) | `->` | Có | Có | MATCH |
| `LegalConcept` (Chuyển nhượng QSDĐ) | `HAS_PROCEDURE` | `LegalProcedure` (TT Chuyển nhượng) | `->` | Có | Có | MATCH |
| `LegalConcept` (Chuyển nhượng QSDĐ) | `HAS_PROCEDURE` | `LegalProcedure` (TT Đăng ký BĐ) | `->` | Có | Có | MATCH |

"""
parser_adapter.py
Adapted from luatdo (Go) parser engine (parse.go, html.go, law.go).
Provides deterministic document and provision parsing and stable ID generation.
"""

import re
import html
import hashlib
from typing import Dict, List, Optional, Tuple, Any

# ==========================================
# Regex patterns from luatdo/parse/parse.go
# ==========================================

FRONT_MATTER_KEY = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
CHAPTER_LINE = re.compile(r"^(?:Chương|CHƯƠNG)\s+([0-9]+|[IVXLC]+)\s*[:.]?\s*(.*)$")
SECTION_LINE = re.compile(r"^(?:Mục|MỤC)\s+([0-9]+|[IVXLC]+)\s*[:.]?\s*(.*)$")
ARTICLE_LINE = re.compile(r"^Điều\s+(\d+[a-zđ]?)(?:\.\s*(.*)|\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ].*))?$", re.UNICODE)
CLAUSE_LINE = re.compile(r"^(\d+[a-zđ]?)\.(?:\s+(.*))?$")
POINT_LINE = re.compile(r"^([a-zđ]{1,2})\)\s+(.*)$")
NUMBER_LINE = re.compile(r"^Số:\s*([0-9]+/[0-9]{4}/[^\s,;]+)")
SIGNATURE_LINE = re.compile(r"^(?:TM\.|KT\.|CHỦ TỊCH QUỐC HỘI|CHỦ TỊCH NƯỚC|Nơi nhận:|XÁC THỰC VĂN BẢN)")
ANNEX_LABEL_LINE = re.compile(r"^(?:PHỤ LỤC|Phụ lục)(?:\s+(?:số\s+)?([IVXLC]+|\d+[A-Za-zĐđ]?))?\s*[:.]?$")
ANNEX_KIND_LINE = re.compile(r"^(QUY ĐỊNH|QUY CHẾ|QUY TRÌNH|QUY TẮC|ĐIỀU LỆ|NỘI QUY|THỂ LỆ|DANH MỤC|BIỂU MẪU|ĐỀ ÁN|KẾ HOẠCH|CHƯƠNG TRÌNH|PHƯƠNG ÁN|HƯỚNG DẪN)[^a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]*$")
ISSUANCE_LINE = re.compile(r"^[(\uFF08]?\s*(?:ban hành\s+)?kèm theo\b", re.IGNORECASE)
DECORATION_LINE = re.compile(r"^(?:[-_–—=*.\s]+|CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM|Độc lập\s*[-–—]\s*Tự do\s*[-–—]\s*Hạnh phúc)$")

NUMBER_PATTERN = re.compile(r"^(\d+)/(\d{4})/([A-Za-z0-9ĐđƯưÔôÂâ-]+)$")
CONSTITUTION_PATTERN = re.compile(r"^Hiến pháp\s+(\d{4})$")
DMY_PATTERN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
ISO_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
SLUG_CLEANUP = re.compile(r"[^a-z0-9]+")

BLOCK_TAGS = {
    "p", "div", "br", "tr", "td", "th",
    "li", "ul", "ol", "table", "section",
    "article", "h1", "h2", "h3", "h4",
    "h5", "h6", "blockquote", "hr"
}
DROP_TAGS = {"script", "style", "head"}

LOCAL_BODIES = {"UBND", "HDND", "UB", "CTUBND", "CTUB"}

# Vietnamese Telex map for numbers
TELEX_REPLACEMENTS = {
    "ă": "aw", "Ă": "aw",
    "â": "aa", "Â": "aa",
    "ê": "ee", "Ê": "ee",
    "ô": "oo", "Ô": "oo",
    "ơ": "ow", "Ơ": "ow",
    "ư": "uw", "Ư": "uw",
    "đ": "dd", "Đ": "dd",
}

VIETNAMESE_FOLD_MAP = {
    "a": "áàảãạăắằẳẵặâấầẩẫậ",
    "e": "éèẻẽẹêếềểễệ",
    "i": "íìỉĩị",
    "o": "óòỏõọôốồổỗộơớờởỡợ",
    "u": "úùủũụưứừửữự",
    "y": "ýỳỷỹỵ",
    "d": "đ",
}

FOLD_DICT = {}
for base, chars in VIETNAMESE_FOLD_MAP.items():
    for c in chars:
        FOLD_DICT[c] = base
        FOLD_DICT[c.upper()] = base.upper()

ASCII_FOLD_DICT = {
    "Đ": "d", "đ": "d",
    "Ư": "u", "ư": "u",
    "Ô": "o", "ô": "o",
    "Â": "a", "â": "a",
}


def ascii_fold(s: str) -> str:
    res = []
    for ch in s:
        res.append(ASCII_FOLD_DICT.get(ch, ch))
    return "".join(res)


def vietnamese_fold(s: str) -> str:
    res = []
    for ch in s:
        res.append(FOLD_DICT.get(ch, ch))
    return "".join(res)


def slug(s: str) -> str:
    folded = vietnamese_fold(s.strip()).lower()
    return SLUG_CLEANUP.sub("-", folded).strip("-")


def number_segment(number: str) -> str:
    res = number.strip()
    for k, v in TELEX_REPLACEMENTS.items():
        res = res.replace(k, v)
    return res.lower()


def doc_id(official_number: str) -> str:
    trimmed = official_number.strip()
    m_const = CONSTITUTION_PATTERN.match(trimmed)
    if m_const:
        year = m_const.group(1)
        return f"vn:constitution:{year}:hien-phap-{year}"
    m = NUMBER_PATTERN.match(trimmed)
    if not m:
        # Fallback slug for non-standard numbers
        safe_num = slug(trimmed)
        return f"vn:law:unknown:{safe_num}" if safe_num else "vn:law:unknown:unknown"
    num, year, body = m.group(1), m.group(2), m.group(3)
    slugified = f"{num}-{year}-{ascii_fold(body)}".lower()
    return f"vn:law:{year}:{slugified}"


def body_abbrev(token: str) -> str:
    letters = ascii_fold(token.strip()).upper()
    for i, ch in enumerate(letters):
        if not ('A' <= ch <= 'Z'):
            return letters[:i]
    return letters


def is_body_relative(official_number: str) -> bool:
    suffix = official_number.strip()
    idx = suffix.rfind("/")
    if idx >= 0:
        suffix = suffix[idx + 1:]
    if "-" not in suffix:
        return False
    issuer = suffix.split("-", 1)[1]
    for part in issuer.split("-"):
        if body_abbrev(part) in LOCAL_BODIES:
            return True
    return False


def doc_id_in(official_number: str, issuing_body: str) -> str:
    d_id = doc_id(official_number)
    if not is_body_relative(official_number):
        return d_id
    body_slug = slug(issuing_body)
    if body_slug:
        return f"{d_id}:{body_slug}"
    return d_id


def provision_id(parent: str, kind: str, number: str) -> str:
    return f"{parent}:{kind}-{number_segment(number)}"


def repeat_id(p_id: str, n: int) -> str:
    return f"{p_id}~{n}"


def roman_to_arabic(s: str) -> str:
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    upper = s.strip().upper()
    if not upper:
        return s
    total, prev = 0, 0
    for ch in reversed(upper):
        if ch not in values:
            return s
        v = values[ch]
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    return str(total)


def iso_date(s: Optional[str]) -> str:
    if not s:
        return ""
    s = str(s).strip()
    if ISO_PATTERN.match(s):
        return s
    m = DMY_PATTERN.match(s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""


def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ==========================================
# HTML to Text (luatdo/parse/html.go)
# ==========================================

def html_to_text(source: str) -> str:
    if not source:
        return ""
    
    out: List[str] = []
    skip: str = ""
    i = 0
    length = len(source)
    
    while i < length:
        c = source[i]
        if c != '<':
            j = source.find('<', i)
            if j < 0:
                j = length
            if not skip:
                out.append(source[i:j])
            i = j
            continue
        
        # Scan tag
        tag_name, closing, end_idx = _scan_tag(source, i)
        i = end_idx
        if not tag_name:
            continue
        
        if skip:
            if closing and tag_name == skip:
                skip = ""
        elif tag_name in DROP_TAGS and not closing:
            skip = tag_name
        elif tag_name in BLOCK_TAGS:
            out.append('\n')
            
    raw_text = html.unescape("".join(out))
    return _normalize_lines(raw_text)


def _scan_tag(source: str, start: int) -> Tuple[str, bool, int]:
    length = len(source)
    j = start + 1
    closing = False
    if j < length and source[j] == '/':
        closing = True
        j += 1
    if j < length and source[j] == '!':
        k = source.find('>', j)
        if k >= 0:
            return "", False, k + 1
        return "", False, length
        
    tag_start = j
    while j < length and (source[j].isalnum() or source[j] in ('-', '_')):
        j += 1
    name = source[tag_start:j].lower()
    
    quote = ''
    while j < length:
        ch = source[j]
        if quote:
            if ch == quote:
                quote = ''
        elif ch in ('"', "'"):
            quote = ch
        elif ch == '>':
            return name, closing, j + 1
        j += 1
    return name, closing, length


def _normalize_lines(text: str) -> str:
    text = text.replace('\r\n', '\n')
    lines = text.split('\n')
    out: List[str] = []
    blank = False
    for line in lines:
        cleaned = " ".join(line.split()).strip()
        if not cleaned:
            if blank or len(out) == 0:
                continue
            blank = True
            out.append("")
            continue
        blank = False
        out.append(cleaned)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


# ==========================================
# Quarantine & Frontmatter
# ==========================================

def split_front_matter(content: str) -> Tuple[Dict[str, str], str]:
    front = {}
    lines = content.split('\n')
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "---":
            return front, "\n".join(lines[i + 1:])
        m = FRONT_MATTER_KEY.match(s)
        if m:
            front[m.group(1)] = m.group(2).strip()
    return front, content


def quarantine_reason(official_number: str, body: str) -> str:
    lines = [line.strip() for line in body.split('\n') if line.strip()]
    for line in lines:
        m = NUMBER_LINE.match(line)
        if m:
            body_num = m.group(1).rstrip('.,;').strip().upper()
            meta_num = official_number.rstrip('.,;').strip().upper()
            if body_num != meta_num:
                return f"body carries official number {body_num}, metadata says {meta_num}"
            break
            
    article_count = 0
    for line in lines:
        if ARTICLE_LINE.match(line):
            article_count += 1
            if article_count >= 2:
                break
    if article_count < 2:
        return "no article structure found in body"
    return ""


# ==========================================
# Tree Builder (luatdo/parse/parse.go)
# ==========================================

class ParserState:
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.root = doc_id
        self.annex = -1
        self.annexes = 0
        self.chapter = -1
        self.section = -1
        self.article = -1
        self.clause = -1
        self.point = -1
        self.provisions: List[Dict[str, Any]] = []
        self.used: Dict[str, int] = {}

    def annex_id(self) -> str:
        if self.annex < 0:
            return ""
        return self.provisions[self.annex]["id"]

    def add(self, prov: Dict[str, Any]) -> int:
        p_id = prov["id"]
        self.used[p_id] = self.used.get(p_id, 0) + 1
        count = self.used[p_id]
        if count > 1:
            prov["id"] = repeat_id(p_id, count)
        prov["position"] = len(self.provisions) + 1
        self.provisions.append(prov)
        return len(self.provisions) - 1

    def at(self, i: int) -> Optional[Dict[str, Any]]:
        if 0 <= i < len(self.provisions):
            return self.provisions[i]
        return None

    def append_text(self, i: int, text: str):
        prov = self.at(i)
        if prov is None:
            return
        if prov.get("text"):
            prov["text"] += "\n" + text
        else:
            prov["text"] = text

    def deepest(self) -> int:
        if self.point >= 0:
            return self.point
        if self.clause >= 0:
            return self.clause
        if self.article >= 0:
            return self.article
        if self.section >= 0:
            return self.section
        if self.chapter >= 0:
            return self.chapter
        if self.annex >= 0:
            return self.annex
        return -1


def add_heading(prov: Optional[Dict[str, Any]], line: str):
    if prov is None:
        return
    if line != line.upper():
        return
    if not prov.get("heading"):
        prov["heading"] = line
    else:
        prov["heading"] += " " + line


def section_opens(line: str, in_article: bool) -> bool:
    m = SECTION_LINE.match(line)
    if not m:
        return False
    return (not in_article) or (m.group(2).strip() == "")


def is_structural(line: str) -> bool:
    return bool(ARTICLE_LINE.match(line) or CHAPTER_LINE.match(line) or
                SECTION_LINE.match(line) or CLAUSE_LINE.match(line))


def open_annex(p: ParserState, lines: List[str], i: int) -> Tuple[int, bool]:
    line = lines[i]
    label = ""
    confirmed = False
    if ANNEX_LABEL_LINE.match(line):
        label = line
        confirmed = True
    elif ANNEX_KIND_LINE.match(line):
        label = line
    else:
        return i, False

    title = []
    end = i
    window = min(len(lines), i + 11)
    for j in range(i + 1, window):
        lj = lines[j]
        if ISSUANCE_LINE.search(lj):
            confirmed = True
            end = j
            while end + 1 < len(lines) and not (lines[end].endswith(")") or lines[end].endswith("）")):
                end += 1
            break
        if is_structural(lj):
            break
        if not DECORATION_LINE.match(lj):
            title.append(lj)

    if not confirmed:
        return i, False

    p.annexes += 1
    num = str(p.annexes)
    heading = " ".join([label] + title).strip()
    heading = " ".join(heading.split())

    p.annex = p.add({
        "id": provision_id(p.doc_id, "annex", num),
        "kind": "annex",
        "number": num,
        "heading": heading,
        "text": "",
    })
    p.root = p.at(p.annex)["id"]
    p.chapter = p.section = p.article = p.clause = p.point = -1
    return end, True


def quoted_lines(lines: List[str]) -> List[bool]:
    inside = [False] * len(lines)
    open_indices: List[int] = []
    
    for i, line in enumerate(lines):
        for ch in line:
            if ch == '\u201c':  # “
                open_indices.append(i)
            elif ch == '\u201d':  # ”
                if open_indices:
                    start = open_indices.pop()
                    for k in range(start + 1, i + 1):
                        inside[k] = True
            elif ch == '"':
                if open_indices:
                    start = open_indices.pop()
                    for k in range(start + 1, i + 1):
                        inside[k] = True
                else:
                    open_indices.append(i)
    return inside


def parse_body(doc_id: str, body: str) -> List[Dict[str, Any]]:
    lines = [line.strip() for line in body.split('\n') if line.strip()]
    if not lines:
        return []

    p = ParserState(doc_id)
    quoted = quoted_lines(lines)
    saw_article = False
    tail = False

    i = 0
    while i < len(lines):
        line = lines[i]
        if quoted[i]:
            p.append_text(p.deepest(), line)
            i += 1
            continue

        if saw_article:
            next_idx, ok = open_annex(p, lines, i)
            if ok:
                saw_article, tail = False, False
                i = next_idx + 1
                continue
            if SIGNATURE_LINE.match(line):
                tail = True

        if tail:
            i += 1
            continue

        m_chap = CHAPTER_LINE.match(line)
        m_sec = SECTION_LINE.match(line)
        m_art = ARTICLE_LINE.match(line)
        m_clause = CLAUSE_LINE.match(line)
        m_point = POINT_LINE.match(line)

        if m_chap:
            num = roman_to_arabic(m_chap.group(1))
            heading = m_chap.group(2).strip()
            parent_id = p.annex_id() or p.doc_id
            p.chapter = p.add({
                "id": provision_id(p.root, "chapter", num),
                "parent_id": parent_id,
                "kind": "chapter",
                "number": num,
                "heading": heading,
                "text": "",
            })
            p.section = p.article = p.clause = p.point = -1

        elif p.chapter >= 0 and section_opens(line, p.article >= 0):
            m = SECTION_LINE.match(line)
            num = roman_to_arabic(m.group(1))
            heading = m.group(2).strip()
            parent_id = p.at(p.chapter)["id"]
            p.section = p.add({
                "id": provision_id(parent_id, "section", num),
                "parent_id": parent_id,
                "kind": "section",
                "number": num,
                "heading": heading,
                "text": "",
            })
            p.article = p.clause = p.point = -1

        elif m_art:
            art_num = m_art.group(1)
            heading = m_art.group(2) or m_art.group(3) or ""
            parent_id = p.root
            if p.section >= 0:
                parent_id = p.at(p.section)["id"]
            elif p.chapter >= 0:
                parent_id = p.at(p.chapter)["id"]

            p.article = p.add({
                "id": provision_id(p.root, "article", art_num),
                "parent_id": parent_id,
                "kind": "article",
                "number": art_num,
                "heading": heading.strip(),
                "text": "",
            })
            p.clause = p.point = -1
            saw_article = True

        elif p.article >= 0 and m_clause:
            cl_num = m_clause.group(1)
            cl_text = (m_clause.group(2) or "").strip()
            art_id = p.at(p.article)["id"]
            p.clause = p.add({
                "id": provision_id(art_id, "clause", cl_num),
                "parent_id": art_id,
                "kind": "clause",
                "number": cl_num,
                "heading": "",
                "text": cl_text,
            })
            p.point = -1

        elif p.clause >= 0 and m_point:
            pt_num = m_point.group(1)
            pt_text = (m_point.group(2) or "").strip()
            cl_id = p.at(p.clause)["id"]
            p.point = p.add({
                "id": provision_id(cl_id, "point", pt_num),
                "parent_id": cl_id,
                "kind": "point",
                "number": pt_num,
                "heading": "",
                "text": pt_text,
            })

        elif p.point >= 0:
            p.append_text(p.point, line)
        elif p.clause >= 0:
            p.append_text(p.clause, line)
        elif p.article >= 0:
            p.append_text(p.article, line)
        elif p.section >= 0 and p.article < 0:
            add_heading(p.at(p.section), line)
        elif p.chapter >= 0 and p.article < 0:
            add_heading(p.at(p.chapter), line)
        elif p.annex >= 0:
            p.append_text(p.annex, line)

        i += 1

    for prov in p.provisions:
        if prov.get("text"):
            prov["text_hash"] = hash_text(prov["text"])

    return p.provisions


def parse_document(raw_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a single document record.
    raw_doc must contain: official_number, issuing_body, title, doc_type, content_html, ...
    """
    off_num = str(raw_doc.get("so_ky_hieu") or "").strip()
    issuing = str(raw_doc.get("co_quan_ban_hanh") or "").strip()
    title = str(raw_doc.get("title") or "").strip()
    raw_html = raw_doc.get("content_html") or ""

    d_id = doc_id_in(off_num, issuing)

    doc_node = {
        "id": d_id,
        "official_number": off_num,
        "issuing_body": issuing,
        "title": title,
        "doc_type": str(raw_doc.get("loai_van_ban") or ""),
        "effective_from": iso_date(raw_doc.get("ngay_co_hieu_luc")),
        "signed_on": iso_date(raw_doc.get("ngay_ban_hanh")),
        "expired_on": iso_date(raw_doc.get("ngay_het_hieu_luc")),
        "force_status": str(raw_doc.get("tinh_trang_hieu_luc") or ""),
        "source": "th1nhng0",
        "source_url": f"https://vbpl.vn/pages/portal.aspx?ItemID={raw_doc.get('id', '')}",
        "status": "parsed",
        "quarantine": "",
    }

    if not raw_html:
        doc_node["status"] = "metadata"
        return {"document": doc_node, "provisions": []}

    plain_text = html_to_text(raw_html)
    front, body = split_front_matter(plain_text)

    if front.get("Ngày hiệu lực"):
        doc_node["effective_from"] = iso_date(front["Ngày hiệu lực"])

    reason = quarantine_reason(off_num, body)
    if reason:
        doc_node["status"] = "quarantined"
        doc_node["quarantine"] = reason
        return {"document": doc_node, "provisions": []}

    provisions = parse_body(d_id, body)
    return {"document": doc_node, "provisions": provisions}

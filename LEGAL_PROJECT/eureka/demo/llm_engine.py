
import os
import re
import html
import time
import shutil
import subprocess
import requests

# =====================================================
# 1. CẤU HÌNH LLM
# =====================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:7b"
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)

client = None
ollama_llm = None
ollama_process = None
ollama_error = None


# =====================================================
# 2. KHỞI TẠO OPENAI
# =====================================================

def initialize_openai():

    global client

    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Chưa cấu hình biến môi trường OPENAI_API_KEY."
            )

        client = OpenAI(api_key=api_key)

        print("Đã khởi tạo OpenAI thành công.")

        return True

    except Exception as e:
        client = None
        print(f"Lỗi khởi tạo OpenAI: {e}")
        return False


# =====================================================
# 3. KIỂM TRA OLLAMA SERVER
# =====================================================

def is_ollama_running():

    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=3
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


# =====================================================
# 4. KHỞI ĐỘNG OLLAMA SERVER
# =====================================================

def start_ollama():

    global ollama_process

    # Nếu Ollama đã chạy thì không khởi động lần nữa
    if is_ollama_running():
        print("Ollama Server đang hoạt động.")
        return True

    try:
        ollama_executable = os.getenv(
            "OLLAMA_EXECUTABLE",
            "ollama"
        )

        # Tìm file thực thi Ollama
        executable_path = shutil.which(ollama_executable)

        if not executable_path and os.path.isfile(ollama_executable):
            executable_path = ollama_executable

        if not executable_path:
            raise RuntimeError(
                "Không tìm thấy ollama.exe. "
                "Hãy cài Ollama hoặc cấu hình OLLAMA_EXECUTABLE."
            )

        # Thiết lập tiến trình cho Windows
        process_options = {}

        if os.name == "nt":
            process_options["creationflags"] = (
                subprocess.CREATE_NO_WINDOW
            )

        ollama_process = subprocess.Popen(
            [executable_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **process_options
        )

        # Chờ Ollama khởi động
        for _ in range(20):

            if is_ollama_running():
                print("Khởi động Ollama Server thành công.")
                return True

            # Kiểm tra tiến trình có bị dừng không
            if ollama_process.poll() is not None:
                raise RuntimeError(
                    "Tiến trình Ollama đã dừng trước khi Server hoạt động."
                )

            time.sleep(1)

        raise RuntimeError(
            "Ollama Server không phản hồi sau 20 giây."
        )

    except Exception as e:
        print(f"Lỗi khởi động Ollama: {e}")
        return False


# =====================================================
# 5. KIỂM TRA MODEL OLLAMA
# =====================================================

def check_ollama_model():

    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )

        response.raise_for_status()

        models = response.json().get("models", [])

        model_names = [
            item.get("name", "")
            for item in models
        ]

        model_exists = any(
            name == OLLAMA_MODEL
            or name.startswith(OLLAMA_MODEL + ":")
            for name in model_names
        )

        if not model_exists:
            raise RuntimeError(
                f"Chưa tìm thấy model {OLLAMA_MODEL}. "
                f"Hãy chạy lệnh: ollama pull {OLLAMA_MODEL}"
            )

        print(f"Đã tìm thấy model: {OLLAMA_MODEL}")

        return True

    except Exception as e:
        raise RuntimeError(
            f"Lỗi kiểm tra model Ollama: {e}"
        )


# =====================================================
# 6. KHỞI TẠO OLLAMA LLM
# =====================================================

def initialize_ollama():

    global ollama_llm
    global ollama_error

    try:
        # Bước 1: Khởi động Server
        if not start_ollama():
            raise RuntimeError(
                "Không thể khởi động Ollama Server."
            )

        # Bước 2: Kiểm tra model
        check_ollama_model()

        # Bước 3: Khởi tạo ChatOllama
        from langchain_ollama import ChatOllama

        ollama_llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            timeout=120
        )

        ollama_error = None

        print(
            f"Khởi tạo Ollama LLM thành công: {OLLAMA_MODEL}"
        )

        return True

    except Exception as e:

        ollama_llm = None
        ollama_error = str(e)

        print(f"Lỗi khởi tạo Ollama: {ollama_error}")

        return False


# =====================================================
# 7. KHỞI TẠO NHÀ CUNG CẤP LLM
# =====================================================

if LLM_PROVIDER == "openai":

    initialize_openai()

elif LLM_PROVIDER == "ollama":

    initialize_ollama()

else:

    print(
        f"LLM_PROVIDER không hợp lệ: {LLM_PROVIDER}"
    )


# =====================================================
# 8. LÀM SẠCH DỮ LIỆU CẤU TRÚC
# =====================================================

def clean_structural_content(structural_contents):

    structural_text = []

    for idx, item in enumerate(
        structural_contents or [],
        start=1
    ):

        raw_text = item.get("text", "")

        clean_text = html.unescape(str(raw_text))

        clean_text = re.sub(
            r"<[^>]*>",
            " ",
            clean_text
        )

        clean_text = " ".join(clean_text.split())

        structural_text.append(
            f"{idx}. {clean_text}"
        )

    return structural_text


# =====================================================
# 9. CHUẨN BỊ EVIDENCE
# =====================================================

def prepare_evidence(evidence_list):

    evidence_text = []

    for idx, ev in enumerate(
        evidence_list or [],
        start=1
    ):

        target = ev.get("target_node") or {}

        name = (
            target.get("name_vi")
            or target.get("name")
            or ev.get("target_node_id")
            or "Chưa có tên node"
        )

        relation = ev.get(
            "relation",
            "UNKNOWN"
        )

        evidence_text.append(
            f"{idx}. Quan hệ: {relation}\n"
            f"   Nội dung: {name}\n"
            f"   Nguồn: "
            f"{ev.get('source_reference') or 'Chưa có'}"
        )

    return evidence_text


# =====================================================
# 10. TẠO PROMPT TỪ KNOWLEDGE GRAPH
# =====================================================

def build_prompt(
    question,
    evidence_list,
    structural_contents=None,
    paths=None
):

    evidence_text = prepare_evidence(
        evidence_list
    )

    structural_text = clean_structural_content(
        structural_contents
    )

    reasoning_text = "\n".join(
        f"{idx}. {path}"
        for idx, path in enumerate(
            paths or [],
            start=1
        )
    )

    prompt = f"""
Bạn là AI Legal Agent hỗ trợ tra cứu pháp luật Việt Nam.

NGUYÊN TẮC BẮT BUỘC:

1. Chỉ sử dụng dữ liệu được cung cấp từ Knowledge Graph.
2. Không tự tạo điều luật, khoản, điểm, nghị định hoặc án lệ.
3. Không khẳng định dữ liệu demo là pháp luật hiện hành.
4. Nếu không có căn cứ, phải nói rõ dữ liệu chưa đủ.
5. Phân biệt rõ điều kiện và thủ tục.
6. Không tự tạo số hiệu hoặc nguồn trích dẫn.
7. Không suy diễn nội dung không xuất hiện trong dữ liệu.

CÂU HỎI NGƯỜI DÙNG:

{question}

CẤU TRÚC VĂN BẢN PHÁP LUẬT:

{chr(10).join(structural_text) or "Không có dữ liệu"}

ĐƯỜNG SUY LUẬN KNOWLEDGE GRAPH:

{reasoning_text or "Không có dữ liệu"}

CÁC QUAN HỆ VÀ ĐIỀU KIỆN:

{chr(10).join(evidence_text) or "Không có dữ liệu"}

YÊU CẦU TRẢ LỜI:

Trình bày bằng tiếng Việt theo cấu trúc:

1. Nội dung liên quan.
2. Các điều kiện hoặc thủ tục được tìm thấy.
3. Căn cứ trong Knowledge Graph.
4. Giới hạn dữ liệu và thông tin chưa xác minh.

Nếu dữ liệu chỉ là dữ liệu demo, phải ghi rõ điều đó.
"""

    return prompt


# =====================================================
# 11. GỌI OPENAI
# =====================================================

def call_openai(prompt):

    global client

    if client is None:

        if not initialize_openai():
            raise RuntimeError(
                "Không thể khởi tạo OpenAI."
            )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý pháp luật Việt Nam. "
                    "Không được suy diễn ngoài dữ liệu."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        timeout=60
    )

    return response.choices[0].message.content


# =====================================================
# 12. GỌI OLLAMA
# =====================================================

def call_ollama(prompt):

    global ollama_llm

    if ollama_llm is None:

        if not initialize_ollama():
            raise RuntimeError(
                ollama_error or "Không thể khởi tạo Ollama."
            )

    response = ollama_llm.invoke(prompt)

    return response.content


# =====================================================
# 13. HÀM SINH CÂU TRẢ LỜI CHÍNH
# =====================================================

def generate_answer(
    question,
    evidence_list,
    intent="condition_query",
    structural_contents=None,
    paths=None
):

    # Kiểm tra phạm vi câu hỏi
    if intent is None:

        return (
            "Xin lỗi, câu hỏi nằm ngoài phạm vi hỗ trợ "
            "của hệ thống AI Legal Agent."
        )

    # Kiểm tra dữ liệu KG
    if not evidence_list and not structural_contents:

        return (
            "Knowledge Graph hiện chưa có dữ liệu đủ căn cứ "
            "để trả lời câu hỏi này."
        )

    # Tạo prompt
    prompt = build_prompt(
        question=question,
        evidence_list=evidence_list,
        structural_contents=structural_contents,
        paths=paths
    )

    # Gọi mô hình theo nhà cung cấp
    try:

        if LLM_PROVIDER == "openai":

            return call_openai(prompt)

        elif LLM_PROVIDER == "ollama":

            return call_ollama(prompt)

        else:

            return (
                "Nhà cung cấp LLM chưa được cấu hình đúng. "
                "Hãy kiểm tra biến LLM_PROVIDER."
            )

    except Exception as e:

        print(f"Lỗi sinh câu trả lời: {e}")

        return (
            "Không thể tạo câu trả lời từ mô hình AI.\n\n"
            f"Chi tiết lỗi: {str(e)}"
        )

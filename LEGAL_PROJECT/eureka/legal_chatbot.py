
import sys
import streamlit as st

from src.agents.legal_crew_service import run_legal_crew


# ==========================================
# 1. UTF-8
# ==========================================

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(
                encoding="utf-8",
                errors="replace"
            )
        except (OSError, ValueError):
            pass


# ==========================================
# 2. PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Eureka AI Legal Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 3. SESSION STATE
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ==========================================
# 4. SIDEBAR
# ==========================================

with st.sidebar:
    st.title("⚖️ Eureka AI")

    st.markdown("### Thông tin hệ thống")

    st.write("**Knowledge Graph:** Neo4j")
    st.write("**Multi-Agent:** CrewAI")
    st.write("**LLM:** Ollama / Qwen2.5")
    st.write("**Giao diện:** Streamlit")

    st.divider()

    st.markdown("### Trạng thái dữ liệu")

    st.info(
        "Knowledge Graph đang hỗ trợ "
        "tra cứu cấu trúc điều luật."
    )

    st.warning(
        "Nguyên văn và hiệu lực pháp luật "
        "chưa được xác minh đầy đủ."
    )

    st.divider()

    if st.button(
        "🗑️ Xóa lịch sử hội thoại",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()


# ==========================================
# 5. HEADER
# ==========================================

st.title("⚖️ Eureka AI Legal Agent")

st.caption(
    "Hệ thống trợ lý pháp luật AI "
    "sử dụng Knowledge Graph và Multi-Agent"
)

st.info(
    "Hệ thống đang ở giai đoạn thử nghiệm. "
    "Thông tin được truy xuất từ Knowledge Graph "
    "không đồng nghĩa với việc đã kiểm chứng "
    "đầy đủ nội dung hoặc hiệu lực pháp luật."
)


# ==========================================
# 6. HIỂN THỊ KẾT QUẢ
# ==========================================

def display_result(message):
    st.markdown(message["content"])

    article_id = message.get("article_id")
    retrieved = message.get("retrieved", bool(article_id))
    verified = message.get("verified", False)
    errors = message.get("errors", [])

    if article_id:
        st.caption(f"ID điều luật: `{article_id}`")

    if retrieved:
        st.success(
            "Đã tìm thấy điều luật "
            "trong Knowledge Graph."
        )

        st.info(
            "Dữ liệu cấu trúc đã được truy xuất. "
            "Nội dung và hiệu lực pháp luật "
            "chưa được kiểm chứng đầy đủ."
        )

    else:
        st.warning(
            "Chưa tìm thấy điều luật phù hợp "
            "trong Knowledge Graph."
        )

    if verified:
        st.caption(
            "Câu trả lời đã vượt qua "
            "bộ kiểm tra tự động sơ bộ."
        )

    if errors:
        with st.expander("Chi tiết kiểm tra"):
            for error in errors:
                st.write(f"- {error}")


# ==========================================
# 7. LỊCH SỬ HỘI THOẠI
# ==========================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "assistant":
            display_result(message)

        else:
            st.markdown(message["content"])


# ==========================================
# 8. CHAT INPUT
# ==========================================

question = st.chat_input(
    "Nhập câu hỏi pháp luật của bạn..."
)


# ==========================================
# 9. XỬ LÝ CÂU HỎI
# ==========================================

if question:

    question = question.strip()

    if question:

        user_message = {
            "role": "user",
            "content": question
        }

        st.session_state.messages.append(
            user_message
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Đang tra cứu Knowledge Graph "
                "và xử lý các Agent..."
            ):

                try:
                    result = run_legal_crew(question)

                    article_id = result.get("article_id")
                    answer = result.get(
                        "answer",
                        "Chưa có kết quả."
                    )

                    assistant_message = {
                        "role": "assistant",
                        "content": answer,
                        "article_id": article_id,
                        "retrieved": bool(article_id),
                        "verified": result.get(
                            "verified",
                            False
                        ),
                        "errors": result.get(
                            "errors",
                            []
                        )
                    }

                    display_result(assistant_message)

                    st.session_state.messages.append(
                        assistant_message
                    )

                except Exception as exc:
                    st.error(
                        "Không thể xử lý câu hỏi. "
                        "Vui lòng kiểm tra backend, "
                        "Neo4j và Ollama."
                    )

                    with st.expander(
                        "Chi tiết lỗi kỹ thuật"
                    ):
                        st.exception(exc)

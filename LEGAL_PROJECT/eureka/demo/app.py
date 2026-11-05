import streamlit as st
import os

from kg_engine import LegalKG
from retriever import GraphRetriever
from llm_engine import generate_answer
from metrics import run_evaluation, calculate_accuracy

# Tối ưu giao diện toàn trang
st.set_page_config(page_title="Legal Graph-RAG", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS & FontAwesome
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    /* Dark Mode & Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Ẩn các thành phần mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Giao diện Title mượt mà */
    .app-title {
        font-size: 1.5rem; /* Adjusted for longer title */
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        line-height: 1.4;
        display: block; /* Removed flex layout to allow natural wrapping */
        text-align: center;
    }
    
    .app-title i {
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-right: 12px;
    }
    
    /* Headers chuyên nghiệp */
    .premium-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
        border-bottom: 1px solid #334155;
        padding-bottom: 8px;
    }
    
    /* Custom Icon Colors */
    .premium-header i {
        color: #94a3b8;
        font-size: 1.1rem;
    }
    
    /* Giao diện Chat Message (Bot và User) */
    .stChatMessage {
        background-color: transparent !important;
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    /* Custom Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# Define premium Avatars
USER_AVATAR = "https://api.iconify.design/mdi:account-tie.svg?color=%2394a3b8"
BOT_AVATAR = "https://api.iconify.design/mdi:scale-balance.svg?color=%23a78bfa"

# Initialize KG and Retriever only once
@st.cache_resource
def load_engine():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    json_path = os.path.join(
        base_dir,
        "data",
        "json",
        "legal_kg_demo_converted.json"
    )

    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Không tìm thấy Knowledge Graph: {json_path}"
        )

    kg = LegalKG(json_path)
    retriever = GraphRetriever(kg)

    return retriever
retriever = load_engine()

# Main Title
st.markdown('<div class="app-title"><i class="fa-solid fa-gavel"></i> STUDY ON BUILDING AN INTELLIGENT LEGAL ASSISTANT SYSTEM BASED ON MULTI-AGENT ARCHITECTURE AND KNOWLEDGE GRAPH FOR STATUTORY RETRIEVAL IN VIETNAM</div>', unsafe_allow_html=True)

# Sidebar for Evaluation Metrics
with st.sidebar:
    st.markdown('<div class="premium-header"><i class="fa-solid fa-chart-pie"></i> Evaluation Metrics</div>', unsafe_allow_html=True)
    if st.button("Run Evaluation", use_container_width=True):
        with st.spinner("Running Test Cases..."):
            correct, total = run_evaluation(retriever)
            acc_str = calculate_accuracy(correct, total)
            st.success(f"Accuracy: {correct}/{total} test cases ({acc_str})")
    else:
        st.info("Nhấn 'Run Evaluation' để chạy kiểm thử độ chính xác trên tập dữ liệu chuẩn.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing chat messages
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

question = st.chat_input("Nhập câu hỏi pháp luật...")


if question:
    # Hiển thị câu hỏi người dùng
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user", avatar=USER_AVATAR):
        st.write(question)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Đang truy xuất Knowledge Graph và phân tích..."):

            # Bước 1: Tìm thực thể pháp lý
            entities = retriever.search_legal_entity(question)

            if not entities:
                answer = generate_answer(
                    question,
                    [],
                    intent=None
                )

            else:
                # Bước 2: Lấy thực thể phù hợp nhất
                top_entity = entities[0]

                # Bước 3: Truy xuất đường suy luận
                paths, evidence_list, structural_contents = (
                    retriever.get_reasoning_path(top_entity["id"])
                )

                # Bước 4: Sinh câu trả lời từ cả hai nguồn dữ liệu
                answer = generate_answer(
                    question=question,
                    evidence_list=evidence_list,
                    intent="condition_query",
                    structural_contents=structural_contents,
                    paths=paths
                )

                # Hiển thị đường suy luận để kiểm tra
                with st.expander("Xem kết quả truy xuất Knowledge Graph"):
                    st.markdown("**Thực thể được tìm thấy:**")
                    st.json(top_entity)

                    st.markdown("**Reasoning paths:**")
                    for path in paths:
                        st.write(path)

                    st.markdown("**Structural contents:**")
                    st.json(structural_contents)

                    st.markdown("**Evidence:**")
                    st.json(evidence_list)

        st.write(answer)


    # Lưu câu trả lời một lần duy nhất
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
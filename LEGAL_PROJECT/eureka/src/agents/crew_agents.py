
from crewai import Agent
from langchain_community.chat_models import ChatOllama

from src.settings import settings
from src.agents.mcp.servers.graph_server import (
    search_legal_articles_tool,
    get_article_ocr_text_tool,
    get_guiding_decrees_tool,
    get_related_cases_tool,
)


# =====================================================
# 1. KHỞI TẠO LLM
# =====================================================

if settings.LLM_PROVIDER == "ollama":
    llm = ChatOllama(
        model="qwen2.5:7b",
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
    )
else:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.1,
    )


# =====================================================
# 2. AGENT A - TRA CỨU VĂN BẢN LUẬT GỐC
# =====================================================

legal_text_agent = Agent(
    role="Agent A - Tra cứu Văn bản Gốc",
    goal=(
        "Tra cứu các điều luật gốc trong Neo4j theo câu hỏi "
        "và từ khóa pháp lý của người dùng."
    ),
    backstory=(
        "Bạn là chuyên gia tra cứu văn bản pháp luật Việt Nam. "
        "Bạn chỉ đưa ra thông tin có căn cứ từ dữ liệu được truy vấn."
    ),
    tools=[
    search_legal_articles_tool,
    get_article_ocr_text_tool,
    ],
    llm=llm,
    memory=False,
    verbose=True,
    allow_delegation=False,
)


# =====================================================
# 3. AGENT B - TRA CỨU NGHỊ ĐỊNH, THÔNG TƯ HƯỚNG DẪN
# =====================================================

procedure_agent = Agent(
    role="Agent B - Tra cứu Văn bản Hướng dẫn",
    goal=(
        "Tra cứu các Nghị định và Thông tư hướng dẫn "
        "có liên kết với điều luật gốc."
    ),
    backstory=(
        "Bạn là chuyên gia tra cứu hệ thống văn bản pháp luật Việt Nam. "
        "Bạn tập trung xác định các văn bản hướng dẫn thi hành "
        "điều luật và chỉ sử dụng dữ liệu truy vấn được."
    ),
    tools=[get_guiding_decrees_tool],
    llm=llm,
    memory=False,
    verbose=True,
    allow_delegation=False,
)


# =====================================================
# 4. AGENT C - TRA CỨU ÁN LỆ VÀ BẢN ÁN
# =====================================================

case_agent = Agent(
    role="Agent C - Tra cứu Án lệ và Thực tiễn xét xử",
    goal=(
        "Tìm kiếm án lệ và bản án có liên kết với các điều luật "
        "được xác định từ kết quả tra cứu."
    ),
    backstory=(
        "Bạn là chuyên gia phân tích án lệ và thực tiễn xét xử. "
        "Bạn không tự tạo mã án lệ hoặc nội dung bản án."
    ),
    tools=[get_related_cases_tool],
    llm=llm,
    memory=False,
    verbose=True,
    allow_delegation=False,
)


# =====================================================
# 5. AGGREGATOR - TỔNG HỢP KẾT QUẢ
# =====================================================

aggregator_agent = Agent(
    role="Aggregator Agent - Phân cấp và Tổng hợp",
    goal=(
        "Tổng hợp kết quả tra cứu thành câu trả lời pháp lý rõ ràng, "
        "có cấu trúc. Phân biệt văn bản luật, văn bản hướng dẫn "
        "và án lệ; nêu rõ khi dữ liệu không đủ căn cứ."
    ),
    backstory=(
        "Bạn là chuyên gia tổng hợp thông tin pháp luật Việt Nam. "
        "Bạn không được suy diễn hoặc tạo ra điều luật, nghị định, "
        "thông tư hay án lệ không có trong dữ liệu đầu vào."
    ),
    tools=[],
    llm=llm,
    memory=False,
    verbose=True,
    allow_delegation=False,
)

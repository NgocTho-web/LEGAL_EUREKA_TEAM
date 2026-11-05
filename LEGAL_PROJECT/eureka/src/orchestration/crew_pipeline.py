from crewai import Task, Crew, Process
from src.agents.crew_agents import (
    legal_text_agent, 
    procedure_agent, 
    case_agent, 
    aggregator_agent
)

def run_parallel_legal_crew(user_query: str) -> str:
    task_a = Task(
        description=f"Tìm mã Điều luật chính và nội dung gốc liên quan đến câu hỏi: '{user_query}'",
        expected_output="Mã Điều luật chính (Ví dụ: Dieu_188) và nội dung gốc.",
        agent=legal_text_agent
    )

    task_b = Task(
        description="Tra cứu các Nghị định/Thông tư hướng dẫn (quan hệ GUIDES) từ mã Điều luật của Agent A.",
        expected_output="Danh sách các Nghị định/Thông tư hướng dẫn.",
        agent=procedure_agent,
        context=[task_a],
        async_execution=True
    )

    task_c = Task(
        description="Tra cứu các Án lệ (quan hệ APPLIED_IN) từ mã Điều luật của Agent A.",
        expected_output="Danh sách các Án lệ áp dụng.",
        agent=case_agent,
        context=[task_a],
        async_execution=True
    )

    task_aggregate = Task(
        description="""
        Gom thông tin từ Task A, Task B, Task C. Trả lời bằng tiếng Việt và sắp xếp theo thứ tự hiệu lực pháp lý:
        1. Bộ luật / Luật gốc (ghi rõ Điều mấy)
        2. Nghị định / Thông tư hướng dẫn
        3. Án lệ thực tế
        """,
        expected_output="Câu trả lời pháp lý hoàn chỉnh bằng tiếng Việt kèm trích dẫn rõ ràng.",
        agent=aggregator_agent,
        context=[task_a, task_b, task_c]
    )

    legal_crew = Crew(
        agents=[legal_text_agent, procedure_agent, case_agent, aggregator_agent],
        tasks=[task_a, task_b, task_c, task_aggregate],
        process=Process.sequential,
        verbose=True
    )

    return str(legal_crew.kickoff())
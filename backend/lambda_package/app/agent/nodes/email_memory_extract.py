from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

llm = ChatOpenAI(temperature=0)

def extract_memory_from_email(state: dict) -> dict:
    email_text = state.get("tool_result", "")

    prompt = f"""
Extract important long-term facts from this email.

Examples:
"Project X is delayed by 2 weeks" →
type: project_status
key: Project X
value: delayed by 2 weeks

If nothing important, return NONE.

Email:
{email_text}
"""

    resp = llm.invoke([
        SystemMessage(content="Extract factual memory."),
        HumanMessage(content=prompt)
    ]).content.strip()

    if resp == "NONE":
        return state

    state["extracted_memory"] = resp
    state["memory_source"] = "email"
    return state

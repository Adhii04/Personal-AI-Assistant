from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

llm = ChatOpenAI(temperature=0)

def extract_memory_from_chat(state: dict) -> dict:
    prompt = f"""
Extract any long-term memory from this message.

If nothing important, return NONE.

Message:
"{state['message']}"

Examples:
"I hate 9 AM meetings" →
type: preference
key: meeting_time
value: dislikes 9 AM meetings
"""

    resp = llm.invoke([
        SystemMessage(content="You extract structured memory."),
        HumanMessage(content=prompt)
    ]).content.strip()

    if resp == "NONE":
        return state

    state["extracted_memory"] = resp
    return state

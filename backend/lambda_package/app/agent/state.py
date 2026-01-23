from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    user_id: int
    message: str
    intent: Optional[str]
    memories: Optional[List[str]]
    tool_result: Optional[str]
    final_response: Optional[str]

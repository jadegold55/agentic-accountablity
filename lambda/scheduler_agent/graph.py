from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
import os
from state import SchedulerState
from tools import tools
from prompts import COMMAND_SYSTEM_PROMPT, SCHEDULE_SYSTEM_PROMPT
from langchain_core.messages import SystemMessage

llm = ChatGroq(model=os.getenv("SCHEDULER_LLM_MODEL", "llama-3.1-8b-instant"))
llm_with_tools = llm.bind_tools(tools)


def route_after_tools(state: SchedulerState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return "agent"

    last_message = messages[-1]
    tool_name = getattr(last_message, "name", None)
    mode = state.get("mode")

    if mode == "command" and tool_name == "send_message":
        return END

    if mode == "schedule" and tool_name == "send_message":
        return END

    return "agent"


def agent_node(state: SchedulerState) -> dict:
    system_prompt = (
        COMMAND_SYSTEM_PROMPT
        if state.get("mode") == "command"
        else SCHEDULE_SYSTEM_PROMPT
    )
    response = llm_with_tools.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    return {"messages": [response]}


tool_node = ToolNode(tools)
graph = StateGraph(SchedulerState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_conditional_edges("tools", route_after_tools, {"agent": "agent", END: END})
app = graph.compile()

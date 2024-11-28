from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tavily import TavilyClient
import os


load_dotenv()

memory = SqliteSaver.from_conn_string(":memory:")


class AgentState(TypedDict):
    task:str
    plan:str
    draft: str
    critique: str
    content: List[str]
    max_revisions: int
    revision_number: int


model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
or instructions for the sections."""

WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
Generate the best essay possible for the user's request and the initial outline. \
If the user provides critique, respond with a revised version of your previous attempts. \
Utilize all the information below as needed: 

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following essay. Generate a list of search queries that will gather \
any relevant information. Only generate 3 queries max."""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""


class Queries(BaseModel):
    queries: List[str]

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def plan_node(state: AgentState):
    messages = [
        SystemMessage(content=PLAN_PROMPT), 
        HumanMessage(content=state['task'])
    ]
    response = model.invoke(messages)
    return {"plan": response.content}

def research_plan_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_PLAN_PROMPT),
        HumanMessage(content=state['task'])
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content, "queries": queries.queries}


def generation_node(state: AgentState):
    content = "\n\n".join(state['content'] or [])
    user_message = HumanMessage(
        content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
    messages = [
        SystemMessage(
            content=WRITER_PROMPT.format(content=content)
        ),
        user_message
        ]
    response = model.invoke(messages)
    return {
        "draft": response.content, 
        "revision_number": state.get("revision_number", 1) + 1
    }

def reflection_node(state: AgentState):
    messages = [
        SystemMessage(content=REFLECTION_PROMPT), 
        HumanMessage(content=state['draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content}

def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state['critique'])
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content, "queries": queries.queries}

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"


builder = StateGraph(AgentState)

builder.add_node("planner", plan_node)
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.add_node("research_plan", research_plan_node)
builder.add_node("research_critique", research_critique_node)

builder.set_entry_point("planner")

builder.add_conditional_edges(
    "generate", 
    should_continue, 
    {END: END, "reflect": "reflect"}
)

builder.add_edge("planner", "research_plan")
builder.add_edge("research_plan", "generate")

builder.add_edge("reflect", "research_critique")
builder.add_edge("research_critique", "generate")

# graph = builder.compile(checkpointer=memory)
graph = builder.compile()


if __name__ == "__main__":
    thread = {"configurable": {"thread_id": "1"}}

    # Initialize the state
    config = {
        "task": "Write an essay about the impact of artificial intelligence on society",
        "plan": "",
        "draft": "",
        "critique": "",
        "content": [],
        "max_revisions": 2,
        "revision_number": 0
    }
    
    # Run the graph
    for output in graph.stream(config, thread):
        # The output contains the updates to the state
        for key, value in output.items():
            if key != 'configurable':  # Skip the thread configuration
                print(f"\nExecuting node: {key}")
                print("-" * 50)
                
                if "plan" in value:
                    print("Generated Plan:", value["plan"])
                elif "content" in value:
                    print("Research Content Count:", len(value["content"]))
                elif "draft" in value:
                    print("Generated Draft:", value["draft"])
                    print("Revision Number:", value.get("revision_number"))
                elif "critique" in value:
                    print("Critique:", value["critique"])
                    
    print("\nFinal State:")
    print("============")
    # Get the final state by applying all updates
    final_state = config.copy()
    for output in graph.stream(config, thread):
        for key, value in output.items():
            if key != 'configurable':
                final_state.update(value)
    print("Final Draft:", final_state.get("draft"))

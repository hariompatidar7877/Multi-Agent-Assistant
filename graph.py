from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from typing import Literal
from state import BlogState

from agents import get_llm, researcher_agent, writer_agent, editor_agent

MAX_REVISION = 4


#### Node - Edges

### Define nodes

def researcher_node(state:BlogState):
    """Researcher Agents geneates {or revises} the research outlines"""
    llm = get_llm()
    researcher_data = researcher_agent(
        llm= llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.research_feedback
    )


    state.research = researcher_data
    state.research_feedback = ""

    return state


def human_review_research_node(state:BlogState):
    """Pause and ask the human tp approve the research or send the feedback"""
    decision = interrupt({
        "stage" : "researcher_review",
        "research":state.research,
        "instructions":(
            "Reply with 'approve' to coutinue to writing. "
            "or describe what to change to send it back to the researcher"
        )
    })
    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision)
        action="approve" if text.lower() in ["approve", "ok","yes","process",""] else "revise"
        feedback= " " if action == "approve" else text


    state.research_feedback = feedback

    return state

def writer_node(state:BlogState):
    """Writer Agents produce the full draft blog {or revise it}"""
    llm = get_llm()
    draft_data = writer_agent(
        llm= llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.draft_feedback
    )


    state.draft = draft_data
    state.draft_feedback = ""

    return state

def human_review_draft_node(state:BlogState):
    """Pause and ask the human tp approve the draft or send the feedback"""
    decision = interrupt({
        "stage" : "draft_review",
        "draft":state.draft,
        "instructions":(
            "Reply with 'approve' to coutinue to sent the editor. "
            "or describe what to change to send it back to the writer"
        )
    })
    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision)
        action="approve" if text.lower() in ["approve", "ok","yes","process",""] else "revise"
        feedback= " " if action == "approve" else text


    state.draft_feedback = feedback

    return state

def editor_node(state:BlogState):
    llm = get_llm()
    final = editor_agent(
        llm=llm,
        topic=state.topic,
        draft=state.draft,
        audience=state.audience
    )
    state.final_blog=final
    return state

#### Conditional Edges
def route_after_research_review(state:BlogState)->Literal["research", "writer"]:
    if state.research_feedback:
        return "research"
    else:
        return "writer"

def route_after_draft_review(state:BlogState)->Literal["edit", "writer"]:
    if state.draft_feedback and state.revision_count<MAX_REVISION:
        return "writer"
    else:
        return "edit"



#### Build and Compile the graph

def build_blog_graph():
    builder = StateGraph(BlogState)


    ### ADD NODES
    builder.add_node("research", researcher_node)
    builder.add_node("review_research", human_review_research_node)
    builder.add_node("writer", writer_node)
    builder.add_node("review_draft", human_review_draft_node)
    builder.add_node("edit", editor_node)


    ### ADD EDGES

    builder.add_edge(START, "research")
    builder.add_edge("research", "review_research" )
    builder.add_conditional_edges("review_research", 
                                  route_after_research_review,
                                  {"research": "research", "writer":"writer"}

                                  )
    builder.add_edge("writer", "review_draft")
    builder.add_conditional_edges("review_draft", 
                                    route_after_draft_review,
                                    {"writer":"writer", "edit":"edit" }
    
                                  )
    builder.add_edge("edit", END)

####ADD CON EDGES

    GRAPH = builder.compile(checkpointer=InMemorySaver())

    return GRAPH







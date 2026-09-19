import os 
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


#### GET LLM
def get_llm(model_name: str= "openai/gpt-oss-20b", temperature : float = 0.5):
    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model=model_name, temperature=temperature, api_key=api_key)
    return llm


### Research Agent
RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    {"role" : "system", "content": """
        "You are a Research Agent. Given a blog topic and target audience, produce a clear,
        "structured research outline. Include:\n"
        "1. 5-7 key points the blog should cover\n"
        "2. Important facts, stats, or examples for each point\n"
        "3. Suggested angle or hook\n"
        "Be concise. Use bullet points. Do NOT write the full blog yet."

          """},
    {"role":"user", "content": "Topic: {topic}, Audience:{audience}, revision:{revision_hints}, Write the research outline now. "}
])

### define research_agent
def researcher_agent(llm:ChatGroq, topic: str, audience:str, feedback: str= "")-> str:
    revision_hints = f"The human provided this feedback on your previous research - please address it : {feedback}."
    if not feedback:
        revision_hints = "This is your first attempt"

    chain = RESEARCHER_PROMPT | llm

    result = chain.invoke(
        {
            "topic": topic,
            "audience": audience,
            "revision_hints": revision_hints
        }
    )
    return result.content


#### Writer Agent
WRITER_PROMPT = ChatPromptTemplate.from_messages([
    {"role" : "system", "content": """
        "You are a Blog Writer Agent. Using the research notes provided, write a complete, "
        "engaging blog post.\n"
        "Rules: \n"
        "-Length: 500-800 words\n"
        "-Structure: catch title, intro hook, 3-5 sections with H2 headings, conclusion\n"
        "-Tone: clear, friendly, suited to the target audience\n"
        "-Use markdown formatting\n"
        "Do NOT add a 'word count' line at the end"
                      """},
    {"role":"user", "content":"""
        Topic : {topic},
        Audience : {audience},
        Research Notes: {research}
        (revision_hints)
        Write the full blog post now
     """}
])



### define writer_agent
def writer_agent(llm:ChatGroq, topic: str, audience:str, research:str="", feedback: str= "")-> str:
    revision_hints = f"The human provided this feedback on your previous draft  and asked for  these changes- {feedback}. Please apply these changes during writting the blog."
    if not feedback:
        revision_hints = "This is your first attempt"

    chain = WRITER_PROMPT | llm

    result = chain.invoke(
        {
            "topic": topic,
            "audience": audience,
            "research":research,
            "revision_hints": revision_hints
        }
    )
    return result.content



### Editor Agent

EDITOR_PROMPT = ChatPromptTemplate.from_messages([
    {"role" : "system", "content": """
            "You are an Editor Agent the final quality gate before publishing.\n"
            "Take the draft and produce the FINAL polished version. Specifically:\n"
            "- Fix grammar, spelling, and awkward phrasing\n"
            "- Tighten wordy sentences\n"
            "-Improve flow and transitions between sections\n"
            "- Make the title and intro more compelling if needed\n"
            "- Keep the same structure and markdown formatting\n"
            "-Blog Wroding should look like human. not a AI, and don't any special char and complex/ fancy words.\n"
            "Output only the final polished blog post no commentary."
                         """},
        {"role":"user", "content":"""
            Topic : {topic},
            Audience : {audience},
            Draft : {draft}
        
            Return the publish blog post.
                            """}
])

### define Editor_agent
def editor_agent(llm:ChatGroq, topic: str, audience : str,  draft : str = "")-> str:

    chain = EDITOR_PROMPT | llm

    result = chain.invoke(
        {
            "topic": topic,
            "audience": audience,
            "draft": draft
        }
    )
    return result.content
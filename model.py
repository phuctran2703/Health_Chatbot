import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from rag import retrieval_tool

# Load environment variables
load_dotenv()

# Initialize LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp"
    )
else:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# Define tools for the agent
tools = [retrieval_tool]

# Create the health chatbot agent
health_chatbot = create_react_agent(llm, tools)

def get_health_chatbot():
    """Return the configured health chatbot agent"""
    return health_chatbot

def stream_chat_with_agent(message: str, config=None):
    """
    Stream chat with the health agent
    
    Args:
        message (str): User's message/question
        config (dict, optional): Configuration for the agent
    
    Yields:
        str: Chunks of agent's response
    """
    try:
        if config is None:
            config = {"configurable": {"thread_id": "health_chat"}}
        
        # Stream the agent's response
        for chunk in health_chatbot.stream(
            {"messages": [("user", message)]},
            config=config
        ):
            # Extract content from different types of chunks
            if "agent" in chunk:
                if "messages" in chunk["agent"]:
                    for msg in chunk["agent"]["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content
            elif "tools" in chunk:
                # Handle tool calls if needed
                continue
                
    except Exception as e:
        yield f"Có lỗi xảy ra: {str(e)}"

if __name__ == "__main__":
    # Test the health chatbot
    test_message = "Cách điều trị cảm lạnh?"
    print(f"Testing health chatbot with: {test_message}")
    print("=" * 50)
    
    print("Streaming response:")
    for chunk in stream_chat_with_agent(test_message):
        print(chunk, end="", flush=True)
    print("\n" + "=" * 50)

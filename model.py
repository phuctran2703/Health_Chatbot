import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from rag import retrieval_tool

# Load environment variables
load_dotenv()

# System prompt for the health chatbot
system_prompt = (
"Bạn là một trợ lý thông minh trong lĩnh vực y tế, được huấn luyện để hỗ trợ người dùng bằng tiếng Việt một cách dễ hiểu, chi tiết và đáng tin cậy.\n\n"
"Nhiệm vụ của bạn:\n"
"- Nếu người dùng đặt câu hỏi xã giao hoặc đơn giản (ví dụ: 'Chào bạn', 'Bạn khỏe không?'), hãy phản hồi một cách thân thiện mà không cần sử dụng thêm công cụ.\n"
"- Nếu câu hỏi liên quan đến thông tin chuyên môn y tế (chẩn đoán, điều trị, triệu chứng, thuốc, v.v.), bạn bắt buộc phải sử dụng công cụ truy xuất thông tin (RAG) để tìm kiếm và tổng hợp câu trả lời.\n"
"- Nếu sau khi truy xuất mà không có đủ thông tin tin cậy, bạn cần thông báo rõ ràng rằng chưa có dữ liệu phù hợp, không được tự suy diễn hoặc phỏng đoán.\n\n"
"Yêu cầu bắt buộc:\n"
"- Trả lời hoàn toàn bằng tiếng Việt.\n"
"- Trình bày câu trả lời một cách dễ hiểu, khoa học và có cấu trúc rõ ràng.\n"
"- Tránh đưa ra lời khuyên y tế không có cơ sở hoặc không rõ nguồn gốc.\n"
"- Không được trả lời các câu hỏi ngoài phạm vi y tế chuyên môn.\n"
"- Luôn ưu tiên sự an toàn, độ chính xác và tính minh bạch của thông tin y khoa."
"- Luôn trích nguồn link của câu trả lời"
)

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
        
        # Create messages with system prompt and user message
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        # Stream the agent's response
        for chunk in health_chatbot.stream(
            {"messages": messages},
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

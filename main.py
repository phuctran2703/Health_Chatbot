from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import chromadb
import os
import json
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Gemini AI imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

app = FastAPI(title="Health Chatbot API", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ChromaDB client configuration
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = os.getenv("CHROMADB_PORT", "8001")
CHROMADB_URL = f"http://{CHROMADB_HOST}:{CHROMADB_PORT}"

# Google Gemini AI configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=1000
    )
else:
    llm = None
    print("Warning: GOOGLE_API_KEY not found. Gemini AI features will be disabled.")

class HealthQuery(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    try:
        # Kiểm tra kết nối với ChromaDB bằng cách kết nối trực tiếp
        client = chromadb.HttpClient(host=CHROMADB_HOST, port=int(CHROMADB_PORT))
        # Thử tạo hoặc lấy collection để test kết nối
        collections = client.list_collections()
        chromadb_status = "connected"
    except Exception as e:
        chromadb_status = f"error: {str(e)}"
    
    # Kiểm tra trạng thái Gemini AI
    gemini_status = "available" if llm and GOOGLE_API_KEY else "not_configured"
    
    return {
        "status": "healthy", 
        "message": "Service is up and running",
        "chromadb_status": chromadb_status,
        "chromadb_url": CHROMADB_URL,
        "gemini_ai_status": gemini_status
    }

@app.post("/chat/stream")
async def chx1tream(query: HealthQuery):
    def generate_response():
        try:
            # Sử dụng Gemini AI nếu có
            if llm and GOOGLE_API_KEY:
                try:
                    # Tạo system prompt cho chatbot y tế
                    system_prompt = """Bạn là một chatbot chuyên về sức khỏe và y tế. Hãy trả lời các câu hỏi một cách chính xác, hữu ích và dễ hiểu. 
                    
                    Nguyên tắc quan trọng:
                    - Luôn khuyến khích người dùng đến gặp bác sĩ khi cần thiết
                    - Không tự chẩn đoán bệnh
                    - Đưa ra lời khuyên chung về sức khỏe
                    - Sử dụng tiếng Việt tự nhiên và thân thiện
                    - Chỉ trả lời các câu hỏi liên quan đến sức khỏe, không trả lời các câu hỏi ngoài lĩnh vực y tế
                    - Nếu không chắc chắn, hãy thành thật nói không biết
                    """
                    
                    # Gọi Gemini AI với streaming
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=query.question)
                    ]
                    
                    # Gửi metadata trước
                    yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': True})}\n\n"
                    
                    # Stream thật từ Gemini AI
                    for chunk in llm.stream(messages):
                        if chunk.content:
                            # Gửi từng chunk như Gemini AI trả về
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"
                            time.sleep(0.05)  # Delay nhỏ để mượt hơn
                    
                    # Gửi signal kết thúc
                    yield f"data: {json.dumps({'type': 'end', 'status': 'success'})}\n\n"
                    return
                    
                except Exception as ai_error:
                    print(f"Gemini AI error: {ai_error}")
                    # Fallback to basic response
                    pass
            
            # Fallback response nếu không có AI hoặc có lỗi
            fallback_text = f"Cảm ơn bạn đã hỏi về '{query.question}'. Tôi là chatbot sức khỏe và khuyến khích bạn tham khảo ý kiến bác sĩ để được tư vấn chính xác nhất về vấn đề sức khỏe."
            
            # Gửi metadata
            yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': False})}\n\n"
            
            # Stream từng từ
            words = fallback_text.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'word', 'content': word, 'index': i})}\n\n"
                time.sleep(0.08)
            
            yield f"data: {json.dumps({'type': 'end', 'status': 'success'})}\n\n"
            
        except Exception as e:
            print(f"Stream chat error: {e}")
            error_text = f"Xin chào! Cảm ơn bạn đã hỏi về '{query.question}'. Hiện tại tôi đang gặp một chút khó khăn kỹ thuật nhưng vẫn có thể trò chuyện với bạn. Để được tư vấn chính xác về sức khỏe, bạn nên tham khảo ý kiến bác sĩ chuyên khoa nhé!"
            
            yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': False})}\n\n"
            
            words = error_text.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'word', 'content': word, 'index': i})}\n\n"
                time.sleep(0.08)
            
            yield f"data: {json.dumps({'type': 'end', 'status': 'limited'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

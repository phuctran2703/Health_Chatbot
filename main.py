from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
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

# Import health chatbot agent
from model import health_chatbot, stream_chat_with_agent

app = FastAPI(title="Health Chatbot API", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    # Kiểm tra trạng thái Gemini AI và RAG system
    gemini_status = "available" if llm and GOOGLE_API_KEY else "not_configured"
    
    try:
        # Test health chatbot agent
        agent_status = "available" if health_chatbot else "not_available"
    except:
        agent_status = "error"
    
    return {
        "status": "healthy", 
        "message": "Service is up and running",
        "gemini_ai_status": gemini_status,
        "rag_agent_status": agent_status
    }

@app.post("/chat/stream")
async def chat_stream(query: HealthQuery):
    def generate_response():
        try:
            # Sử dụng RAG agent trước
            if health_chatbot and GOOGLE_API_KEY:
                try:
                    # Gửi metadata trước
                    yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': True, 'rag_enabled': True})}\n\n"
                    
                    # Stream từ RAG agent
                    config = {"configurable": {"thread_id": f"health_chat_{int(time.time())}"}}
                    
                    for chunk in stream_chat_with_agent(query.question, config):
                        if chunk and chunk.strip():
                            # Gửi từng chunk từ agent
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                            time.sleep(0.05)  # Delay nhỏ để mượt hơn
                    
                    # Gửi signal kết thúc
                    yield f"data: {json.dumps({'type': 'end', 'status': 'success'})}\n\n"
                    return
                    
                except Exception as agent_error:
                    print(f"RAG Agent error: {agent_error}")
                    # Fallback to basic response
                    pass
            
            # Fallback response nếu không có AI hoặc có lỗi
            fallback_text = f"Cảm ơn bạn đã hỏi về '{query.question}'. Tôi là chatbot sức khỏe và khuyến khích bạn tham khảo ý kiến bác sĩ để được tư vấn chính xác nhất về vấn đề sức khỏe."
            
            # Gửi metadata
            yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': False, 'rag_enabled': False})}\n\n"
            
            # Stream từng từ
            words = fallback_text.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'word', 'content': word, 'index': i})}\n\n"
                time.sleep(0.08)
            
            yield f"data: {json.dumps({'type': 'end', 'status': 'success'})}\n\n"
            
        except Exception as e:
            print(f"Stream chat error: {e}")
            error_text = f"Xin chào! Cảm ơn bạn đã hỏi về '{query.question}'. Hiện tại tôi đang gặp một chút khó khăn kỹ thuật nhưng vẫn có thể trò chuyện với bạn. Để được tư vấn chính xác về sức khỏe, bạn nên tham khảo ý kiến bác sĩ chuyên khoa nhé!"
            
            yield f"data: {json.dumps({'type': 'metadata', 'ai_powered': False, 'rag_enabled': False})}\n\n"
            
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

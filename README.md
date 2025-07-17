# Health Chatbot với ChromaDB và Gemini AI

Ứng dụng Health Chatbot tối giản sử dụng FastAPI, ChromaDB và Google Gemini AI.

## Tính năng chính

- 🤖 **AI Chat Response**: Trả lời thông minh bằng Google Gemini AI
- 🔍 **Database Health Check**: Kiểm tra kết nối với ChromaDB
- 💬 **Giao diện web**: Frontend đơn giản với Tailwind CSS

## API Endpoints

- `GET /` - Giao diện web chat
- `GET /health` - Kiểm tra kết nối database và AI status  
- `POST /chat` - Chat với AI bot

## Cài đặt

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình API Keys
Chỉnh sửa file `.env`:
```env
GOOGLE_API_KEY=your_google_api_key_here
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
```

**Lấy Google API Key:**
1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Tạo API key mới
3. Sao chép và dán vào file `.env`

## Cách chạy

### 1. Chạy với Docker Compose
```bash
docker-compose up --build
```

### 2. Chạy thủ công
```bash
# 1. Chạy ChromaDB
docker run -p 8001:8000 chromadb/chroma:latest

# 2. Chạy Health Chatbot  
python main.py
```

Truy cập: http://localhost:8000

## Test API

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat với AI
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Làm thế nào để tăng cường miễn dịch?"}'
```

### 3. Chat với vector search
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Làm thế nào để giữ sức khỏe tốt?"}'
```

### 4. Test ChromaDB trực tiếp
```bash
curl http://localhost:8001/api/v1/heartbeat
```

## Endpoints

### Health Chatbot API (Port 8000)
- `GET /` - Trang chủ
- `GET /health` - Health check + ChromaDB status
- `POST /chat` - Chat với vector search
- `POST /add-document` - Thêm document vào ChromaDB
- `GET /api/info` - Thông tin API

### ChromaDB (Port 8001)
- `GET /api/v1/heartbeat` - ChromaDB health check
- `GET /api/v1/collections` - Danh sách collections
- ChromaDB API endpoints khác...

## Swagger UI

- Health Chatbot: http://localhost:8000/docs
- ChromaDB: http://localhost:8001/docs

## Auto Test

Chạy script tự động test tất cả endpoints:
```bash
./test-docker.bat
```

## Cấu trúc file

- `main.py`: FastAPI application với ChromaDB integration
- `Dockerfile`: Docker config cho FastAPI app
- `Dockerfile.chromadb`: Docker config riêng cho ChromaDB (optional)
- `docker-compose.yml`: Multi-service configuration
- `requirements.txt`: Python dependencies
- `test-docker.bat`: Auto test script

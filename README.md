# Health Chatbot: RAG-based Medical QA
This project implements a comprehensive pipeline for building a health-focused retrieval-augmented generation (RAG) chatbot. The system leverages web data crawling, document processing, embedding & vector database construction, advanced information retrieval, and evaluation with real-world health Q&A pairs.

- Detail code:  [Click Here](https://github.com/phuctran2703/Health_Chatbot/blob/main/health-chatbot.ipynb)
- Demo: [Click Here](https://youtu.be/cJYNJ-8c08Y)

## 1. Data Crawling & Extraction
- **Target Domain:** Health articles from VNVC, specifically the main article and its first-level links at: [[vnvc.vn](https://vnvc.vn).](https://vnvc.vn/benh-thuong-gap-o-tre-em-duoi-5-tuoi/.)
- **Main Steps:**
  - Crawl the main article and all its first-level child pages (internal links under the same topic).
  - Use requests and BeautifulSoup to download and parse HTML content.
  - Clean HTML to remove noise (scripts, images, tables, etc.).
  - Extract article text and all sub-sections, creating:
    - A full-document version (for summarization).
    - Detailed "chunks" by section/subsection (for fine-grained retrieval).
  - Metadata is attached to each chunk (URL, section headers, unique doc ID).
- **Example:**
  ```sql
  {'metadata': {'doc_id': 'e0cc7f0cbbfeea7b3776d2bdd2d4329b',
              'section_h1': '30+ bệnh thường gặp ở trẻ em dưới 5 tuổi và cách '
                            'phòng ngừa',
              'section_h2': 'Các bệnh thường gặp ở trẻ em dưới 5 tuổi cha mẹ '
                            'nên để ý',
              'section_h3': '1. Các bệnh trẻ em dưới 5 tuổi thường gặp ở hệ hô '
                            'hấp',
              'section_h4': 'Cảm lạnh',
              'url': 'https://vnvc.vn/benh-thuong-gap-o-tre-em-duoi-5-tuoi/'},
     'text': 'Cảm lạnh: Cảm lạnh là bệnh lý truyền nhiễm do virus tấn công và gây '
             'nhiễm trùng đường hô hấp trên (mũi, họng và xoang). Hiện nay, các '
             'nhà khoa học đã tìm ra hơn 200 loại virus khác nhau có thể gây ra '
             'bệnh cảm lạnh ở trẻ em và người lớn nhưng phổ biến nhất là do '
             'Rhinovirus. Cảm lạnh ở trẻ em thường biểu hiện thông qua các triệu '
             'chứng như nghẹt mũi, chảy nước mũi, ngứa họng, đau họng, hắt hơi.\n'
             'Nhiều trường hợp chủ quan, xem nhẹ sự nguy hiểm của cảm lạnh, trẻ '
             'không được điều trị bệnh kịp thời và đúng cách, nguy cơ tiến triển '
             'nặng, gây viêm tai, viêm xoang, thậm chí viêm tiểu phế quản, viêm '
             'phổi cực kỳ nguy hiểm.\n'...
  }
  ```
 
## 2. Summarization
- **Custom Summarization:** Uses a Google Gemini LLM with a Vietnamese prompt to create high-level, fact-rich summaries for each article.
- **Purpose:** These summaries serve as an entry point for semantic search and improve retrieval efficiency.
- **Storage:** Summaries are stored with metadata in a separate vector database collection.


## 3. Multi-representation Indexing
<img width="1643" height="709" alt="image" src="https://github.com/user-attachments/assets/2f026773-8417-4c65-ad37-2e338c8ee2cb" />

- **Dual-Level Embeddings:** Each document is indexed using two complementary representations:
  - **Summaries**: High-level semantic overviews of documents for fast, coarse-grained retrieval.
  - **Detailed Chunks:** Fine-grained sections of the full content to support accurate answer generation.
- **Embedding Model:** Uses HuggingFace’s multilingual model (intfloat/multilingual-e5-base), optimized with vector normalization to support both Vietnamese and English retrieval tasks.
- **ChromaDB as Vector Store:**
  - Stores summary vectors in chroma_storage/summaries.
  - Stores chunk-level vectors in chroma_storage/details.

## 4. Question Translation (RAG-Fusion)
<img width="1912" height="542" alt="image" src="https://github.com/user-attachments/assets/83f5243a-b5ab-4740-8428-656314b1c0bf" />

- For every user question, the system generates multiple semantically diverse rephrasings using an LLM prompt.
- This helps the retrieval engine match different document phrasings that may not exactly align with the original query.
- In this implementation, 3 rewritten questions are generated in addition to the original.

- Example:
```python
question = "Cách điều trị cảm lạnh"
generate_queries.invoke({"question": question})
```
→ Generated queries:

```python
[
  "Cách điều trị cảm lạnh",
  "Phương pháp chữa trị bệnh cảm thông thường là gì?",
  "Tôi nên làm gì để nhanh khỏi bệnh cảm lạnh?",
  "Các biện pháp khắc phục tại nhà hiệu quả cho cảm lạnh là gì?"
]
```

## 5. Retrieval
**Retrieval is performed in two levels:**

- **Step 1** – Coarse retrieval (Summary level):
  - Retrieves top-N relevant summaries from the vector database.
  - Extracts associated document IDs for the next step.
- **Step 2** – Fine retrieval (Chunk level):
  - From the selected documents, searches for the most relevant detailed chunks.

**Reciprocal Rank Fusion (RRF):**

<img width="183" alt="image" src="https://github.com/user-attachments/assets/58d7b995-e900-4944-87a0-0c50aa6da5ec" />

- Combines results from all rewritten queries using RRF, which assigns higher weight to documents that consistently rank well across different rewrites.
- This fusion method ensures more stable and relevant results by balancing precision and diversity.

## 6. Answer Generation (RAG)

- **Context Assembly:** The most relevant document chunks are provided as context to the LLM.
- **LLM Prompting:** A structured, fact-focused prompt instructs the LLM to answer accurately, clearly, and only with information supported by the retrieved context.
- **Final Output:** The chatbot provides detailed, evidence-based answers, including links to the source material.

- Example:
```python
question = "Cách điều trị cảm lạnh"
final_rag_chain.invoke({"question":question})
```
→ Answer:

```python
Có nhiều cách để điều trị cảm lạnh, bao gồm:
- Nghỉ ngơi: Để cơ thể có thời gian phục hồi.
- Uống nhiều nước: Bổ sung nước lọc, nước ép rau củ quả, nước dừa, mật ong,... để bù nước và các chất dinh dưỡng cần thiết.
- Ăn thức ăn dễ tiêu: Chọn các loại thực phẩm giàu dinh dưỡng, dễ ăn, dễ nuốt và dễ tiêu hóa như cháo, súp, canh hầm.
- Xịt thông mũi: Người lớn có thể dùng thuốc xịt hoặc nhỏ mũi trong tối đa 5 ngày. Trẻ em trên 6 tuổi cần có chỉ định của bác sĩ. Không dùng cho trẻ dưới 6 tuổi.
- Vệ sinh mũi họng: Sử dụng nước muối loãng để vệ sinh họng và mũi giúp giảm viêm nhiễm.
Đối với trẻ sơ sinh và trẻ nhỏ:
- Cho trẻ bú sữa mẹ hoặc sữa công thức (với trẻ dưới 6 tháng).
- Làm sạch chất nhầy trong mũi bằng nước muối sinh lý và dụng cụ hút mũi.
- Thoa vaseline quanh viền lỗ mũi để giảm kích ứng.
- Sử dụng máy tạo độ ẩm trong phòng.
- Mật ong có thể giúp giảm ho cho trẻ trên 12 tháng tuổi (dùng trước khi ngủ).
Kiêng cữ:
- Hạn chế hút thuốc và tránh khói thuốc.
- Không dùng kháng sinh (vì cảm lạnh do virus).
- Không dùng chất kích thích như rượu, bia, caffeine.
- Hạn chế thực phẩm giàu protein, chất béo, đồ chế biến sẵn, đồ ăn nhiều gia vị mặn, nước ngọt có ga.
```

## 7. Chatbot Agent Integration
- **LangGraph REACT Agent:** The notebook includes a modular agent using LangGraph's REACT pattern combined with the above retrieval tool.
- **System Prompt:** Enforces responsible behavior (e.g., do not hallucinate, always cite sources, answer in Vietnamese, and handle social/non-medical queries gracefully).
- **End-to-End Demo:** Handles user chat, performs retrieval, and generates final answers.

## 8. Evaluation Pipeline

- **Health QA Dataset:** A set of health-related question–answer pairs automatically generated by ChatGPT, based on these websites.
- **Automated RAG Evaluation:**
  - For each question, context is retrieved and an answer is generated.
  - The result, including the user question, retrieved context, generated answer, and reference answer, is assembled into an evaluation dataset.
  - Example:
      ```python
      {
        "user_input": "Bệnh nào là bệnh truyền nhiễm thường gặp ở trẻ em dưới 5 tuổi do virus tấn công đường hô hấp trên?",
        "retrieved_contexts": [...],
        "response": "Bệnh cúm là bệnh truyền nhiễm đường hô hấp do virus cúm (Influenza virus) gây ra và rất thường gặp ở trẻ em dưới 5 tuổi...",
        "reference": "Cảm lạnh là bệnh lý truyền nhiễm do virus tấn công và gây nhiễm trùng đường hô hấp trên..."
      }
      ```
- **Metrics:** Uses ragas for automatic evaluation, including:
  - Context Recall – how much relevant information was retrieved
  - Faithfulness – how accurately the answer reflects the context
  - Answer Similarity – how semantically close the generated answer is to the reference

  ```python
  {
    "context_recall": 0.8362,
    "faithfulness": 0.9556,
    "semantic_similarity": 0.9159
  }

  ```

# Application

The basic Health Chatbot application is built using FastAPI, ChromaDB, and Google Gemini AI.

## Interface
<img width="1919" height="902" alt="image" src="https://github.com/user-attachments/assets/ba315d28-a3db-48e6-9d69-c0ba1d1e7077" />


## Main Features

-  **AI Chat Response**: Provides intelligent answers to medical questions by connecting with ChromaDB and Google Gemini AI.

## Installation

### 1. Configure API Keys

**Get Google API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and paste it into the `.env` file

Edit the `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

## How to Run

### 1. Run with Docker Compose
```bash
docker-compose up --build
```

### 2. Run Manually
```bash
pip install -r requirements.txt
python main.py
```

Access the app at: http://localhost:8000

## File Structure

- `main.py`: FastAPI application with ChromaDB integration
- `Dockerfile`: Docker configuration for the FastAPI app
- `docker-compose.yml`: Multi-service configuration
- `requirements.txt`: Python dependencies
- `test-docker.bat`: Automated test script

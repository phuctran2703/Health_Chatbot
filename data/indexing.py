import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load environment variables
dotenv.load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash")

# Load data
with open('full_contents.json', 'r', encoding='utf-8') as f:
    full_contents = json.load(f)

with open('detailed_chunks.json', 'r', encoding='utf-8') as f:
    detailed_chunks = json.load(f)

# Define custom summarization prompt
custom_prompt = PromptTemplate(
    input_variables=["text"],
    template=(
        "Bạn là một trợ lý y tế thông minh, có nhiệm vụ tóm tắt các bài viết về sức khỏe "
        "một cách tổng quan và đầy đủ để phục vụ cho quá trình tìm kiếm trở nên dễ dàng.\n\n"
        "Dưới đây là nội dung bài viết:\n{text}\n\n"
        "Tóm tắt:"
    )
)

# Load summarization chain using the custom prompt
summarizer = load_summarize_chain(llm, chain_type="stuff", prompt=custom_prompt)

# Run summarization
summaries = []
for doc in full_contents:
    if not doc: continue
    doc_obj = Document(page_content=doc["text"])
    summary = summarizer.run([doc_obj])
    summaries.append({
        "metadata": doc["metadata"],
        "summary": summary
    })


# Khởi tạo mô hình embedding
embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    encode_kwargs={"normalize_embeddings": True}
)

# Khởi tạo ChromaDB cho tóm tắt
chroma_summary = Chroma(
    collection_name="summaries",
    embedding_function=embedding_model,
    persist_directory="chroma_storage/summaries"
)
chroma_summary.delete_collection()

# Lưu các summary vào ChromaDB
for item in summaries:
    chroma_summary.add_documents([
        Document(
            page_content=item["summary"],
            metadata=item["metadata"]
        )
    ])

# Khởi tạo ChromaDB cho cách chunks
chroma_detail = Chroma(
    collection_name="detail_chunks",
    embedding_function=embedding_model,
    persist_directory="chroma_storage/details"
)
chroma_detail.delete_collection()

# Lưu các detail vào ChromaDB
for item in detailed_chunks:
    chroma_detail.add_documents([
        Document(
            page_content=item["text"],
            metadata=item["metadata"]
        )
    ])

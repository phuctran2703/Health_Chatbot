import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.load import dumps, loads
from collections import defaultdict
from langchain.tools import StructuredTool
from pydantic import BaseModel
from operator import itemgetter
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Initialize LLM and embedding model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp"
    )
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        encode_kwargs={"normalize_embeddings": True}
    )
else:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# Initialize Chroma collections
chroma_summary = Chroma(
    collection_name="summaries",
    embedding_function=embedding_model,
    persist_directory="data/chroma_storage/summaries"    
)

chroma_detail = Chroma(
    collection_name="detail_chunks",
    embedding_function=embedding_model,
    persist_directory="data/chroma_storage/details"
)

# RAG Fusion template for query expansion
template = """Bạn là một trợ lý ngôn ngữ AI giúp cải thiện kết quả tìm kiếm trong hệ thống truy xuất thông tin dựa trên vector.

Nhiệm vụ của bạn là viết lại câu hỏi gốc của người dùng thành 3 phiên bản khác nhau, có ý nghĩa tương đồng nhưng được diễn đạt theo nhiều cách khác nhau.  
Các câu hỏi viết lại này cần phản ánh sự đa dạng về cách diễn đạt, mức độ chi tiết hoặc các ý định tiềm ẩn khác nhau của người dùng, nhằm tăng khả năng tìm được tài liệu phù hợp khi sử dụng tìm kiếm theo độ tương đồng embedding.

Hãy trả về tổng cộng 4 câu hỏi: câu gốc và 3 câu viết lại, mỗi câu nằm trên một dòng riêng biệt, bắt đầu bằng câu hỏi gốc.

Câu hỏi gốc: {question}"""

prompt_rag_fusion = ChatPromptTemplate.from_template(template)

# Query generation chain
generate_queries = (
    prompt_rag_fusion 
    | llm
    | StrOutputParser()
    | (lambda x: x.split("\n"))
)

def health_retriever(query):
    """Retrieve health information using summary and detail documents"""
    # First, search summaries to get relevant document IDs
    summary_docs = chroma_summary.similarity_search(query, k=3)
    
    # Extract unique document IDs
    doc_ids = list({doc.metadata["doc_id"] for doc in summary_docs})
    
    # Then search details within those documents
    detail_docs = chroma_detail.similarity_search(
        query=query,
        k=10,
        filter={"doc_id": {"$in": doc_ids}}
    )
    return detail_docs

retriever = RunnableLambda(health_retriever)

def reciprocal_rank_fusion(results: list[list], k=60):
    """Reciprocal_rank_fusion that takes multiple lists of ranked documents 
       and an optional parameter k used in the RRF formula"""
    
    # Initialize a dictionary to hold fused scores for each unique document
    fused_scores = defaultdict(float)

    # Iterate through each list of ranked documents
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            # Update the score of the document using the RRF formula: 1 / (rank + k)
            fused_scores[doc_str] += 1 / (rank + k)

    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return reranked_results

# RAG Fusion retrieval chain
retrieval_chain_rag_fusion = generate_queries | retriever.map() | reciprocal_rank_fusion

# Tool definition
class RagInput(BaseModel):
    question: str

def run_retrieval_only(question: str):
    """Run only the retrieval part to get relevant documents"""
    try:
        return retrieval_chain_rag_fusion.invoke({"question": question})
    except Exception as e:
        return f"Lỗi khi truy xuất tài liệu: {str(e)}"

# Create structured tool
retrieval_tool = StructuredTool.from_function(
    name="retrieval_tool", 
    description="Truy vấn thông tin y tế chỉ để lấy tài liệu liên quan",
    func=run_retrieval_only,
    args_schema=RagInput
)

# Test function
# def test_rag(question: str = "Cách điều trị cảm lạnh"):
#     """Test the RAG system with a sample question"""
#     print(f"Testing RAG with question: {question}")
#     print("=" * 80)
    
#     try:
#         # Test retrieval only
#         print("1. Testing retrieval...")
#         docs = run_retrieval_only(question)
#         print(f"Retrieved {len(docs)} documents")
#         for i, (doc, score) in enumerate(docs[:3], 1):
#             print(f"Document #{i} (score: {score:.4f}):")
#             print(f"Content: {doc.page_content[:200]}...")
#             print("-" * 40)
        
#         print("\n2. RAG agent will handle the final answer generation.")
#         print("Use the agent to get complete answers based on retrieved documents.")
        
#     except Exception as e:
#         print(f"Error during testing: {e}")

# if __name__ == "__main__":
#     # Run test
#     test_rag()

import os
import json
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

CHROMA_PATH = "./data/chroma"

def load_laws_from_json():
    """讀取 data/laws.json"""
    if not os.path.exists("./data/laws.json"):
        print("⚠️ 找不到 laws.json，跳過法條匯入。")
        return []
        
    with open("./data/laws.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    docs = []
    for item in data:
        docs.append(Document(
            page_content=item["content"],
            metadata={
                "source": item["source"],
                "article_id": item["article_id"],
                "type": "statute"
            }
        ))
    return docs

def load_cases_from_json():
    """讀取 data/cases.json (新增這個函式)"""
    if not os.path.exists("./data/cases.json"):
        print("⚠️ 找不到 cases.json，跳過判例匯入。")
        return []

    with open("./data/cases.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    docs = []
    for item in data:
        docs.append(Document(
            page_content=item["content"],
            metadata={
                "source": item["case_id"],   # 將案號當作 source
                "court": item["court"],
                "type": "case",             # 標記這是判例
                "cited_articles": item["cited_articles"] # 重要：用來過濾的關鍵
            }
        ))
    return docs

def ingest_data():
    # 1. 清理舊資料庫 (確保資料乾淨)
    if os.path.exists(CHROMA_PATH):
        print("🧹 清除舊資料庫...")
        shutil.rmtree(CHROMA_PATH)

    print("🔄 開始建立向量資料庫...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma(
        collection_name="mole_legal_data",
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    # 2. 匯入法條
    law_docs = load_laws_from_json()
    if law_docs:
        print(f"📚 寫入 {len(law_docs)} 條法規...")
        vectorstore.add_documents(law_docs)

    # 3. 匯入判例 (這裡是新的)
    case_docs = load_cases_from_json()
    if case_docs:
        print(f"⚖️ 寫入 {len(case_docs)} 則判例...")
        vectorstore.add_documents(case_docs)
    
    print("✅ 資料庫重建完成！")

if __name__ == "__main__":
    ingest_data()
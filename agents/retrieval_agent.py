from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from typing import List, Dict

# 初始化資料庫連線
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="mole_legal_data",
    embedding_function=embeddings,
    persist_directory="./data/chroma"
)

def run_case_retrieval(query: str, related_statute_ids: List[str]) -> List[Dict]:
    """
    Step 3: 判例檢索 Agent
    邏輯：
    1. 用使用者的 query 進行向量搜尋，找出最像的 10 個判例 (Recall)。
    2. 過濾 (Filter)：只保留那些「引用了」前面找到的法條的判例。
    3. 如果過濾後沒剩半個，為了避免開天窗，會保留分數最高的 1 個。
    """
    
    print(f"   -> [Retrieval Agent] 收到關鍵法條 ID: {related_statute_ids}")
    
    # 1. 寬鬆檢索：先撈 10 筆 (包含 metadata 裡的 type='case')
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 10,
            "filter": {"type": "case"} # 只撈判例
        }
    )
    docs = retriever.invoke(query)
    
    # 2. 精確過濾 (Metadata Filtering)
    # 我們在 ingest.py 裡存的格式是 "民法_184,民法_195" 字串
    filtered_cases = []
    
    for doc in docs:
        cited_str = doc.metadata.get("cited_articles", "")
        # 檢查：該判例引用的法條中，是否有任何一條出現在我們找到的 related_statute_ids 裡？
        # 例如：related_statute_ids=['民法_184'], cited_str="民法_184,民法_195" -> 中！
        is_relevant = False
        for stat_id in related_statute_ids:
            if stat_id in cited_str:
                is_relevant = True
                break
        
        if is_relevant:
            filtered_cases.append(doc)
            
    # 3. 如果過濾太嚴格導致沒結果，就 fallback (至少回傳最相關的那一篇)，避免 user 看到空空的
    if not filtered_cases and docs:
        print("   -> (警告) 找不到完全符合引用法條的判例，將回傳最相似的案例。")
        filtered_cases = [docs[0]]
        
    # 取前 3 名
    return filtered_cases[:3]
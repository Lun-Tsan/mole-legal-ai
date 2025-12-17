import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from api.schemas import ConsultResponse, Statute, Case

# 引入 Agent 模組
from agents.classifier import run_classifier
from agents.retrieval_agent import run_case_retrieval # <--- 新增這個

load_dotenv()

# 初始化資源
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="mole_legal_data",
    embedding_function=embeddings,
    persist_directory="./data/chroma"
)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def retrieve_statutes(query: str, domain: str):
    """Step 2: Expert Agent (只撈法條)"""
    
    # 修改點：ChromaDB 如果有多個條件，必須用 $and 包起來
    if domain in ["民法", "刑法"]:
        filter_dict = {
            "$and": [
                {"type": "statute"},
                {"source": domain}
            ]
        }
    else:
        # 如果沒有指定領域，就只過濾 type
        filter_dict = {"type": "statute"}
        
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 2, 
            "filter": filter_dict
        }
    )
    return retriever.invoke(query)

def run_mole_pipeline(query: str) -> ConsultResponse:
    # --- Step 1: Classifier Agent (分類) ---
    print(f"1. [Classifier] 分析案件領域...")
    target_domains = run_classifier(query)
    print(f"   -> 領域: {target_domains}")

    # --- Step 2: Expert Agents (法條檢索) ---
    found_statute_docs = []
    found_statute_ids = [] # 用來存 "民法_184" 這種 ID 給下一步用
    
    for domain in target_domains:
        print(f"2. [Expert] 檢索 '{domain}' 法條...")
        docs = retrieve_statutes(query, domain)
        found_statute_docs.extend(docs)
        
        # 收集條號 ID (從 metadata 提取)
        for d in docs:
            sid = d.metadata.get("article_id")
            if sid:
                found_statute_ids.append(sid)

    # 去重
    unique_statutes = {d.page_content: d for d in found_statute_docs}.values()

    # --- Step 3: Retrieval Agent (判例檢索 - 依賴上一步的法條 ID) ---
    print(f"3. [Retrieval] 根據法條與案情檢索判例...")
    found_case_docs = run_case_retrieval(query, found_statute_ids)

    # --- 資料整理 (封裝成 API 格式) ---
    api_statutes = []
    api_cases = []
    context_text = ""
    
    # 整理法條
    context_text += "【相關法律條文】\n"
    for doc in unique_statutes:
        m = doc.metadata
        content = doc.page_content
        api_statutes.append(Statute(
            law_name=m.get("source", "未知"),
            article_id=m.get("article_id", ""),
            content=content
        ))
        context_text += f"- {m.get('article_id')}: {content}\n"

    # 整理判例
    context_text += "\n【相關實務判例】\n"
    for doc in found_case_docs:
        m = doc.metadata
        content = doc.page_content
        api_cases.append(Case(
            case_id=m.get("source", "未知"),
            court=m.get("court", "法院"),
            summary=content
        ))
        context_text += f"- {m.get('court')} {m.get('source')}: {content}\n"

    # --- Step 4: Synthesizer Agent (總結報告) ---
    print(f"4. [Synthesizer] 撰寫最終報告...")
    
    synthesizer_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一個專業且溫暖的法律顧問 AI。請根據提供的法條與判例資料，為使用者撰寫分析報告。
        
        回答結構要求：
        1. 【法律分析】：引用剛才找到的法條，解釋為何適用於此案。
        2. 【實務見解】：參考找到的判例，說明法院通常如何判決（例如賠償金額考量、判刑輕重）。
        3. 【白話建議】：用最通俗的話告訴使用者現在該做什麼（例如蒐證、和解或提告）。
        
        請注意：
        - 必須「有所本」，嚴格基於提供的資料回答。
        - 語氣保持客觀但有同理心。
        """),
        ("user", "使用者案件：{query}\n\n參考資料庫：\n{context}")
    ])
    
    chain = synthesizer_prompt | llm
    ai_response = chain.invoke({"query": query, "context": context_text})
    
    return ConsultResponse(
        domains=target_domains,
        statutes=api_statutes,
        cases=api_cases,
        summary=ai_response.content
    )
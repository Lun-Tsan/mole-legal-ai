import os
from dotenv import load_dotenv  # <--- 新增這一行
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

# 1. 載入環境變數 (務必放在 ChatOpenAI 初始化之前！)
load_dotenv()  # <--- 這一行非常重要

# 檢查一下是否有讀到 Key，如果沒有就直接拋出更清楚的錯誤
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ 錯誤：找不到 OPENAI_API_KEY！請確認專案根目錄下有 .env 檔案，且內容包含 OPENAI_API_KEY=sk-...")

# 2. 定義分類輸出的結構
class DomainClassification(BaseModel):
    domains: List[str] = Field(
        description="涉及的法律領域列表，例如 ['民法', '刑法']。若不確定則回傳所有領域。"
    )

# 3. 初始化 LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 4. 設定分類專用的 Prompt
classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一個資深的法律案件分案人員。
    請分析使用者的案件描述，判斷其涉及哪些法律領域（目前僅支援：'民法'、'刑法'）。
    
    規則：
    - 涉及金錢糾紛、損害賠償、合約問題通常為「民法」。
    - 涉及犯罪、坐牢、罰金、故意傷害通常為「刑法」。
    - 若兩者皆有（如車禍撞傷人），請同時回傳。
    """),
    ("user", "{query}")
])

# 5. 建立分類鏈 (Chain)
classifier_chain = classifier_prompt | llm.with_structured_output(DomainClassification)

def run_classifier(query: str) -> List[str]:
    """執行分類，回傳領域列表"""
    try:
        result = classifier_chain.invoke({"query": query})
        if not result or not result.domains:
            return ["民法", "刑法"] # 預設值
        return result.domains
    except Exception as e:
        print(f"⚠️ 分類 Agent 發生錯誤: {e}，將使用預設全領域檢索。")
        return ["民法", "刑法"]
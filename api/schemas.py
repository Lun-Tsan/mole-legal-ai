from pydantic import BaseModel
from typing import List, Optional

# 定義輸入格式：使用者只傳送案件摘要
class ConsultRequest(BaseModel):
    query: str

# 定義輸出格式：法條
class Statute(BaseModel):
    law_name: str       # 例如：民法
    article_id: str     # 例如：民法_184
    content: str        # 條文內容

# 定義輸出格式：判例
class Case(BaseModel):
    case_id: str
    court: str          # 例如：最高法院
    summary: str        # 判例重點摘要

# 定義輸出格式：完整回應
class ConsultResponse(BaseModel):
    domains: List[str]      # 涉及領域 (如 ["民法", "刑法"])
    statutes: List[Statute] # 相關法條列表
    cases: List[Case]       # 相關判例列表
    summary: str            # 白話文總結
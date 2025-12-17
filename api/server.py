from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import ConsultRequest, ConsultResponse
from pipeline.workflow import run_mole_pipeline
from fastapi.responses import RedirectResponse
# --- 新增引入 db ---
from api.db import init_db, save_record, get_all_records, delete_record
# 初始化資料庫 (確保檔案存在)
init_db()

app = FastAPI(title="MoLE 法律諮詢系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/web", StaticFiles(directory="static", html=True), name="static")

@app.post("/api/consult", response_model=ConsultResponse)
async def consult(request: ConsultRequest):
    print(f"收到查詢：{request.query}")
    
    # 執行 AI 分析
    result = run_mole_pipeline(request.query)
    
    # --- 自動存檔 ---
    # 將 Pydantic 物件轉為 dict 存入資料庫
    save_record(request.query, result.dict())
    
    return result

@app.get("/")
async def root():
    # 當使用者進入首頁時，自動將他轉到網頁介面
    return RedirectResponse(url="/web/index.html")

# --- 新增：取得歷史紀錄 API ---
@app.get("/api/history")
async def get_history():
    return get_all_records()

# --- 新增：刪除紀錄 API ---
@app.delete("/api/history/{record_id}")
async def delete_history_item(record_id: int):
    delete_record(record_id)
    return {"status": "success", "message": f"Record {record_id} deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
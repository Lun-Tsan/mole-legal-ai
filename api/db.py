import sqlite3
import json
from datetime import datetime

DB_NAME = "mole_history.db"

def init_db():
    """初始化資料庫：如果沒有資料表就建立"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 建立一個 history 表格
    # id: 序號
    # query: 使用者問題
    # result_json: 完整的後端回應 (存成 JSON 字串，方便直接還原)
    # created_at: 時間
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_record(query: str, result_data: dict):
    """儲存一筆諮詢紀錄"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 將字典轉成 JSON 字串儲存
    json_str = json.dumps(result_data, ensure_ascii=False)
    
    cursor.execute(
        "INSERT INTO history (query, result_json) VALUES (?, ?)",
        (query, json_str)
    )
    conn.commit()
    conn.close()

def get_all_records():
    """取得所有紀錄 (最新的在上面)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # 讓我們可以用欄位名稱取值
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, query, result_json, created_at FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "query": row["query"],
            "result": json.loads(row["result_json"]), # 轉回字典
            "created_at": row["created_at"]
        })
    
    conn.close()
    return results

def delete_record(record_id: int):
    """刪除指定的歷史紀錄"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
import os
import re
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# --- 1. 資料庫配置 ---

# 判斷環境變數，自動選擇 SQLite (本地) 或 PostgreSQL (Render/Zeabur)
# Render/Zeabur 通常提供 DATABASE_URL，若是 postgres:// 開頭需修正為 postgresql:// 以符合 SQLAlchemy 新版規範
database_url = os.getenv("DATABASE_URL", "sqlite:///./local_messages.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    database_url, 
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. 資料庫模型 ---

class MessageModel(Base):
    __tablename__ = "messages"

    # 使用自動遞增的主鍵，但在顯示時我們會透過計算轉換成 #001~#100
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 建立資料表
Base.metadata.create_all(bind=engine)

# --- 3. FastAPI 設定 ---

app = FastAPI()

# 設定 CORS，允許前端網頁跨域存取 (開發時方便，生產環境可限制來源)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 模型 (用於驗證請求資料)
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    display_id: str
    content: str
    created_at: datetime

# Dependency: 取得資料庫 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. API 路由 ---

@app.get("/messages", response_model=list[MessageResponse])
def get_messages(db: Session = Depends(get_db)):
    # 取得所有留言，按時間排序
    messages = db.query(MessageModel).order_by(MessageModel.created_at.asc()).all()
    
    results = []
    for msg in messages:
        # 計算顯示用的序號 #001 ~ #100
        # 邏輯：((資料庫ID - 1) % 100) + 1，這樣ID 101 會變回 #001，達成循環效果
        seq_num = (msg.id - 1) % 100 + 1
        formatted_id = f"#{seq_num:03d}"
        
        results.append({
            "display_id": formatted_id,
            "content": msg.content,
            "created_at": msg.created_at
        })
    return results

@app.post("/messages")
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    # 1. 檢查目前筆數
    count = db.query(MessageModel).count()
    
    # 2. 如果達到或超過 100 筆，刪除最舊的一筆
    if count >= 100:
        oldest_msg = db.query(MessageModel).order_by(MessageModel.created_at.asc()).first()
        if oldest_msg:
            db.delete(oldest_msg)
            db.commit()
    
    # 3. 新增留言
    new_msg = MessageModel(content=message.content)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    return {"status": "success", "id": new_msg.id}

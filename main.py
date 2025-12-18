from fastapi import FastAPI

# 1. 建立 FastAPI 實例
app = FastAPI()

# 2. 使用 app.get 而不是直接用 get
@app.get("/")
def read_root():
    return {"status": "success", "message": "Hello Render! My FastAPI app is live."}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "description": "This is a test endpoint"}

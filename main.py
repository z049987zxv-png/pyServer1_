from fastapi import FastAPI

app = FastAPI()

@get("/")
def read_root():
    return {"status": "success", "message": "Hello Render! My FastAPI app is live."}

@get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "description": "This is a test endpoint"}

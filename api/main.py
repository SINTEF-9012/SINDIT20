from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root() -> dict:
    return {"message": "Hello World!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, query: str = None) -> dict:
    return {"item_id": item_id, "query": query}


@app.get("/users/")
async def read_users() -> dict:
    return {
        "users": [
            {"user": "Rick", "username": "rick"},
            {"user": "Morty", "username": "morty"},
        ]
    }

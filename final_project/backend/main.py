import uvicorn
from fastapi import (
    FastAPI,
)
import os
import sys

sys.path.append("api")

from api.hello import hello

app = FastAPI()

app.include_router(
    hello,
    prefix="/v1/hello",
    tags=["hello"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

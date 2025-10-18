import uvicorn
from fastapi import (
    FastAPI,
)
import os
import sys

sys.path.append("api")

from api.hello import hello
from api.digital_twin import digital_twin

app = FastAPI()

app.include_router(
    hello,
    prefix="/v1/hello",
    tags=["hello"],
)

app.include_router(
    digital_twin,
    prefix="/v1/digital_twin",
    tags=["digital_twin"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

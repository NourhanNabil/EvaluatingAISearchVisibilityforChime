from fastapi import FastAPI
import uvicorn

from Controllers import HealthController, RagController
from Config.Service import Service

app = FastAPI()

app.include_router(HealthController.health_router)
app.include_router(RagController.rag_router)

if __name__ == "__main__":
    uvicorn.run(app, host=Service.HOST, port=Service.PORT)

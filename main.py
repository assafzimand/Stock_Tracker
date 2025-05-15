from fastapi import FastAPI
from app.api import router
from app.data.scheduler import start_scheduler, stop_scheduler
import uvicorn
import webbrowser
import threading

app = FastAPI()
app.include_router(router.router)

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

if __name__ == "__main__":
    def open_browser():
        webbrowser.open("http://127.0.0.1:8000/docs")

    threading.Timer(1.5, open_browser).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI
import gradio as gr
from admin import get_admin_interface
from digital_twin import get_interface
from dotenv import load_dotenv
import os

load_dotenv(override=True)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

app = FastAPI()

admin_ui = get_admin_interface()
public_ui = get_interface()

app = gr.mount_gradio_app(app, admin_ui, path="/admin", auth=[("admin", ADMIN_PASSWORD)])

app = gr.mount_gradio_app(app, public_ui, path="")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=7860)

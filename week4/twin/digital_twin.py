from agents import Agent, Runner, trace
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import gradio as gr
from mcp_servers import memory_graph_server, memory_rag_server
from questions import record_question_with_no_answer
from contacts import record_new_person_to_get_in_touch
from push import push_notify_to_twin
import asyncio
from context import instructions, name
from styling import custom_css, EXAMPLE_QUESTIONS
from gradio.themes.utils import fonts

load_dotenv(override=True)
MODEL = "gpt-4.1"
tools = [record_new_person_to_get_in_touch, record_question_with_no_answer, push_notify_to_twin]


async def stream_response(messages, mcps):
    agent = Agent(
        "Digital Twin", instructions=instructions, model=MODEL, tools=tools, mcp_servers=mcps
    )
    result = Runner.run_streamed(agent, messages)
    reply = ""
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            reply += event.data.delta
            reply = reply.replace(" — ", " -- ").replace("—", " -- ")
            yield reply


async def chat(message, history):
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages += [{"role": "user", "content": message}]
    with trace("Digital Twin"):
        async with memory_rag_server() as rag_server:
            async with memory_graph_server() as graph_server:
                mcps = [rag_server, graph_server]
                async for chunk in stream_response(messages, mcps):
                    yield chunk


def get_interface():
    theme = gr.themes.Default(
        primary_hue="sky", neutral_hue="slate", font=[fonts.GoogleFont("Poppins"), "sans-serif"]
    )
    with gr.Blocks(
        css=custom_css,
        title=f"{name} | Digital Twin",
        theme=theme,
    ) as interface:
        with gr.Row(elem_classes="header-container"):
            gr.HTML(f"""
                <div class="main-title">{name}'s&nbsp;Digital&nbsp;Twin</div>
                <div class="subtitle">Ask me anything about my professional background, skills, and experience.</div>
            """)
        with gr.Row(elem_classes="examples-container"):
            gr.HTML('<div class="examples-title">💡 Try asking:</div>')
            with gr.Row():
                example_buttons = [
                    gr.Button(q, elem_classes="example-btn", size="sm") for q in EXAMPLE_QUESTIONS
                ]
        chatbot_interface = gr.ChatInterface(
            fn=chat,
            type="messages",
            title="",
            chatbot=gr.Chatbot(
                height=500,
                placeholder=f"👋 Hi! I'm {name}'s digital twin. Ask away…",
                type="messages",
                label=name,
                avatar_images=(None, "me.png"),
            ),
            textbox=gr.Textbox(
                placeholder="Ask me about my background, skills, projects, or experience…",
                container=False,
                scale=7,
            ),
        )
        for btn in example_buttons:
            btn.click(lambda q: q, inputs=[btn], outputs=[chatbot_interface.textbox])
        gr.HTML(f"<div class='footer'>{name}'s Digital Twin</div>")

    return interface


async def main():
    interface = get_interface()
    interface.launch(inbrowser=True)


if __name__ == "__main__":
    asyncio.run(main())

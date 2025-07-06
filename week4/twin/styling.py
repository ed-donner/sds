# palette.py  (optional helper file)

PRIMARY_COLOR_LIGHT = "#0ea5e9"  # sky‑500
PRIMARY_COLOR_DARK = "#38bdf8"  # sky‑400  (for emphasis on dark bg)
ACCENT_COLOR = "#f472b6"  # pink‑400
BG_LIGHT = "#ffffff"
BG_LIGHT_SECONDARY = "#f8fafc"  # slate‑50
BG_DARK = "#0f172a"  # slate‑900
BG_DARK_SECONDARY = "#1e293b"  # slate‑800
TEXT_LIGHT = "#0f172a"  # almost‑black
TEXT_DARK = "#e2e8f0"  # slate‑200
BORDER_LIGHT = "#e2e8f0"  # slate‑200
BORDER_DARK = "#334155"  # slate‑600


EXAMPLE_QUESTIONS = [
    "What are your top accomplishments?",
    "Tell me about your most exciting project",
    "How do I get in touch with you?",
    "Do you like cheese?",
]

custom_css = r"""


/*  ------------------------  THEME TOKENS  ------------------------  */
:root {
    --font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                   Roboto, 'Helvetica Neue', sans-serif;

    --primary-500:  #0ea5e9;   /* sky‑500 */
    --primary-600:  #0284c7;   /* sky‑600 (hover) */
    --accent-400:   #f472b6;   /* pink‑400 */
    --bg-main:      #ffffff;
    --bg-alt:       #f8fafc;
    --text-main:    #0f172a;
    --text-sub:     #475569;   /* slate‑600 */
    --border:       #e2e8f0;
}

.dark {
    --primary-500:  #38bdf8;   /* brighter sky on dark */
    --primary-600:  #0ea5e9;
    --bg-main:      #0f172a;
    --bg-alt:       #1e293b;
    --text-main:    #e2e8f0;
    --text-sub:     #94a3b8;
    --border:       #334155;
}

/*  ------------------------  RESET / GLOBAL  ------------------------  */
html, body, .gradio-container {
    font-family: var(--font-family);
    background: var(--bg-alt);
    color: var(--text-main);
}

/* Make the app a pleasant centred card on large screens */
.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding: 1rem;
}

/*  ------------------------  HEADER  ------------------------  */
.header-container {
    text-align: center;
    padding: 2.5rem 1rem 2rem;
    background: var(--bg-main);
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 8px 16px rgba(0,0,0,.05);
    border: 1px solid var(--border);
    transition: background .3s ease, border-color .3s ease;
}

.main-title {
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--primary-500);
    margin-bottom: .5rem;
}

.subtitle {
    font-size: 1.125rem;
    color: var(--text-sub);
}

/*  ------------------------  EXAMPLE BUTTONS  ------------------------  */
.examples-container {
    background: var(--bg-main);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 8px rgba(0,0,0,.03);
    border: 1px solid var(--border);
}

.examples-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: .75rem;
}

.example-btn {
    background: var(--bg-alt) !important;
    color: var(--primary-500) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9999px !important;
    padding: .45rem 1rem !important;
    margin: .25rem !important;
    font-size: .92rem !important;
    transition: all .2s ease;
}
.example-btn:hover {
    background: var(--primary-500) !important;
    color: #ffffff !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,.10);
}

/*  ------------------------  CHAT STYLING  ------------------------  */
[data-testid="chatbot"]{
    background: var(--bg-main) !important;
    border-radius: 16px !important;
    border: 1px solid var(--border) !important;
}

/* user bubble */
[data-testid="chatbot"] .message-wrap.user {
    background: var(--primary-500) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}
/* bot bubble */
[data-testid="chatbot"] .message-wrap.bot {
    background: var(--bg-alt) !important;
    color: var(--text-main) !important;
    border-left: 4px solid var(--primary-500) !important;
    border-radius: 10px !important;
}

/*  ------------------------  FOOTER  ------------------------  */
.footer {
    text-align: center;
    padding: 1rem .5rem;
    color: var(--text-sub);
    font-size: .85rem;
}
footer {display:none !important}
"""

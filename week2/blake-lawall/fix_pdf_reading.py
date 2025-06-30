# Copy this code to replace cells 14 and 15 in your notebook

# Read in both PDFs with proper variable names

# Read in the LinkedIn PDF
reader = PdfReader("blake/linkedin.pdf")
linkedin_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin_text += text

# Read in the AI resume PDF
reader = PdfReader("blake/Blake_Lawall-AI-20241024.pdf")
ai_resume_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        ai_resume_text += text

# Read in the summary text file
with open("blake/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

name = "Blake Lawall"

# Updated system prompt to use both PDFs
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background, LinkedIn profile, and AI resume which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin_text}\n\n## AI Resume:\n{ai_resume_text}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}." 
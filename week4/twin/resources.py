from pypdf import PdfReader
import json

reader = PdfReader("./me/linkedin.pdf")

linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

with open("./me/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

with open("./me/style.txt", "r", encoding="utf-8") as f:
    style = f.read()

with open("./me/facts.json", "r", encoding="utf-8") as f:
    facts = json.load(f)

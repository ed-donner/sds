import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(override=True)
os.chdir(Path(__file__).parent)

MODEL = "gpt-4.1-nano"
KNOWLEDGE_BASE_PATH = "knowledge-base"
SUMMARY_FOLDER = "knowledge-base/summary"
BATCH_SIZE = 10

SYSTEM_PROMPT = """
You are an expert at analyzing and summarizing documents. 
You will receive a batch of markdown documents. 

Please provide:
1. Brief bullet points of key points (3-5 bullets)
2. A 1-2 paragraph summary of what these documents are saying

Your summary should support holistic understanding for a RAG system.
"""


def get_next_summary_filename():
    """Find the next available summary_N.md filename."""
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    counter = 1
    while True:
        filename = os.path.join(SUMMARY_FOLDER, f"summary_{counter}.md")
        if not os.path.exists(filename):
            return filename
        counter += 1


def read_markdown_files(folder_path):
    """Read all markdown files from a folder."""
    md_files = glob.glob(os.path.join(folder_path, "**/*.md"), recursive=True)
    documents = []
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    'path': file_path,
                    'content': content
                })
        except Exception as e:
            print(f"  ⚠️  Could not read {file_path}: {e}")
    
    return documents


def create_batches(documents, batch_size=BATCH_SIZE):
    """Split documents into batches."""
    batches = []
    for i in range(0, len(documents), batch_size):
        batches.append(documents[i:i + batch_size])
    return batches


def summarize_batch(llm, batch):
    """Generate a summary for a batch of documents."""
    combined_content = "\n\n---\n\n".join([doc['content'] for doc in batch])
    
    messages = [
        ("system", SYSTEM_PROMPT),
        ("user", f"Please summarize the following documents:\n\n{combined_content}")
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        return response.content
    except Exception as e:
        print(f"  ❌ Error generating summary: {e}")
        return None


def process_knowledge_base(max_api_calls=None):
    """Process all subfolders in knowledge-base and create summaries."""
    llm = ChatOpenAI(temperature=0, model_name=MODEL)
    
    # Get all subfolders
    folders = glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*"))
    folders = [f for f in folders if os.path.isdir(f) and not f.endswith("summary")]
    
    if not folders:
        print("No folders found in knowledge-base")
        return
    
    summaries = []
    api_calls_made = 0
    
    for folder in folders:
        folder_name = os.path.basename(folder)
        print(f"\n📁 Processing folder: {folder_name}")
        
        # Read all markdown files
        documents = read_markdown_files(folder)
        
        if not documents:
            print(f"  ⚠️  No markdown files found in {folder_name}")
            continue
        
        print(f"  Found {len(documents)} documents")
        
        # Create batches
        batches = create_batches(documents)
        print(f"  Processing {len(batches)} batch(es)")
        
        # Process each batch
        for batch_idx, batch in enumerate(batches, 1):
            if max_api_calls and api_calls_made >= max_api_calls:
                print(f"\n⚠️  Reached maximum API calls limit ({max_api_calls})")
                break
            
            # Determine heading
            if len(batches) == 1:
                heading = f"## {folder_name.title()} Documents - Overview"
            else:
                heading = f"## {folder_name.title()} Documents - Batch {batch_idx}"
            
            print(f"  Processing batch {batch_idx}/{len(batches)} ({len(batch)} documents)...")
            
            # Generate summary
            summary = summarize_batch(llm, batch)
            api_calls_made += 1
            
            if summary:
                summaries.append(f"{heading}\n\n{summary}")
                print(f"  ✓ Batch {batch_idx} summarized")
            else:
                print(f"  ✗ Batch {batch_idx} failed, skipping")
        
        if max_api_calls and api_calls_made >= max_api_calls:
            break
    
    # Write all summaries to file
    if summaries:
        output_file = get_next_summary_filename()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(summaries))
        
        print(f"\n✅ Summary complete! Written to: {output_file}")
        print(f"📊 Total API calls made: {api_calls_made}")
        print(f"📝 Total batches summarized: {len(summaries)}")
    else:
        print("\n⚠️  No summaries generated")


if __name__ == "__main__":
    import sys
    
    # Check for max API calls argument
    max_calls = None
    if len(sys.argv) > 1:
        try:
            max_calls = int(sys.argv[1])
            print(f"🔒 Limiting to {max_calls} API call(s)")
        except ValueError:
            print("Usage: python summarize.py [max_api_calls]")
            sys.exit(1)
    
    process_knowledge_base(max_api_calls=max_calls)


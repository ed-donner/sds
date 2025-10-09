# Summarization Script Specifications

## Overview

Create a Python script (`summarize.py`) that processes documents from the knowledge-base directory, generates AI summaries in batches, and saves them to a summary folder.

## Requirements

### 1. Directory Structure

- **Input**: `knowledge-base/*` (all subfolders)
- **Output**: `knowledge-base/summary/` (create if doesn't exist)
- **Exclude**: The summary folder itself from processing

### 2. Document Processing Logic

- Iterate through each subfolder in `knowledge-base/` (e.g., company, contracts, employees, products)
- For each subfolder:
  - Collect all `.md` files
  - Process documents in batches of 10
  - If folder has 15 documents: process first 10, then remaining 5
  - If folder has 23 documents: process first 10, then next 10, then remaining 3

### 3. AI Summarization

- **Model**: `gpt-4.1-nano`
- **Input to AI**: Combine up to 10 documents as context
- **Output from AI**:
  - Brief bullet points or overview of key points
  - 1-2 paragraph summary of what the documents are saying
  - Purpose: Support holistic RAG queries

### 4. Output Format

- **Single file**: All summaries go into ONE markdown file
- **Structure within file**:

  ```
  ## [Heading for batch 1]
  [Summary content]

  ## [Heading for batch 2]
  [Summary content]
  ```

- Each heading should clearly identify what's being summarized (e.g., folder name + batch number if multiple batches)

### 5. File Naming Convention

- Start with `summary_1.md`
- If `summary_1.md` exists, use `summary_2.md`
- If `summary_2.md` exists, use `summary_3.md`
- Continue incrementing until finding an unused filename

### 6. Technical Details

- Use similar structure to `ingest.py` (same working directory setup, dotenv loading)
- Use `glob` for file discovery
- Should handle UTF-8 encoding for reading markdown files
- Script should be runnable via `python summarize.py`

### 7. Error Handling

- Handle missing folders gracefully
- Handle files that can't be read (encoding issues)
- Print progress indicators (which folder/batch is being processed)

### 8. Dependencies

- Should reuse existing patterns from `ingest.py`
- Will need OpenAI API (or similar) for gpt-4.1-nano
- Should load environment variables from `.env` file

### 9. Success Criteria

- Script processes all subfolders in knowledge-base (except summary)
- Creates one summary file with all batch summaries
- Each summary includes heading + key points + 1-2 paragraph overview
- File naming handles conflicts automatically
- Console output shows completion status

## Example Output Structure

```markdown
## Company Documents - Overview

**Key Points:**

- Point 1
- Point 2
- Point 3

The company documents describe...
[1-2 paragraphs of summary]

## Contracts Documents - Batch 1

**Key Points:**

- Point 1
- Point 2

The first 10 contract documents cover...
[1-2 paragraphs of summary]

## Contracts Documents - Batch 2

...
```

# Simple OpenAI RAG Example

## Setup

1. Create a virtual environment:
   `python3 -m venv ragenv`
2. Activate it:
   `source ragenv/bin/activate`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Add your OpenAI key to `.env`:
   `OPENAI_API_KEY=your_key_here`

## Run

Use the project virtualenv so the installed dependencies are available:

`./ragenv/bin/python rag.py --query "What is TowerZ?"`

By default, the script reads `data/document.txt` and retrieves the three most similar chunks.

Optional arguments:
- `--document` to point at a different source file
- `--top-k` to control how many chunks are returned
- `--model` to choose the OpenAI model for the final answer
- `--show-context` to print the retrieved chunks before the answer

## API

Start the FastAPI server from the project root:

```bash
./ragenv/bin/uvicorn api:app --reload
```

Ask the document a question in another terminal:

```bash
curl "http://127.0.0.1:8000/query?query=What%20is%20TowerZ%3F"
```

`GET /query` accepts a required `query` parameter and optional `top_k` parameter
(from 1 to 10). It returns the answer and the chunks supplied to OpenAI as context.

The **docs** is available at: `http://127.0.0.1:8000/docs`

## How it works

1. The script embeds your document and stores the chunks in FAISS.
2. It retrieves the most relevant chunks for your question.
3. It sends those retrieved chunks as `Context:` inside the OpenAI prompt.
4. The model answers using that context instead of the raw document alone.

## Structure

Everything is in `rag.py`, in the same order the RAG pipeline runs:

1. `load_document_chunks` reads and splits the document.
2. `build_vector_store` embeds chunks and creates the FAISS index.
3. `retrieve_chunks` runs similarity search for the question.
4. `build_prompt` puts only those retrieved chunks into the LLM context.
5. `answer_question` calls OpenAI and returns the answer.

This keeps the example easy to read while each step is still a small testable function.

## Test

Run the unit test from the project root after installing dependencies:

```bash
source ragenv/bin/activate
python -m unittest
```

If you prefer not to activate the virtualenv, run the same test directly with the project interpreter:

```bash
./ragenv/bin/python -m unittest
```

# Learning Document: LLM-Powered Teaching Assistant

This document has three parts: **Project Description**, **Theory** (topics and subtopics used in development), and **Code Explanation** (file-by-file and block-by-block).

---

# Part 1: Project Description

## 1.1 What the Project Does

The **Teaching Assistant** is an LLM-powered web application that turns a PDF document into a structured learning experience. A user uploads a PDF, and the app:

1. **Splits the document into topics** — An LLM analyzes the full text and returns logical sections (topics) with titles and the exact text for each.
2. **Teaches each topic** — For any topic, the user can request a clear, didactic explanation generated from that topic’s content only.
3. **Quiz after each topic** — The app generates 3–5 quiz questions (and answers) from the topic; the user types answers and can check them.
4. **Chat with the teacher** — The user can ask questions or clear doubts in a chat; the “teacher” (LLM) answers based only on the current topic’s document content, with multi-turn conversation.

## 1.2 High-Level Architecture

- **Frontend / orchestration**: Streamlit (single Python app).
- **Document handling**: PyMuPDF (`fitz`) to load PDFs and extract text.
- **Intelligence**: A single LLM (OpenAI or Anthropic, chosen via config) used for:
  - Splitting the document into topics (chunker).
  - Explaining a topic (teacher).
  - Generating quiz Q&A (teacher).
  - Answering follow-up questions in chat (teacher).
- **Configuration**: Environment variables (`.env`) for provider and API keys.

## 1.3 User Flow

1. User opens the app and uploads a PDF.
2. App loads the PDF text and calls the LLM to get a list of topics (outline).
3. User sees the outline in the sidebar and selects a topic.
4. Main area shows: topic title → “Explain this topic” → optional Quiz → “Ask the teacher” chat.
5. User can move between topics with Previous/Next or sidebar; each topic has its own teaching, quiz, and chat history.
6. “Start over” clears the document and state so a new PDF can be uploaded.

## 1.4 Project Layout

| File / folder      | Purpose |
|--------------------|--------|
| `app.py`           | Streamlit UI: upload, outline, topic view, teaching, quiz, chat, navigation. |
| `doc_loader.py`     | PDF loading and text extraction (PyMuPDF). |
| `chunker.py`        | LLM-based splitting of document text into topics. |
| `teacher.py`        | LLM calls: teach topic, generate Q&A, answer user questions (chat). |
| `llm_config.py`    | Reads env; returns the correct LangChain chat model (OpenAI or Anthropic). |
| `requirements.txt` | Python dependencies. |
| `.env.example`     | Example env vars (provider, API keys). |
| `README.md`        | Setup and run instructions. |
| `docs/LEARNING.md`  | This learning document. |

---

# Part 2: Theory Document

This section covers the main topics and subtopics used while developing the project.

---

## 2.1 Streamlit

### 2.1.1 What Streamlit Is

Streamlit is a Python library for building data and ML apps as web UIs. You write Python scripts; Streamlit turns them into a reactive app with widgets (buttons, inputs, file uploaders, etc.) and re-runs the script when the user interacts.

### 2.1.2 Key Concepts

- **Script re-execution**: Each interaction (click, input, upload) triggers a full re-run of the script from top to bottom.
- **Widgets**: `st.button`, `st.file_uploader`, `st.text_input`, `st.chat_input`, `st.chat_message`, `st.markdown`, `st.spinner`, etc.
- **Session state**: `st.session_state` is a key–value store that persists across re-runs. Used to keep topics, current index, cached teachings, Q&A, chat history, and upload key so the app doesn’t “forget” after each click.
- **Rerun**: `st.rerun()` forces an immediate re-run so the UI updates after changing state (e.g. after processing upload or adding a chat message).

### 2.1.3 Layout and Structure

- **Sidebar**: `st.sidebar` for outline and “Start over.”
- **Main area**: Title, uploader, current topic, teaching block, quiz, chat, navigation.
- **Columns**: `st.columns` for Previous / (space) / Next buttons.

### 2.1.4 Chat UI

- `st.chat_message(role)` and `st.chat_input(placeholder)` provide a chat-style interface.
- Messages are stored in `st.session_state.chat_messages[topic_index]` as a list of `{"role": "user"|"assistant", "content": "..."}`.

---

## 2.2 PDF Processing

### 2.2.1 Why PDFs Are Non-Trivial

PDFs store layout and graphics, not a single “text stream.” Extracting text requires a library that understands PDF structure (streams, fonts, positioning).

### 2.2.2 PyMuPDF (fitz)

- **Role**: Open a PDF, iterate pages, extract text per page.
- **API used**: `fitz.open(path)`, `doc.load_page(i)`, `page.get_text()`.
- **Page numbering**: We use 1-based page numbers for the user (e.g. “page 1”); internally we still use 0-based indices.

### 2.2.3 Text Extraction Strategy

- Extract text page by page so we can later map content to pages if needed.
- Join pages with newlines (or use boundaries) to form one document string for the chunker and teacher.
- Very long documents are truncated in the chunker to stay within LLM context limits.

---

## 2.3 Large Language Models (LLMs)

### 2.3.1 What an LLM Does Here

The app uses an LLM as a single backend for:

- **Structured task**: “Split this document into topics and return JSON.”
- **Generation task**: “Explain this topic,” “Generate quiz Q&A,” “Answer this student question.”

The same model is used for all of these; only the system/user prompts and the data (document or topic text) change.

### 2.3.2 Prompts and Roles

- **System prompt**: Defines the “role” and rules (e.g. “You are a teacher; answer only from the document”).
- **User (Human) message**: Contains the actual data and request (e.g. document text, topic content, or the student’s question).
- **Assistant message**: In chat we send previous assistant replies so the model has conversation history (multi-turn).

### 2.3.3 Temperature

- We use a low temperature (e.g. `0.3`) so outputs are more deterministic and focused on the provided content rather than creative deviation.

### 2.3.4 Context Limits

- Models have a maximum context length (tokens). We truncate long document/topic text (e.g. 120k characters for chunking, 25–30k for teaching/QA/chat) to avoid exceeding limits.

---

## 2.4 LangChain

### 2.4.1 Why LangChain

LangChain gives a common interface (messages in, message out) for different providers (OpenAI, Anthropic). The app can switch providers by changing env vars and one factory function.

### 2.4.2 Message Types

- **SystemMessage**: Instructions and context (e.g. “You are a teacher…” plus document section).
- **HumanMessage**: User or “user-like” content (e.g. document text, student question).
- **AIMessage**: Assistant’s previous replies in a conversation.

### 2.4.3 Invocation

- `llm.invoke(messages)` returns a response object; we read `response.content` (or fallback to `str(response)`) for the text.

### 2.4.4 Provider-Specific Packages

- `langchain_openai.ChatOpenAI`: OpenAI API (e.g. GPT-4o).
- `langchain_anthropic.ChatAnthropic`: Anthropic API (e.g. Claude).
- Both are created with `api_key`, `model`, and `temperature`; the rest of the code only uses `invoke(messages)`.

---

## 2.5 Document Chunking and “RAG-like” Flow

### 2.5.1 Not Classical RAG

We do not use vector DB or semantic search. The “retrieval” step is **LLM-based chunking**: the model reads the full document and returns logical topics with verbatim excerpts. So “retrieval” is done once at the start (per document).

### 2.5.2 Topic = Chunk

- Each topic has a **title** and **content** (excerpt from the document).
- All downstream steps (teach, quiz, chat) use only that topic’s content so answers stay grounded.

### 2.5.3 Structured Output (JSON)

- For chunking and quiz generation we ask the LLM to return JSON (e.g. `[{"title":"...", "content":"..."}]` or `[{"question":"...", "answer":"..."}]`).
- We strip optional markdown code fences (```json ... ```) and parse with `json.loads`; on failure we use a fallback (e.g. single “Full document” topic or empty Q&A list).

---

## 2.6 Session State and Caching

### 2.6.1 Why Session State

Streamlit re-runs the script on every interaction. Without persistent state we would lose the list of topics, current topic index, generated teachings, quiz Q&A, and chat history. `st.session_state` holds all of that.

### 2.6.2 What We Store

- **topics**: List of `Topic` (title, content) after chunking.
- **current_topic_index**: Which topic is shown.
- **topic_teachings**: Dict mapping topic index → generated explanation text (cache).
- **topic_qa**: Dict mapping topic index → list of `QuizItem` (cache).
- **user_answers**: Dict mapping topic index → list of user answer strings for the quiz.
- **chat_messages**: Dict mapping topic index → list of `{role, content}` for the teacher chat.
- **doc_processed**: Whether we have already run chunking for the current upload (avoids re-running on every rerun).
- **upload_key**: Integer used in the file uploader’s key so that “Start over” can reset the uploader by changing the key.

### 2.6.3 Caching Effect

- “Explain this topic” and “Generate Q&A” are run once per topic and stored; we don’t call the LLM again unless the user clicks “Regenerate.”
- Chat history is accumulated in `chat_messages[idx]` so the teacher can use previous turns when answering.

---

## 2.7 Environment and Configuration

### 2.7.1 Twelve-Factor Style

- Configuration (provider, API keys, optional model names) lives in the environment, not in code.
- `.env` is loaded with `python-dotenv`; we read with `os.getenv(...)`.

### 2.7.2 Variables Used

- **DEFAULT_PROVIDER**: `openai` or `anthropic`.
- **OPENAI_API_KEY**, **ANTHROPIC_API_KEY**: API keys (at least one required for the chosen provider).
- **OPENAI_MODEL**, **ANTHROPIC_MODEL**: Optional overrides for model name.

### 2.7.3 Validation

- If the selected provider’s key is missing or is the placeholder value, we raise a clear `ValueError` so the app can show a helpful message (e.g. “Set OPENAI_API_KEY in .env”).

---

## 2.8 Multi-Turn Chat and Grounding

### 2.8.1 Goal

The “Ask the teacher” feature should answer only from the document (current topic). Follow-up questions should still be grounded in that same content and in the prior chat turns.

### 2.8.2 How It’s Done

- **System message**: Contains full instructions and the **document section** (topic title + content) so every reply is conditioned on that section.
- **Conversation history**: Previous user and assistant messages are appended in order so the model sees the full thread.
- **New question**: Appended as the latest `HumanMessage`. The model then generates the next assistant reply.

### 2.8.3 Out-of-Scope Questions

The system prompt tells the model to say when a question is outside the given content and to suggest re-reading or asking more specifically. This keeps the “teacher” honest and avoids hallucination beyond the document.

---

## 2.9 Answer Checking (Quiz)

### 2.9.1 No LLM for Checking

To keep the app simple and fast, quiz answers are checked with **string matching**, not an LLM:

- Normalize: strip and lower-case both user answer and correct answer.
- Consider correct if: exact match, or one string contains the other (with a simple check so empty user answer isn’t marked correct).

### 2.9.2 Optional Extension

A more advanced version could use the LLM to judge “semantic correctness” (e.g. “Is the user’s answer equivalent in meaning?”). The current design prioritizes simplicity and predictability.

---

# Part 3: Code Explanation

This part walks through every project file and explains the code in order.

---

## 3.1 `llm_config.py`

**Purpose**: Load env, choose LLM provider, and return a LangChain chat model.

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 1–8    | Module docstring, `__future__`, `os`, `load_dotenv` | Standard setup; `load_dotenv()` loads `.env` so `os.getenv` can read it. |
| 10–12  | `DEFAULT_OPENAI_MODEL`, `DEFAULT_ANTHROPIC_MODEL` | Default model names if the user doesn’t set `OPENAI_MODEL` / `ANTHROPIC_MODEL`. |
| 15–24  | `get_llm()` docstring and start | Function that returns the right chat model. Reads `DEFAULT_PROVIDER` (default `openai`). |
| 26–40  | `if provider == "openai"` | Check `OPENAI_API_KEY`; if missing or placeholder, raise `ValueError`. Import `ChatOpenAI`, read model from env (or default), return `ChatOpenAI(model=..., api_key=..., temperature=0.3)`. |
| 42–56  | `if provider == "anthropic"` | Same idea for Anthropic: check `ANTHROPIC_API_KEY`, import `ChatAnthropic`, return with model, key, temperature. |
| 58–61  | `raise ValueError(...)` | If provider is neither `openai` nor `anthropic`, fail with a clear message. |
| 64–76  | `get_available_provider()` | Iterate over providers and return the first one that has a non-placeholder API key (useful for UI or fallback logic). |

---

## 3.2 `doc_loader.py`

**Purpose**: Load a PDF and expose text per page or as one string (and optional page boundaries).

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 1–9    | Imports, `PageContent` dataclass | `PageContent` holds `page_num` (int) and `text` (str) for one page. |
| 21–46  | `load_pdf(path)` | Convert `path` to `Path`; raise `FileNotFoundError` if missing. Open with `fitz.open(path)`. Loop over pages: `doc.load_page(i)`, `page.get_text()`, append `PageContent(page_num=i+1, text=text)`. Close doc in `finally`. Return list of `PageContent`. |
| 49–60  | `load_pdf_as_text(path)` | Call `load_pdf(path)` and join each page’s text with `"\n\n"`. Returns one string (full document). |
| 63–86  | `get_full_text_with_page_boundaries(path)` | Same as loading pages, but build one string and a list of `(start, end)` character offsets per page. Used if you need to map chunks back to page ranges. |

---

## 3.3 `chunker.py`

**Purpose**: Take full document text and use the LLM to split it into topics (title + content per topic).

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 1–12   | Imports, `Topic` dataclass | `Topic` has `title` and `content` (both strings). Uses `HumanMessage`, `SystemMessage` from LangChain and `get_llm` from `llm_config`. |
| 23–34  | `extract_topics(full_text, max_topics)` | If text is empty, return `[]`. If longer than 120k chars, truncate and append a short note to avoid context overflow. |
| 36–48  | System and user prompts, `invoke` | System: you split the document into topics; return JSON `[{"title":"...", "content":"..."}]`; content must be verbatim; use 3–max_topics topics. User: the document text. Build `messages`, call `llm.invoke(messages)`, get `content`, pass to `_parse_topics_response`. |
| 61–84  | `_parse_topics_response(content)` | Strip content; if it starts with ```, remove JSON code fence. `json.loads(content)`. On error or if not a list, return one topic “Full document” with truncated raw content. Else loop over list: for each dict, get `title` and `content`, validate types, append `Topic(...)`. If no valid topics, same single-topic fallback. Return list of `Topic`. |

---

## 3.4 `teacher.py`

**Purpose**: Three LLM-backed operations—teach a topic, generate quiz Q&A, answer a student question (with optional history).

### 3.4.1 Data and `teach_topic`

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 15–19  | `QuizItem` | Dataclass: `question` and `answer` (strings). |
| 22–48  | `teach_topic(topic_title, topic_content)` | If content empty, return a fixed message. System prompt: you are a teacher; explain in a structured way; use only the provided text. User prompt: topic title + content. `invoke` with `[SystemMessage, HumanMessage]`; return `response.content`. |

### 3.4.2 `generate_qa`

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 51–81  | `generate_qa(topic_title, topic_content, num_questions=5)` | If content empty, return `[]`. System: return JSON only, format `[{"question":"...", "answer":"..."}]`, base on the text. User: topic + content (truncated to 30k). Invoke; parse with `_parse_qa_response`; return list of `QuizItem`. |
| 138–160 | `_parse_qa_response(content)` | Strip; remove ``` fences; `json.loads`. If not a list, return `[]`. For each dict, get question/answer (or q/a); append `QuizItem` if both are non-empty strings. Return list. |

### 3.4.3 `answer_question`

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 84–135 | `answer_question(topic_title, topic_content, user_question, conversation_history)` | If content empty, return fixed message. Build context string (topic + document section, truncated). System prompt: you are a teacher; answer only from the document section below; handle out-of-scope politely; then append full context to system. Build `messages`: `[SystemMessage(system_prompt)]` + for each turn in `conversation_history`: `HumanMessage` or `AIMessage` by role + `HumanMessage(user_question)`. Invoke; return `response.content`. |

---

## 3.5 `app.py`

**Purpose**: Streamlit UI and flow—upload, outline, topic view, teaching, quiz, chat, navigation.

### 3.5.1 Helpers and State Init

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 15–16  | `_normalize(s)` | Strip and lower-case a string; used for comparing quiz answers. |
| 18–34  | `_init_state()` | Initialize `st.session_state` keys if missing: `topics`, `current_topic_index`, `topic_teachings`, `topic_qa`, `user_answers`, `doc_processed`, `upload_key`, `chat_messages`. |

### 3.5.2 Page Setup and LLM Check

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 37–39  | `main()`, `set_page_config`, `_init_state()` | Set page title and layout; ensure state exists. |
| 41–50  | Title, caption, LLM check | Show title and short caption. Try `get_llm()`; on `ValueError` show error and instructions, then `return` so the rest of the app doesn’t run without a valid config. |

### 3.5.3 Upload and Chunking

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 53–69  | File uploader, temp file, processing | `st.file_uploader` with key that includes `upload_key` (so “Start over” can reset it). If file is present and `doc_processed` is False: write upload to a temp PDF file, call `load_pdf_as_text`, then `extract_topics`; set `doc_processed=True`, `current_topic_index=0`; on success show message; on exception show error and return; in `finally` delete temp file. |
| 71–75  | No topics | If after init/upload we still have no topics, show “Upload a PDF” and return. |

### 3.5.4 Sidebar

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 77–94  | Sidebar: outline, Start over | In `st.sidebar`: subheader “Outline”; for each topic a button with label `"1. Title"` etc.; on click set `current_topic_index` and `st.rerun()`. Divider; “Start over” button clears all state (topics, teachings, qa, answers, chat_messages), increments `upload_key`, and reruns. |

### 3.5.5 Current Topic and Teaching Block

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 95–99  | Current topic | `idx = current_topic_index`, `current = topics[idx]`. |
| 101–115 | Teaching | Subheader = current title. If no cached teaching for `idx`: show “Explain this topic” button; on click call `teach_topic`, store in `topic_teachings[idx]`, rerun. Else show cached teaching and “Regenerate explanation” (same call, then rerun). |

### 3.5.6 Quiz Block

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 117–162 | Quiz | If no Q&A for `idx`: “Generate Q&A” button; on click call `generate_qa`, store in `topic_qa[idx]`, init `user_answers[idx]`, rerun. Else: load `qa_list` and `user_answers`; for each question show label and `st.text_input` (key includes `idx` and `i`); sync `user_answers[idx]`. “Check answers”: for each item normalize user and correct answer, compare (exact or substring), show ✅/❌ and correct answer. “Regenerate Q&A”: regenerate, reset user answers, rerun. |

### 3.5.7 Chat Block

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 164–195 | Ask the teacher | Subheader and caption. Ensure `chat_messages[idx]` exists (empty list if not). Render each message with `st.chat_message(msg["role"])` and `st.markdown(msg["content"])`. `st.chat_input(...)`: when user sends, append user message to `chat_list`, call `answer_question` with current topic, prompt, and `history=chat_list[:-1]`, show reply in assistant bubble, append assistant message to `chat_list`, save to `chat_messages[idx]`, rerun. “Clear chat for this topic” clears `chat_messages[idx]` and reruns. |

### 3.5.8 Navigation

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 197–205 | Previous / Next | Three columns; column 1: “Previous topic” (if `idx > 0` decrement index and rerun); column 3: “Next topic” (if not last, increment and rerun). |

### 3.5.9 Entry Point

| Line(s) | Code / concept | Explanation |
|--------|-----------------|-------------|
| 208–209 | `if __name__ == "__main__"` | Call `main()` when the script is run directly (e.g. `streamlit run app.py`). |

---

## 3.6 Supporting Files (Brief)

- **requirements.txt**: Lists `streamlit`, `pymupdf`, `langchain`, `langchain-openai`, `langchain-anthropic`, `langchain-core`, `python-dotenv` (and versions). Install with `pip install -r requirements.txt`.
- **.env.example**: Template with `DEFAULT_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and optional model overrides. User copies to `.env` and fills in keys.
- **.gitignore**: Excludes `.env`, `__pycache__`, `.venv`, `.streamlit`, etc., so secrets and caches aren’t committed.
- **README.md**: Describes the project, setup (install, `.env`, `streamlit run app.py`), usage, and file layout.

---

This learning document covers the project description, the theory behind the main topics and subtopics used in development, and a code-level explanation of every file and important block in the Teaching Assistant codebase.

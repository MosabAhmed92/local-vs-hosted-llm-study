# The Full Round-Trip of a "Hello" Message in Open WebUI + Ollama

> **Context**: Mac setup — Ollama runs natively on your Mac, Open WebUI runs in a single Docker container.  
> Port mapping: Mac port `8080` → Container port `8080` (or `3000:8080` depending on your compose file).

---

## Table of Contents

1. [The Outgoing Journey — "hello" leaving Chrome](#the-outgoing-journey--hello-leaving-chrome)
2. [The Incoming Journey — the response reaching you](#the-incoming-journey--the-response-reaching-you)
3. [What is saved in openwebui_data](#what-is-saved-in-openwebui_data)

---

## The Outgoing Journey — "hello" leaving Chrome

### Step 1 — Chrome on your Mac

You type `localhost:8080` in Chrome and hit Enter (or `localhost:3000` if that's your Mac-side mapping). Chrome opens a TCP connection to `127.0.0.1` port `8080` on your own Mac. It sends a standard HTTP GET request asking for the Open WebUI page. Open WebUI's JavaScript loads in your browser. You type "hello" and click Send. Chrome's JavaScript now sends an **HTTP POST request** — still to `localhost:8080` on your Mac — carrying a JSON body with your message, your session token, and the model you've selected.

### Step 2 — The Docker port bridge intercepts it

Docker is silently listening on your Mac's port `8080`. It grabs the TCP connection and forwards it across the internal Docker network into the Open WebUI container — specifically to `172.18.0.x:8080` (the container's internal IP). Your Mac knows nothing about what happens after this handoff.

```
YOUR MAC
  Chrome → localhost:8080 (your Mac's port)
                │
                ▼
  Docker port bridge
  Listening on Mac:8080
  Forwarding to Container:8080
                │
                ▼
  Open WebUI container
  internal IP: 172.18.0.x
  listening on its own port 8080
```

### Step 3 — Open WebUI's web server receives it

Inside the container, **Uvicorn** (the Python web server) is listening on `0.0.0.0:8080` — the container's own port 8080, which has nothing to do with your Mac's port 8080. These are the same number but on completely different machines. Uvicorn hands the request to FastAPI.

> **Reminder**: port 8080 on your Mac and port 8080 inside the container are two entirely separate things. The same number is a coincidence of configuration — they are on two different virtual computers.

### Step 4 — FastAPI authenticates and saves your message

FastAPI reads the JWT session token from your request headers and verifies it against the users stored in the SQLite database. Once you're confirmed as a valid logged-in user, it does two things:

- Creates or retrieves your current chat session (with a UUID and a title, likely auto-generated from "hello")
- Writes your message to the database: `role = "user"`, `content = "hello"`, `timestamp = now`

> **This write happens before Ollama is even contacted.** Your message is persisted the moment you send it, regardless of whether Ollama responds successfully.

### Step 5 — Open WebUI calls Ollama

The backend now formats a new HTTP POST to Ollama — specifically to:

```
http://host.docker.internal:11434/api/chat
```

It includes your full conversation history, the model name, and `stream: true`.

The address `host.docker.internal` is a special hostname Docker provides inside every container. It resolves to your Mac's own IP address — because Ollama is running natively on your Mac, not in any container. This is the only way for the container to reach back out to a process running on the Mac itself.

```
Open WebUI container
  Sends POST to: http://host.docker.internal:11434/api/chat
                │
                │ host.docker.internal = your Mac's IP
                │ as seen from inside the container
                ▼
  YOUR MAC (natively)
  Ollama process listening on Mac's localhost:11434
```

### Step 6 — Ollama receives it and starts working

Ollama, running as a regular Mac process on port `11434`, receives the POST. If the model isn't already in RAM it loads it from disk (from `~/.ollama/models/` on your Mac — no Docker involved). It tokenizes "hello" (converts it into numeric IDs the model understands) and begins the transformer inference pass — billions of matrix multiplications producing a probability distribution over the next token.

---

## The Incoming Journey — the response reaching you

### Step 7 — Ollama streams tokens, not the full response

Ollama doesn't wait until it finishes generating. Because the request included `stream: true`, it sends each token back immediately as it's produced:

```
"Hi" → " there" → "!" → " How" → " can" → " I" → " help" → " you" → " today" → "?"
```

Each chunk is a tiny JSON object sent over the still-open HTTP connection back to the Open WebUI container via `host.docker.internal`. Streaming is why you see the response appearing token by token in the UI — you're watching live inference, not a delayed reveal of a finished response.

### Step 8 — Open WebUI relays each token to Chrome

The Open WebUI backend receives each tiny chunk from Ollama and **immediately** forwards it to your Chrome browser without waiting for more. It uses **Server-Sent Events (SSE)** — a technique where the original HTTP response connection stays open and the server pushes data down it in real time.

Each token chunk travels the same path as the original request, in reverse:

```
Ollama (Mac native)
  → host.docker.internal (back into the container)
  → Open WebUI backend (relays instantly)
  → Container port 8080
  → Docker port bridge
  → Mac port 8080
  → Chrome
```

The original POST connection from Chrome is never closed until the full response is done. The SSE events ride on it.

### Step 9 — Chrome renders tokens word by word

Chrome's JavaScript is listening for SSE events on that open connection. Every time a new token chunk arrives, it appends it to the chat message in the UI. This is why you see the response appearing letter by letter or word by word — each token arrives individually in real time as Ollama produces it.

### Step 10 — Ollama signals it's done

When Ollama has finished generating, it sends a final chunk with `"done": true`. The Open WebUI backend catches this, closes the connection to Ollama, and then saves the **complete assistant response** to the SQLite database:

```
role    = "assistant"
content = "Hi there! How can I help you today?"
model   = "llama2"   (or whichever model you selected)
tokens  = 12         (example)
time    = 847ms      (example generation time)
```

Then it sends a final SSE event to Chrome indicating completion.

### Step 11 — Chrome marks the conversation complete

Chrome's JavaScript receives the "done" signal, stops the typing animation, re-enables the input field, and updates the chat title in the sidebar (if it was auto-generated from your first message).

---

## The Full Picture — Both Directions

```
YOUR MAC
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Chrome (browser)                                               │
│  ↓ HTTP POST "hello"           ↑ SSE token chunks arriving     │
│                                                                 │
│  Docker port bridge                                             │
│  Mac:8080 ←→ Container:8080                                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Open WebUI Container                                     │  │
│  │                                                           │  │
│  │  Uvicorn web server (port 8080 inside container)         │  │
│  │       ↓                              ↑                   │  │
│  │  FastAPI backend                                          │  │
│  │  ├── Authenticates user                                   │  │
│  │  ├── Saves user message to SQLite DB ←──────────────┐    │  │
│  │  ├── POSTs to host.docker.internal:11434             │    │  │
│  │  └── Relays SSE tokens back to Chrome        Saves   │    │  │
│  │       ↓                              ↑       response│    │  │
│  └───────│──────────────────────────────│───────────────┘    │  │
│          │ host.docker.internal         │                     │  │
│          ↓ (resolves to Mac's IP)       │ streams done=true   │  │
│                                         │                     │  │
│  Ollama (native process on your Mac)    │                     │  │
│  Port 11434 — no Docker involved        │                     │  │
│  Loads model → tokenizes → infers ──────┘                    │  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What is saved in `openwebui_data`

This Docker volume is mounted at `/app/backend/data` inside the Open WebUI container. On your Mac it physically lives in Docker's internal volume storage (managed by Docker Desktop — not a regular folder you browse in Finder).

### The most important file: `webui.db`

A single **SQLite database file**. Everything Open WebUI knows lives in here.

For your "hello" conversation, the following is written:

**In the `chat` table** — one row per conversation:

| Field | Value |
|---|---|
| `id` | A UUID (e.g. `a3f7c1d2-...`) |
| `user_id` | Your user's UUID |
| `title` | Auto-generated (e.g. "Hello") |
| `created_at` | Timestamp when you sent the message |
| `updated_at` | Timestamp of the last response |

**In the messages** (stored as JSON inside the chat row or a separate table, depending on version) — two entries:

```json
{ "role": "user",      "content": "hello" }
{ "role": "assistant", "content": "Hi there! How can I help you today?",
  "model": "llama2", "tokens": 12, "duration_ms": 847 }
```

**In the `user` and `auth` tables** — written when you first created your account:

| Field | What it holds |
|---|---|
| `name` | Your display name |
| `email` | Your login email |
| `password` | Bcrypt hash (never stored in plain text) |
| `role` | `admin` (first user) or `user` |
| `created_at` | Account creation timestamp |

### Other files in `/app/backend/data/`

| File / Folder | What it contains |
|---|---|
| `webui.db` | The entire SQLite database — users, chats, messages, settings |
| `uploads/` | Any files you attach to messages (empty for plain text chats) |
| `cache/` | Temporary files generated at runtime |
| Various `.json` config files | App-level settings, saved prompts, custom model configs |

### The critical insight about volumes and data safety

```
docker compose down          → containers deleted, VOLUME SURVIVES ✅
docker compose down -v       → containers deleted, VOLUME DELETED ❌

docker compose up            → new container, mounts the SAME volume
                               all your chats and accounts are still there ✅
```

`webui.db` is the only file you need to back up if you care about your chat history and accounts. As long as the `openwebui_data` volume exists on your Mac, no amount of container restarts, image updates, or `docker compose down` commands will lose your data. The only way to lose it is `docker compose down -v` or manually deleting the volume.

---

*The user message is always saved before Ollama is called. The assistant response is saved after the last token arrives. If Ollama crashes mid-response, the user message is already in the DB but the assistant response may be incomplete or missing.*

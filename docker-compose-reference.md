# A Comprehensive Guide to Docker Compose for AI Applications
> **Focus: Open WebUI + Ollama** *(with contrast to a FastAPI project)*

---

## Table of Contents

1. [The Mental Model: From Docker to Docker Compose](#1-the-mental-model-from-docker-to-docker-compose)
2. [How Open WebUI and Ollama Fit Into This Architecture](#2-how-open-webui-and-ollama-fit-into-this-architecture)
3. [Mac vs. Linux Setup Differences](#3-mac-vs-linux-setup-differences)
   - 3.1 [The Mac Reality: Why Ollama Runs on Your Mac, Not in a Container](#31-the-mac-reality-why-ollama-runs-on-your-mac-not-in-a-container)
   - 3.2 [The Compose Irony on Mac](#32-the-compose-irony-on-mac)
   - 3.3 [Windows + NVIDIA GPU: Where Compose Truly Shines](#33-windows--nvidia-gpu-where-compose-truly-shines)
   - 3.4 [Side-by-Side: Mac vs Windows vs Linux](#34-side-by-side-mac-vs-windows-vs-linux)
4. [Demystifying Services (The Blueprint)](#4-demystifying-services-the-blueprint)
5. [Demystifying Port Mapping](#5-demystifying-port-mapping-the-thing-driving-you-crazy)
6. [Demystifying Environment Variables](#6-demystifying-environment-variables)
7. [Demystifying Networking (How Containers Talk)](#7-demystifying-networking-how-containers-talk)
8. [Volumes: Why Data Survives](#8-volumes-why-data-survives)
9. [Full compose.yaml for Open WebUI + Ollama](#9-full-composeyaml-for-open-webui--ollama)
10. [What Actually Happens After `docker compose up -d`](#10-what-actually-happens-after-docker-compose-up--d)
11. [The Reverse: `docker compose down`](#11-the-reverse-docker-compose-down)
12. [Comparison: FastAPI Project vs. Open WebUI + Ollama](#12-a-comparison-your-fastapi-project-vs-open-webui--ollama)
13. [Why Do I Suddenly Need Docker Compose?](#13-i-already-know-dockerfiles-why-do-i-suddenly-need-docker-compose)
14. [Step-by-Step: Running the Stack](#14-step-by-step-running-the-stack)
15. [Managing Models with Ollama](#15-managing-models-with-ollama)
16. [Common Pitfalls and Solutions](#16-common-pitfalls-and-solutions)
17. [Visual Reference: Everything Together](#17-visual-reference-everything-together)
18. [Conclusion & Final Mental Checklist](#18-conclusion)

---

## 🖥️ The Core Idea You Must Never Forget

> Before reading anything else, burn this into your brain — it will make every section below click immediately.

**When Docker creates a container, it is building a brand-new, isolated virtual computer.**
That virtual computer has its own operating system, its own filesystem, its own network — and critically — **its own `localhost` and its own set of ports.**

Think of it this way:

```
┌─────────────────────────────────────────────────────────┐
│  YOUR MAC (the real computer)                           │
│  localhost = your Mac                                   │
│  Ports: 3000, 8080, 11434, etc. belong to your Mac     │
│                                                         │
│   ┌──────────────────────────────┐                      │
│   │  CONTAINER: open-webui       │                      │
│   │  (a virtual computer)        │                      │
│   │  localhost = open-webui only │                      │
│   │  Its own ports: 8080         │                      │
│   └──────────────────────────────┘                      │
│                                                         │
│   ┌──────────────────────────────┐                      │
│   │  CONTAINER: ollama           │                      │
│   │  (another virtual computer)  │                      │
│   │  localhost = ollama only     │                      │
│   │  Its own ports: 11434        │                      │
│   └──────────────────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

You have **three separate computers** in this picture:
- Your Mac
- The Open WebUI virtual computer (container)
- The Ollama virtual computer (container)

Each one has its own `localhost`. They are completely isolated from each other by default. They do **not** share ports. A port open inside a container is **invisible** to your Mac and to other containers — unless you explicitly create a bridge.

**Port mapping** = punching a hole from your Mac's port → into the virtual computer's port.  
**Docker networking** = creating a private LAN so the virtual computers can talk to each other.  
**Service names** = the hostnames the virtual computers use to find each other (like `ollama` or `open-webui`).

This single mental model explains everything that follows. Keep coming back to it.

---

## 1. The Mental Model: From Docker to Docker Compose

### 1.1 What Problem Does Docker Solve?

Docker solves the **"it works on my machine"** problem. It packages an application and all its dependencies into a container (a virtual computer) that runs consistently anywhere Docker is installed — on your Mac, on a Linux server, anywhere.

### 1.2 What Is a Docker Image?

A Docker image is a **lightweight, standalone, executable package** that includes everything needed to run software (OS base, runtime, dependencies, code, config). Images are **read-only templates** — the blueprint for a virtual computer before it's switched on.

### 1.3 What Is a Container?

A container is a **running instance** of a Docker image — the virtual computer actually switched on and running. It is **ephemeral by default** — any changes inside are lost when it stops, unless you use volumes. Think of it like a virtual machine that boots from a snapshot: every time you start it, it starts fresh from the image unless you explicitly persist data.

### 1.4 What Does a Dockerfile Do?

A Dockerfile is a script that **builds a Docker image** — it defines what goes inside the virtual computer. A typical FastAPI project might have:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This creates a virtual computer that has Python installed, your code copied in, and a startup command ready to go.

### 1.5 Why Dockerfiles Become Inconvenient for Real Projects

A single-container FastAPI project is simple — one virtual computer is enough:

- Build it: `docker build -t sentiment-api .`
- Run it: `docker run -p 8000:8000 sentiment-api`

It works because there is only one virtual computer, no persistent storage, and no communication needed with other virtual computers.

But **Open WebUI + Ollama** has two separate virtual computers that must:

- Talk to each other over a network
- Persist data (models, user data)
- Start together and stop together
- Be configured correctly

Managing this manually with `docker run` commands becomes a nightmare. That's where **Docker Compose** comes in.

### 1.6 What Is Docker Compose?

Docker Compose is a tool for defining and running **multi-container applications** — multiple virtual computers — with a single `compose.yaml` file. One command — `docker compose up` — boots all the virtual computers exactly as defined.

### 1.7 The Relationship Between Dockerfile and Docker Compose

- **Dockerfile** → builds the image (designs the virtual computer)
- **Docker Compose** → uses images to create and run the containers (boots the virtual computers and connects them)

For Open WebUI and Ollama, you typically use official pre-built images, so you **don't need a Dockerfile** — only `compose.yaml`.

### 1.8 When You Need Both vs. Only Compose

| Scenario | Dockerfile | Compose |
|---|---|---|
| Single container, custom app (FastAPI project) | ✅ Needed | ❌ Not needed |
| Multiple containers, official images (Open WebUI + Ollama) | ❌ Not needed | ✅ Needed |
| Multiple containers, some custom code | ✅ For custom ones | ✅ Needed |

---

## 2. How Open WebUI and Ollama Fit Into This Architecture

- **Open WebUI**: A full-stack web interface for LLMs (chat UI, user management). Runs as one virtual computer (container).
- **Ollama**: A lightweight LLM server that runs models locally and exposes a REST API on port `11434`. Runs as a second virtual computer (container).

**They work together:**

```
Your Mac's browser → Open WebUI virtual computer (port 3000 on your Mac, forwarded to port 8080 inside)
Open WebUI virtual computer → Ollama virtual computer (via internal network at http://ollama:11434)
Ollama generates a response and sends it back.
Open WebUI displays it in your browser.
```

They must be on the **same Docker private network** so that the Open WebUI virtual computer can reach the Ollama virtual computer using the service name (`ollama`) as the hostname — like two computers on the same LAN finding each other by name.

---

## 3. Mac vs. Linux Setup Differences

| Aspect | Linux | macOS (Apple Silicon/Intel) |
|---|---|---|
| Docker runs | Natively on host kernel | Inside a lightweight Linux VM |
| GPU support | Yes (NVIDIA, with `--gpus all`) | Not supported (CPU only) |
| Volume performance | Native | Slower for bind mounts; use named volumes |
| Architecture | x86_64 or ARM64 | ARM64 (Apple Silicon) or x86_64 (Intel). Ensure multi-arch images. |

---

### 3.1 The Mac Reality: Why Ollama Runs on Your Mac, Not in a Container

This is something the table above hints at but doesn't fully explain — and it has a direct, practical impact on how you use Docker Compose on your Mac.

On Mac, Docker runs inside a lightweight Linux VM managed by Docker Desktop. This creates a fundamental problem for Ollama specifically:

1. **No GPU passthrough**: Your Mac's GPU (or Apple Silicon's Neural Engine) cannot be accessed from inside a Docker container. If you ran Ollama inside a container on Mac, it would be forced into CPU-only mode — painfully slow for most models.
2. **Extra VM overhead**: Even if performance were acceptable, the additional virtualization layer adds latency and resource cost that is completely unnecessary.

**The practical result**: on Mac, Ollama does not run in a container at all. It runs **natively on your Mac** — installed directly via `brew install ollama` and started with `ollama serve`. It is a regular Mac process, just like any other app.

Only **Open WebUI** runs in a container.

This changes the entire architecture picture:

```
┌──────────────────────────────────────────────────────────┐
│  YOUR MAC (the real, physical computer)                  │
│                                                          │
│  Ollama running NATIVELY here (not in any container)     │
│  → Installed via: brew install ollama                    │
│  → Started via:   ollama serve                           │
│  → Listening on YOUR MAC's own localhost:11434           │
│                                                          │
│   ┌────────────────────────────────────────┐             │
│   │  CONTAINER: open-webui                 │             │
│   │  (one virtual computer)                │             │
│   │                                        │             │
│   │  Needs to reach Ollama — but Ollama    │             │
│   │  is NOT in another container.          │             │
│   │  It's running on the Mac OUTSIDE.      │             │
│   │                                        │             │
│   │  Uses: http://host.docker.internal:11434│            │
│   │  ↑ special address meaning "the Mac"   │             │
│   └────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────┘
```

**`host.docker.internal`** is a special hostname that Docker automatically provides inside every container. It resolves to your Mac's own IP — allowing a container to reach services running natively on your Mac. This is the bridge between the Open WebUI virtual computer and the natively-running Ollama on your Mac.

So on Mac, the correct `OLLAMA_BASE_URL` in your compose.yaml is:

```
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Not `http://ollama:11434` (that would look for another container named `ollama`, which doesn't exist on Mac).  
Not `http://localhost:11434` (that would look inside the Open WebUI container itself).

The **Mac-specific `compose.yaml`** therefore has only **one service**:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"   # Bridge: Mac's port 3000 → container's port 8080
    volumes:
      - openwebui_data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434   # Reaches native Mac Ollama
    restart: unless-stopped

volumes:
  openwebui_data:
```

---

### 3.2 The Compose Irony on Mac

Here is a moment worth pausing on: **Docker Compose exists to connect multiple containers on a private network.** That is its core value proposition.

On your Mac, you have one container (Open WebUI) talking to a native Mac process (Ollama). There is no private Docker network involved. There is no second virtual computer. There is no inter-container communication at all.

So what is Compose doing for you on Mac?

Honestly — it's just a convenience wrapper. Instead of typing a long `docker run` command with all the flags, ports, volumes, and environment variables every time, you define it once in `compose.yaml` and run `docker compose up`. That's it. You are using Compose for its secondary benefit (reproducible, readable configuration), not its primary benefit (multi-container orchestration).

```
On Mac:
  compose.yaml has 1 service
  → Compose is used as a "nice docker run replacement"
  → The private network feature is unused
  → Ollama sits outside Docker entirely

On Windows/Linux with GPU:
  compose.yaml has 2 services
  → Compose is used for its actual purpose
  → Both containers on a private network, talking to each other
  → Full isolation, full orchestration
```

This is not a flaw or a mistake — it's simply the right architectural decision for Mac. Running Ollama natively gives you GPU access and better performance. The single-service compose.yaml is still a clean, portable way to manage the Open WebUI container.

---

### 3.3 Windows + NVIDIA GPU: Where Compose Truly Shines

On **Windows with an NVIDIA GPU** (using WSL2 + the NVIDIA Container Toolkit), Docker can pass through the GPU directly into a container. This changes everything:

- Ollama **can** run inside a container and still access the GPU at full speed
- Open WebUI runs in its own separate container
- Both containers live on Docker's private network
- The two-service `compose.yaml` is genuinely, fully useful

The architecture on Windows/Linux looks like this:

```
┌──────────────────────────────────────────────────────────┐
│  YOUR WINDOWS/LINUX MACHINE                              │
│                                                          │
│   ┌──────────────────────────────────────────────────┐   │
│   │  Docker Private Network                          │   │
│   │                                                  │   │
│   │  ┌─────────────────────┐  ┌───────────────────┐ │   │
│   │  │ Virtual Computer:   │  │ Virtual Computer: │ │   │
│   │  │ ollama              │  │ open-webui        │ │   │
│   │  │                     │  │                   │ │   │
│   │  │ Has GPU access ✅   │  │ Calls:            │ │   │
│   │  │ Port 11434 (inside) │  │ http://ollama:11434│ │   │
│   │  └─────────────────────┘  └───────────────────┘ │   │
│   │         ↑ Docker DNS resolves "ollama" here      │   │
│   └──────────────────────────────────────────────────┘   │
│                                                          │
│   Port bridge: Machine's port 3000 → container's 8080   │
└──────────────────────────────────────────────────────────┘
```

This is the setup where the full two-service `compose.yaml` (from Section 9) makes complete sense:

- Two isolated virtual computers, each doing one job
- Connected via Docker's private network
- Service name DNS (`ollama`) works perfectly
- One `docker compose up` boots both
- One `docker compose down` shuts both down cleanly

**The same `compose.yaml` that feels like overkill on Mac becomes the exactly right tool on Windows/Linux with a GPU.**

---

### 3.4 Side-by-Side: Mac vs Windows vs Linux

| Aspect | Mac (Apple Silicon / Intel) | Windows + NVIDIA GPU | Linux + NVIDIA GPU |
|---|---|---|---|
| Ollama location | Runs **natively on Mac** | Runs **in a container** | Runs **in a container** |
| Open WebUI location | Runs in a container | Runs in a container | Runs in a container |
| Number of containers | 1 | 2 | 2 |
| Compose services | 1 (`open-webui` only) | 2 (`ollama` + `open-webui`) | 2 (`ollama` + `open-webui`) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | `http://ollama:11434` | `http://ollama:11434` |
| Docker private network used | ❌ Not needed | ✅ Essential | ✅ Essential |
| Compose's main benefit | Convenience wrapper | Full orchestration | Full orchestration |
| GPU in container | ❌ Not possible | ✅ With NVIDIA Toolkit + WSL2 | ✅ With NVIDIA Toolkit |

---

## 4. Demystifying Services (The Blueprint)

In `compose.yaml`, a **service** is a definition of how to build and boot one virtual computer. It is **not the container itself** — it's the recipe. When you run `docker compose up`, Docker reads these recipes and boots each virtual computer.

```
compose.yaml (declarative blueprint — the recipes)
┌─────────────────────────────────────────────────────────┐
│ services:                                               │
│   ollama:       ← Recipe for virtual computer #1       │
│     image: ollama/ollama                               │
│     ports: ...                                         │
│                                                        │
│   open-webui:   ← Recipe for virtual computer #2      │
│     image: ghcr.io/open-webui/open-webui:main         │
│     environment: ...                                   │
└─────────────────────────────────────────────────────────┘
                        │
                        │ docker compose up
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Docker Engine reads the recipes and BOOTS the machines │
└─────────────────────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
┌─────────────────────┐   ┌─────────────────────────┐
│ Container: ollama   │   │ Container: open-webui   │
│ (Virtual computer   │   │ (Virtual computer       │
│  now running)       │   │  now running)           │
│  Its own localhost  │   │  Its own localhost      │
│  Its own port 11434 │   │  Its own port 8080      │
└─────────────────────┘   └─────────────────────────┘
```

> **Key takeaway:** One `service:` block = one virtual computer (container). The service is the *blueprint*, the container is the *running machine*.

---

## 5. Demystifying Port Mapping (The Thing Driving You Crazy)

Port mapping is written as **`"HOST_PORT:CONTAINER_PORT"`** — or more precisely: **`"YOUR_MAC_PORT:VIRTUAL_COMPUTER_PORT"`**.

**Why two numbers?**

Remember: your Mac and each container are separate computers, each with their own ports. A port open inside a container is completely invisible to your Mac. To let your browser (running on your Mac) talk to the application running inside a virtual computer, Docker creates a bridge — it listens on a port on your Mac and forwards traffic into the virtual computer's port.

Without this bridge, the virtual computer's port is sealed off. The application is running inside it, but your Mac can't reach it at all.

### Diagram: Browser → Your Mac → Virtual Computer (Container)

```
+------------------------------------------------------------------+
| YOUR MAC                                                         |
|  Your browser opens: http://localhost:3000                       |
|  (port 3000 on YOUR Mac)                                         |
|                  │                                               |
|                  ▼                                               |
|  +----------------------------------------------------------+    |
|  | DOCKER PORT BRIDGE                                       |    |
|  | Listening on YOUR MAC's port: 3000                       |    |
|  | Forwarding traffic into the virtual computer's port: 8080|    |
|  +----------------------------------------------------------+    |
|                              │                                   |
+------------------------------│-----------------------------------+
                               │ (crosses the boundary into
                               │  the virtual computer)
                               ▼
+------------------------------------------------------------------+
| VIRTUAL COMPUTER (open-webui container)                          |
|  Has its OWN localhost — completely separate from your Mac       |
|  Has its OWN ports — completely separate from your Mac          |
|                                                                  |
|  The application is LISTENING on THIS virtual computer's         |
|  port 8080.                                                      |
|                                                                  |
|  It does NOT know about port 3000 on your Mac.                  |
|  It only knows about its own internal port 8080.                |
+------------------------------------------------------------------+
```

**Why not map `8080:8080`?**
You can, but if port 8080 is already used by something on your Mac, you'll get a conflict. Mapping `3000:8080` means you pick port `3000` on your Mac to be the entry point — without touching the virtual computer's internal configuration at all.

**What about Ollama's `11434:11434`?**
This is optional but very useful for debugging. If you add this mapping, you can run `curl http://localhost:11434/api/generate` **on your Mac** to test Ollama directly, bypassing Open WebUI. Even without this mapping, the Open WebUI virtual computer can still reach Ollama's virtual computer through the private Docker network — the Mac doesn't need to be involved in that communication at all.

### Port Mapping Scenarios

| Compose Entry | Browser URL on Your Mac | Why? |
|---|---|---|
| `"3000:8080"` | `http://localhost:3000` | Mac's port 3000 bridges into the virtual computer's port 8080 |
| `"8080:8080"` | `http://localhost:8080` | Direct mapping (if port 8080 is free on your Mac) |
| `"80:8080"` | `http://localhost` (no port needed) | Mac's port 80 is default HTTP |
| No mapping for Ollama | N/A | Open WebUI's virtual computer reaches Ollama's virtual computer directly — your Mac is not involved |

> **Golden Rule:** The **left** number is a port on **your Mac** (what you type in your browser). The **right** number is a port on the **virtual computer** (what the application inside actually listens on). They are on completely separate machines.

---

## 6. Demystifying Environment Variables

Environment variables are how you **configure the behavior** of a virtual computer (container) without rebuilding its image.

### Diagram: How Environment Variables Flow

```
compose.yaml (on your Mac)
┌─────────────────────────────────────────────────────────────────┐
│ services:                                                       │
│   open-webui:                                                   │
│     environment:                                                │
│       - OLLAMA_BASE_URL=http://ollama:11434  ← You define this │
│       - WEBUI_SECRET_KEY=mysecretkey                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Docker injects these into the
                             │ virtual computer at boot time
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ VIRTUAL COMPUTER: open-webui (running container)                │
│                                                                 │
│  The process reads:                                             │
│  os.environ["OLLAMA_BASE_URL"] → "http://ollama:11434"         │
│                                                                 │
│  It uses this address to connect to the Ollama virtual computer│
│  on their shared private Docker network.                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Docker DNS resolves "ollama"
                             │ to the Ollama container's
                             │ internal IP on the private network
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ VIRTUAL COMPUTER: ollama (running container)                    │
│  Internal IP on Docker network: 172.17.0.3                      │
│  Listening on its own port 11434                                │
└─────────────────────────────────────────────────────────────────┘
```

### ⚠️ The Classic Beginner Mistake — The Three Localhosts

This is the most common confusion for people new to Docker, and it falls apart the moment you remember the core idea: **each container is a separate virtual computer with its own `localhost`**.

You have **three separate `localhost` values** in this stack:

```
YOUR MAC's localhost      → 127.0.0.1 on your actual physical Mac
open-webui's localhost    → 127.0.0.1 inside the open-webui virtual computer
ollama's localhost        → 127.0.0.1 inside the ollama virtual computer
```

These are **three completely different addresses**. They do not connect to each other.

So if you set `OLLAMA_BASE_URL=http://localhost:11434` inside the Open WebUI container — you are telling Open WebUI to look for Ollama at **its own `localhost`** — inside its own virtual computer. But Ollama is not there. Ollama is on a different virtual computer entirely. The request fails.

```
                    ❌ WRONG
open-webui virtual computer
  tries: http://localhost:11434
  → looks inside ITSELF for port 11434
  → Ollama is NOT here
  → CONNECTION REFUSED

                    ✅ CORRECT (Windows/Linux — Ollama in container)
open-webui virtual computer
  tries: http://ollama:11434
  → Docker DNS resolves "ollama" to the Ollama virtual computer's IP
  → reaches the correct machine
  → CONNECTION SUCCESS

                    ✅ CORRECT (Mac — Ollama running natively)
open-webui virtual computer
  tries: http://host.docker.internal:11434
  → Docker resolves this to your Mac's own IP
  → reaches Ollama running natively on your Mac
  → CONNECTION SUCCESS
```

You must use the **service name** (`ollama`) on Windows/Linux, or **`host.docker.internal`** on Mac — because in both cases, `localhost` inside the container refers only to that container itself.

### Where Do These Variables Come From?

- **Official documentation**: The Open WebUI docs tell you which variables it accepts (e.g., `OLLAMA_BASE_URL`).
- You define them in the `environment:` section of `compose.yaml` (on your Mac).
- You can also use an `env_file:` to load them from a `.env` file (useful for secrets, though secrets are better handled with Docker secrets in production).

---

## 7. Demystifying Networking (How Containers Talk)

When Compose starts, it automatically creates a **private network** — think of it as a private LAN cable connecting all your virtual computers together. Every container in that project is plugged into this private LAN. They can talk to each other using their **service names as hostnames**, exactly like computers on a local office network can ping each other by name.

Your Mac is **not** on this private LAN. Your Mac connects to individual containers only through the port bridges (port mappings) you define.

```
+---------------------------------------------------------------+
| YOUR MAC                                                      |
|  (Not on the Docker private network)                          |
|  Connects only via port bridges: localhost:3000, :11434       |
|                                                               |
|  +---------------------------------------------------+        |
|  | Docker Private Network: myproject_default          |        |
|  | (A private LAN for the virtual computers only)    |        |
|  |                                                   |        |
|  |  ┌──────────────────┐   ┌───────────────────────┐|        |
|  |  │ Virtual Computer │   │ Virtual Computer      ││        |
|  |  │ Service: ollama  │   │ Service: open-webui   ││        |
|  |  │ IP: 172.18.0.2   │   │ IP: 172.18.0.3        ││        |
|  |  │ Port: 11434      │   │ Port: 8080            ││        |
|  |  └────────┬─────────┘   └──────────┬────────────┘│        |
|  |           │                        │              |        |
|  |           └──────────┬─────────────┘              |        |
|  |                      │                            |        |
|  |    DNS: "ollama"  → 172.18.0.2                    |        |
|  |    DNS: "open-webui" → 172.18.0.3                 |        |
|  +---------------------------------------------------+        |
+---------------------------------------------------------------+
```

**How to test internal connectivity:**

```bash
# Step inside the Open WebUI virtual computer and ping the Ollama virtual computer by name
docker exec -it open-webui ping ollama
# (If ping is installed, you'll see it resolves to ollama's internal IP on the private network.)
```

---

## 8. Volumes: Why Data Survives

Containers (virtual computers) are **ephemeral**. When you shut one down, everything that was created inside it is gone — like powering off a virtual machine that doesn't have a persistent disk. To persist data, you use **volumes**, which are like attaching an external hard drive to the virtual computer.

- **Ollama's virtual computer** stores downloaded models (can be gigabytes) in `/root/.ollama` inside itself
- **Open WebUI's virtual computer** stores user data, chat history, and configuration in `/app/backend/data` inside itself

Without volumes, every time you restart the containers, Ollama would have no models and Open WebUI would have no accounts or history.

In `compose.yaml`:

```yaml
volumes:
  ollama_data:      # Declare the external "hard drive"
  openwebui_data:   # Declare the external "hard drive"

services:
  ollama:
    volumes:
      - ollama_data:/root/.ollama   # Attach it to the virtual computer
  open-webui:
    volumes:
      - openwebui_data:/app/backend/data
```

Even if you run `docker compose down` (shut down all virtual computers), these volumes **remain on your Mac**. Only `docker compose down -v` deletes them.

---

## 9. Full `compose.yaml` for Open WebUI + Ollama

> ⚠️ **Which version do you need?**  
> - **Mac users** → use the single-service Mac version below (Section 9A)  
> - **Windows + NVIDIA GPU / Linux** → use the two-service version (Section 9B)

---

### 9A. Mac `compose.yaml` — Single Service (Ollama runs natively on your Mac)

```yaml
version: '3.8'

services:
  # Only ONE virtual computer — Open WebUI
  # Ollama is NOT here; it runs natively on your Mac via: ollama serve
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"   # Bridge: Mac's port 3000 → container's port 8080
    volumes:
      - openwebui_data:/app/backend/data   # Persist user data
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434   # "host.docker.internal" = your Mac
      - WEBUI_SECRET_KEY=your-secret-key-here   # CHANGE THIS
    restart: unless-stopped

volumes:
  openwebui_data:
```

**Before running this**, make sure Ollama is running natively on your Mac:

```bash
ollama serve         # start Ollama on your Mac
ollama pull llama2   # pull a model (on your Mac, not in Docker)
```

---

### 9B. Windows/Linux `compose.yaml` — Two Services (Full Compose orchestration)

```yaml
version: '3.8'

services:
  # ---------- VIRTUAL COMPUTER 1: OLLAMA ----------
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"   # Bridge: machine's port 11434 → Ollama virtual computer's port 11434
    volumes:
      - ollama_data:/root/.ollama   # Persist models across restarts
    environment:
      - OLLAMA_KEEP_ALIVE=24h
      - OLLAMA_HOST=0.0.0.0
    # For NVIDIA GPU support, uncomment:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]
    restart: unless-stopped

  # ---------- VIRTUAL COMPUTER 2: OPEN WEBUI ----------
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"   # Bridge: machine's port 3000 → Open WebUI virtual computer's port 8080
    volumes:
      - openwebui_data:/app/backend/data   # Persist user data across restarts
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434   # Service name — reaches the Ollama virtual computer
      - WEBUI_SECRET_KEY=your-secret-key-here   # CHANGE THIS
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:
  openwebui_data:
```

---

## 10. What Actually Happens After `docker compose up -d`

1. Reads `compose.yaml` on your Mac
2. Pulls missing images (`ollama/ollama`, `open-webui`) from the internet if not already cached
3. Creates volumes (`ollama_data`, `openwebui_data`) on your Mac if they don't exist
4. Creates a private network (`myproject_default`) — the private LAN for the virtual computers
5. Boots the Ollama virtual computer with its config *(Windows/Linux only)*
6. Boots the Open WebUI virtual computer with its config
7. Starts both (Ollama first due to `depends_on`) *(Windows/Linux only)*
8. Prints "done"

**Verify both virtual computers are running:**

```bash
docker ps
```

**Check logs from each virtual computer:**

```bash
docker logs ollama
docker logs open-webui
```

---

## 11. The Reverse: `docker compose down`

- Shuts down and removes all the virtual computers (containers)
- Removes the private network
- **Does NOT remove volumes** — your data (models, user accounts) stays safe on your Mac

**To remove everything including volumes:**

```bash
docker compose down -v
```

---

## 12. A Comparison: Your FastAPI Project vs. Open WebUI + Ollama

### FastAPI Sentiment Project (Single Virtual Computer)

```
Dockerfile
    │
    ▼
Docker Image (custom build)
    │
    ▼
One Virtual Computer (FastAPI container)
    │
    ▼
Your Mac's browser → http://localhost:8000 → FastAPI API inside the container
```

| Property | Value |
|---|---|
| Virtual computers (containers) | 1 |
| Dockerfile | Yes |
| Networking | Only a port bridge from your Mac → the one container |
| Volumes | Not needed |
| Compose | Not used |

### Open WebUI + Ollama (Two Virtual Computers — Windows/Linux)

```
           compose.yaml (on your Mac/machine)
                │
    ┌───────────┴────────────┐
    ▼                        ▼
Open WebUI                  Ollama
Virtual Computer            Virtual Computer
    │                        │
    │ (volume for data)      │ (volume for models)
    │                        │
    └────────────┬───────────┘
                 │  Private Docker Network
                 │  (virtual computers talk here)
                 │
    ┌────────────┴───────────┐
    │ Port bridges to Mac    │
    ▼                        ▼
Mac:3000 → Container:8080   Mac:11434 → Container:11434 (optional)
    │
    ▼
Your Mac's browser → http://localhost:3000
```

| Property | Value |
|---|---|
| Virtual computers (containers) | 2 |
| Dockerfile | Not needed (official images) |
| Networking | Essential — private LAN between virtual computers |
| Volumes | Required — models and user data must survive restarts |
| Compose | Essential |

---

## 13. I Already Know Dockerfiles. Why Do I Suddenly Need Docker Compose?

You built a FastAPI sentiment classifier with a Dockerfile. It worked because:

- Only one virtual computer
- No communication with other virtual computers
- No persistent state

Now with Open WebUI + Ollama, you have **two separate virtual computers that must cooperate**. You *could* do this manually:

```bash
# Step 1: Create the private LAN manually
docker network create ai-net

# Step 2: Boot the Ollama virtual computer and connect it to the LAN
docker run -d --name ollama --network ai-net -v ollama_data:/root/.ollama ollama/ollama

# Step 3: Boot the Open WebUI virtual computer, connect to LAN, bridge Mac port 3000 → container port 8080
docker run -d --name open-webui --network ai-net \
  -v openwebui_data:/app/backend/data \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  ghcr.io/open-webui/open-webui:main
```

But this is **fragile**. You must remember the network, volumes, and variables every time. Docker Compose packages all this in a single file. It's **declarative** — you describe what you want (two virtual computers, connected, with these settings), and Compose makes it happen.

**Analogy:**

- 🍰 **Dockerfile** = recipe for baking a cake (building one virtual computer's image)
- 🍳 **Docker run** = baking one cake in the oven (booting one virtual computer)
- 🍽️ **Docker Compose** = a full meal plan — multiple dishes prepared together, served at the same time, with one instruction

For your AI stack on Windows/Linux, Compose is not optional — **it's the only sensible way**. On Mac, it's still useful as a clean, repeatable way to manage even a single container.

---

## 14. Step-by-Step: Running the Stack

### On Mac

**1. Start Ollama natively on your Mac:**

```bash
ollama serve
```

**2. Pull a model on your Mac:**

```bash
ollama pull llama2
```

**3. Create a directory and compose file:**

```bash
mkdir ai-stack && cd ai-stack
# Create compose.yaml using the Mac version from Section 9A
```

**4. Boot the Open WebUI virtual computer:**

```bash
docker compose up -d
```

**5. Open your browser** at `http://localhost:3000` (Mac's port 3000 → container's port 8080).  
Create an account — the first user is automatically admin.

**6. Stop:**

```bash
docker compose down
```

---

### On Windows / Linux (with NVIDIA GPU)

**1. Create a directory on your machine:**

```bash
mkdir ai-stack && cd ai-stack
```

**2. Create `compose.yaml`** with the content from [Section 9B](#9b-windowslinux-composeyaml--two-services-full-compose-orchestration).

**3. Boot both virtual computers:**

```bash
docker compose up -d
```

**4. Pull a model into the Ollama virtual computer** (optional, can also do it via Open WebUI):

```bash
docker exec -it ollama ollama pull llama2
```

**5. Open your browser** at `http://localhost:3000`.  
Create an account — the first user is automatically admin.

**6. Stop all virtual computers:**

```bash
docker compose down
```

**7. Stop and wipe all data (volumes too):**

```bash
docker compose down -v
```

---

## 15. Managing Models with Ollama

### On Mac (Ollama runs natively)

```bash
ollama pull llama2     # pull directly on your Mac
ollama pull mistral
ollama list            # list models on your Mac
```

### On Windows/Linux (Ollama runs in a container)

All commands below step inside the Ollama virtual computer and run `ollama` commands there:

```bash
docker exec -it ollama ollama pull llama2
docker exec -it ollama ollama pull mistral
docker exec -it ollama ollama list
```

> On Windows/Linux, models are stored in the `ollama_data` volume, which lives on your machine. Even if the virtual computer is shut down, the models are preserved and will be available when it boots again.

---

## 16. Common Pitfalls and Solutions

| Problem | Solution |
|---|---|
| Open WebUI can't connect to Ollama (Windows/Linux) | Remember: each container is a separate virtual computer. Set `OLLAMA_BASE_URL=http://ollama:11434` (service name, not `localhost`). Check `docker logs ollama`. |
| Open WebUI can't connect to Ollama (Mac) | On Mac, Ollama runs natively. Set `OLLAMA_BASE_URL=http://host.docker.internal:11434`. Make sure `ollama serve` is running on your Mac. |
| Port already in use (e.g., 3000) | Something on your Mac is already using port 3000. Change the Mac-side port: `"3001:8080"`. Access via `http://localhost:3001`. |
| Models disappearing after `down` | Don't use `-v` with `down`. Volumes (stored on your Mac) persist by default. |
| Slow performance on Mac | Use named volumes (not bind mounts). Add `:cached` to bind mounts if used. |
| GPU not working on Linux/Windows | Install NVIDIA Container Toolkit (Linux) or NVIDIA Container Toolkit + WSL2 (Windows) and uncomment the `deploy` section. |
| Permission errors | Set `user: "1000:1000"` in the service definition to match your host user ID. |
| "no such image" error | Check your internet connection. Pull images manually: `docker pull ollama/ollama`. |

---

## 17. Visual Reference: Everything Together

### Mac Architecture — One Container + Native Ollama

```
+-------------------------------------------------------------------+
| YOUR MAC                                                          |
|                                                                   |
|  Ollama running natively here (brew install ollama / ollama serve)|
|  Listening on YOUR MAC's localhost:11434                          |
|                              ▲                                    |
|                              │  host.docker.internal:11434        |
|                              │  (container's way of saying "Mac") |
|  +---------------------------|-------------------------------+    |
|  | Docker                    │                              |    |
|  |  ┌────────────────────────┴──────────────────────────┐  |    |
|  |  │  VIRTUAL COMPUTER: open-webui                      │  |    |
|  |  │  Its own localhost | Its own port 8080             │  |    |
|  |  │  OLLAMA_BASE_URL=http://host.docker.internal:11434 │  |    |
|  |  │  Volume: /app/backend/data (stored on your Mac)    │  |    |
|  |  └────────────────────────────────────────────────────┘  |    |
|  |                 ▲ Port bridge                             |    |
|  |        Mac:3000 → Container:8080                         |    |
|  +-----------------------------------------------------------+    |
|                 ▲                                                 |
|  Browser: http://localhost:3000                                   |
+-------------------------------------------------------------------+
```

### Windows/Linux Architecture — Two Containers, Full Compose

```
+-------------------------------------------------------------------+
| YOUR WINDOWS/LINUX MACHINE                                        |
|                                                                   |
|  Browser: http://localhost:3000  (port on your machine)          |
|  Terminal: curl http://localhost:11434/... (optional, debugging)  |
|            │                                       │             |
|            ▼                                       ▼             |
|  +----------------------------+  +----------------------------+   |
|  | PORT BRIDGE                |  | PORT BRIDGE                |  |
|  | Machine:3000 → Cont.:8080  |  | Machine:11434 → Cont.:11434|  |
|  +----------------------------+  +----------------------------+   |
|            │                                       │             |
|            │   crosses into the private network    │             |
+------------│---------------------------------------│-------------+
             │                                       │
             │    Docker Private Network             │
             │    (Virtual computers' LAN)           │
             ▼                                       ▼
+-----------------------------+  +-----------------------------+
| VIRTUAL COMPUTER: open-webui|  | VIRTUAL COMPUTER: ollama   |
|                             |  |                            |
|  Its own localhost          |  |  Its own localhost         |
|  Listens on its port 8080   |  |  Listens on its port 11434 |
|                             |  |  Has GPU access ✅         |
|  OLLAMA_BASE_URL=           |  |                            |
|  http://ollama:11434 ───────┼──┼──▶ (resolved by Docker DNS)|
|                             |  |                            |
|  Volume: /app/backend/data  |  |  Volume: /root/.ollama     |
|  (stored on your machine)   |  |  (stored on your machine)  |
+-----------------------------+  +-----------------------------+
```

---

## 18. Conclusion

You now have a complete conceptual and practical understanding of why Docker Compose is indispensable for the Open WebUI + Ollama stack — and how the setup differs depending on your machine.

### ✅ Final Mental Checklist — When Reading Any `compose.yaml`

| What to look for | What it means |
|---|---|
| **Services** | How many virtual computers are being defined and booted? |
| **Ports** | Left = port on **your Mac/machine** (what you type in the browser). Right = port on the **virtual computer** (what the app inside listens on). Two separate machines. |
| **Environment** | Configuration injected into the virtual computer at boot time. Use **service names** for container-to-container URLs. Use **`host.docker.internal`** to reach your Mac from inside a container. Never use `localhost` to cross between machines. |
| **Volumes** | External storage attached to the virtual computer. Lives on your Mac. Survives shutdowns. |
| **Network** | The private LAN connecting the virtual computers. They find each other by service name. Your Mac is not on this LAN — only port bridges connect your Mac to it. |

### Quick Decision Guide: Which compose.yaml Do You Need?

```
Are you on a Mac?
  └── YES → Use Section 9A (one service: open-webui only)
             Run Ollama natively: ollama serve
             Set OLLAMA_BASE_URL=http://host.docker.internal:11434

  └── NO (Windows + NVIDIA GPU, or Linux + NVIDIA GPU)
         → Use Section 9B (two services: ollama + open-webui)
           Set OLLAMA_BASE_URL=http://ollama:11434
           Uncomment the GPU deploy block in the ollama service
```

---

*🐳 Bookmark this guide. Whenever ports or variables confuse you, come back to the core idea: your Mac and each container are separate computers, each with their own `localhost` and their own ports. Everything else follows from that.*

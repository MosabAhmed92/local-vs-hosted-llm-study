# LLM Benchmarking Suite: Local vs. Hosted Performance

**Comparing local (Ollama) and hosted (Anthropic) LLM inference performance**

---

## 1. What it does

This project runs Mistral 7B locally via Ollama on an Apple M3 Max, benchmarking it against Anthropic's Claude Haiku and Sonnet using a decoupled Python benchmarking engine. It measures client-side latency (`client_waiting`), raw generation throughput (`tok/s`), and KV cache scaling across short, medium, and long prompts—outputting timestamped CSVs for analysis.

---

## 2. What you learned

- Long contexts cripple local inference because decode is memory‑bandwidth‑bound; the same KV cache growth that slows local models actually saturates hosted H100s, inverting the scaling curve.
- A model can be faster per token (Sonnet at 75 tok/s) but slower overall (12s).


---

## 3. How to run it

**Prerequisites:**
- Ollama 
- Conda 

**Commands (order matters):**

```bash
# 1. Clone and enter the repo
git clone <your-repo-url>
cd llm-benchmarking

# 2. Set up Python environment
conda create -n bench python=3.11 -y
conda activate bench
pip install -r requirements.txt

# 3. Pull the local model
ollama pull mistral:7b-instruct-q5_K_S

# 4.  Start Open WebUI for manual testing
docker compose up -d

# 5. Set your Anthropic API key in a .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "CLAUDE_URL=https://api.anthropic.com/v1/messages" >> .env

# 6. Run the full benchmark (Ollama + Haiku + Sonnet)
python benchmark.py
```

**Output:** A timestamped CSV

---

## 4. Key findings from the benchmark

**pushed CSV file**

- **Local (Ollama):** `tok/s` *drops* as prompts get longer (46 → 43 → 35) – memory saturation.
- **Hosted (Haiku):** `tok/s` *increases* on longer prompts (45 → 65) – High memory bandwidth due to the highly sophisticated hardware setup and the performance.

---

## 5. What's not here that would be needed for production

- **Concurrency & load balancing**
- **Authentication & observability**: No SSO, no audit logs, no Prometheus metrics. Real deployments require structured logging, tracing, and strict role‑based access.
- **Hardware**: This runs on a single laptop. Production would demand dedicated GPU servers (or cloud instances) with multi‑GPU tensor parallelism.

---

## 6. File structure

```text
.
├── benchmark.py            # Master orchestration: runs all three providers
├── main.py                 # Legacy: local Ollama only
├── main_hosted.py          # Legacy: Anthropic API connectivity test
├── aggreg.py               # Loads a saved CSV and re‑aggregates summaries
├── prompts.json            # Prompt suite (short / medium / long)
├── requirements.txt        # Python deps (requests, pandas, python-dotenv, anthropic)
├── docker-compose.yml      # Open WebUI container definition (reference)
├── .gitignore              # Excludes .env, raw CSVs, cache, etc.
└── summarized_df.csv       # The final aggregated result (ready for analysis)
```

---

## 7. References

- [Anthropic API Docs](https://docs.anthropic.com/en/api/getting-started)
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [llama.cpp / GGUF format](https://github.com/ggerganov/llama.cpp)

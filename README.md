# ⚡ Enterprise AI Gateway & Token Observability Proxy

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

An enterprise-grade, high-throughput AI Gateway designed to tackle three acute pain points in enterprise LLM adoption:
1. **AI Cost Inflation** — Mitigated through deterministic SHA-256 prompt hash-caching via Redis.
2. **High Latency** — Delivering sub-10ms responses for cached prompts instead of waiting 2,000ms+ for upstream providers.
3. **PII Data Leaks** — Zero-trust regex token interceptor that automatically redacts Emails, Credit Cards (with Luhn validation), and Phone Numbers *before* prompts transit outside your network.

---

## 🏛️ System Architecture

```text
                      +-----------------------------+
                      |   Client Application / SDK   |
                      +--------------+--------------+
                                     |
                                     | 1. POST /v1/chat/completions
                                     v
                      +-----------------------------+
                      |   FastAPI Gateway Router    |
                      +--------------+--------------+
                                     |
                                     | 2. PII Interceptor (Regex engine)
                                     v
                      +-----------------------------+
                      |  PII Masking & Sanitization |  ---> [Logs redaction incident]
                      +--------------+--------------+
                                     |
                                     | 3. Hash Prompt (SHA-256)
                                     v
                      +-----------------------------+
             +------> |    Redis Cache Layer        |
             |        +--------------+--------------+
             |                       |
   [HIT: sub-10ms]                   | [MISS: proceed]
   Returns cached answer             v
   Increments Tokens Saved    +-----------------------------+
             |                | Upstream LLM (OpenAI/Gemini)|
             |                +--------------+--------------+
             |                               |
             |                               | 4. Response received
             |                               v
             |                +-----------------------------+
             +----------------+  Token & Cost Estimator     |
                              +--------------+--------------+
                                             |
                                             | 5. Async DB write
                                             v
                              +-----------------------------+
                              |   PostgreSQL (Audit Logs)   |
                              +-----------------------------+
                                             ^
                                             | Reads metrics
                              +--------------+--------------+
                              |   Next.js 14 Dashboard      |
                              +-----------------------------+
```

---

## 🚀 Key Features

### 1. Transparent `/v1/chat/completions` Proxy
* Zero disruption to existing codebases. Compatible with OpenAI SDKs, LangChain, LlamaIndex, and standard HTTP clients.
* Simply update `base_url` to point to `http://localhost:8000/v1`.

### 2. Semantic Prompt Hash-Caching (Redis)
* Prompts are normalized and hashed using **SHA-256**.
* **Cache HIT**: Bypasses external providers entirely, returning stored answers in **< 10ms** at **$0.00** cost.
* **Cache MISS**: Transparently forwards request to upstream LLM, writes response to Redis with configurable TTL (default 24h), and logs metrics.

### 3. Automated PII Redaction Pipeline
* Scans incoming message history for sensitive identifiers:
  * **Credit Cards**: Full pattern detection with **Luhn Checksum (Mod 10)** validation to eliminate false positives on serial numbers.
  * **Email Addresses**: RFC 5322 compliant regex masking.
  * **Phone Numbers**: Captures E.164, North American, and international phone formats.
* Replaces matches with `[REDACTED_*]` tokens before the prompt is sent to external cloud APIs.

### 4. Token & Latency Observability Engine
* Real-time tracking of:
  * **Latency (ms)**: End-to-end request duration.
  * **Cache State**: `HIT`, `MISS`, or `BYPASS`.
  * **Tokens & Costs**: Detailed breakdown of prompt, completion, and total tokens, with exact USD costs calculated from upstream pricing catalogs.
* Metrics streamed to an executive Next.js 14 dashboard.

---

## 📁 Repository Structure

```text
ai-gateway-proxy/
├── docker-compose.yml              # PostgreSQL 16 + Redis 7 + Backend + Frontend
├── .env.example                    # Global environment variables
├── README.md                       # Documentation & Quickstart
│
├── backend/                        # FastAPI High-Throughput Proxy
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                 # Lifespan events, CORS, router mounting
│   │   ├── config.py               # Pydantic Settings & environment manager
│   │   ├── core/
│   │   │   ├── pii_sanitizer.py    # Regex & Luhn PII scrubber
│   │   │   ├── cache_manager.py    # Redis SHA-256 hash manager
│   │   │   ├── cost_calculator.py  # Model pricing & cost calculator
│   │   │   └── database.py         # Async SQLAlchemy 2.0 engine
│   │   ├── models/
│   │   │   ├── api_log.py          # Detailed audit log table
│   │   │   └── cost_metric.py      # Aggregated daily rollup table
│   │   ├── schemas/
│   │   │   ├── openai_schema.py    # OpenAI-compatible request/response schemas
│   │   │   └── metrics_schema.py   # Analytics schemas for Next.js
│   │   └── api/
│   │       ├── proxy.py            # /v1/chat/completions endpoint
│   │       └── metrics.py          # /v1/analytics/* endpoints
│   └── tests/
│       ├── run_tests.py            # Zero-dependency test runner
│       ├── test_pii.py             # PII & Luhn unit tests
│       └── test_cache.py           # Cache manager unit tests
│
└── frontend/                       # Next.js 14 (App Router) Dashboard
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── app/
        │   ├── layout.tsx          # Dark modern layout & sidebar
        │   ├── page.tsx            # Live KPI cards & latency distribution
        │   ├── logs/page.tsx       # Searchable & filterable API logs
        │   └── security/page.tsx   # PII audit & interactive sandbox
        ├── components/             # Reusable UI widgets
        └── lib/                    # API client & TypeScript types
```

---

## 🛠️ Quickstart

### Option A: 1-Click Startup with Docker Compose (Recommended for Production)

```bash
# 1. Clone or navigate to the repository
cd d:/project

# 2. Configure your environment
cp .env.example .env

# 3. Spin up PostgreSQL, Redis, FastAPI Backend, and Next.js Frontend
docker compose up -d
```
* **Frontend Observability Dashboard**: [http://localhost:3000](http://localhost:3000)
* **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Local Python Development (Zero External Dependencies Required)

The gateway is architected with graceful in-memory fallbacks: if PostgreSQL or Redis are not running, it automatically operates using SQLite and an in-memory TTL cache!

```bash
# 1. Navigate to the backend directory
cd d:/project/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the automated verification suite
python tests/run_tests.py

# 4. Launch the Gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Testing the Proxy

### 1. Test via cURL (Notice PII Redaction & Cache Hit)

**First Call (Cache MISS - Scans PII & Caches Prompt):**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "Send refund confirmation to client@example.com for card 4532 0151 1283 0366."
      }
    ]
  }'
```
*Notice headers in response:*
* `X-Cache: MISS`
* `X-PII-Redacted: True`

**Second Call with Identical Prompt (Cache HIT - Sub-10ms):**
```bash
curl -i -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "Send refund confirmation to client@example.com for card 4532 0151 1283 0366."
      }
    ]
  }'
```
*Notice headers in response:*
* `X-Cache: HIT`
* `X-Response-Time-Ms: 4.82` (Sub-10ms response!)
* `X-Cost-Saved-USD: 0.000450`

---

### 2. Using with the Official OpenAI Python SDK

```python
from openai import OpenAI

# Simply point base_url to your local AI Gateway
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-optional-gateway-key"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Explain vector databases in one paragraph."}
    ]
)

print(response.choices[0].message.content)
```

---

## 📊 Database Schema (PostgreSQL / SQLite)

### `api_logs` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | UUID Primary Key |
| `timestamp` | `TIMESTAMP WITH TZ` | Request time (indexed) |
| `model` | `VARCHAR(64)` | Requested LLM model |
| `prompt_hash` | `VARCHAR(64)` | Deterministic SHA-256 prompt digest |
| `prompt_tokens` | `INTEGER` | Input token count |
| `completion_tokens` | `INTEGER` | Output token count |
| `total_tokens` | `INTEGER` | Total token volume |
| `latency_ms` | `FLOAT` | Duration in milliseconds |
| `cost_usd` | `FLOAT` | Calculated financial cost |
| `cost_saved_usd` | `FLOAT` | Financial savings on cache HIT |
| `cache_status` | `VARCHAR(16)` | `HIT`, `MISS`, or `BYPASS` |
| `pii_detected` | `BOOLEAN` | Whether sensitive data was intercepted |
| `pii_types_found` | `JSON` | Categories (`["EMAIL", "CREDIT_CARD"]`) |
| `status_code` | `INTEGER` | HTTP Status code (200, 400, 502) |

---

## 🔒 Security & Compliance
* **PCI-DSS Compliance**: Credit cards validated with the Luhn formula and redacted before cloud transit.
* **GDPR & CCPA**: User emails and phone numbers scrubbed from prompt text to prevent personal data leaking into external AI training pipelines.
* **Sub-10ms Hash Retrieval**: SHA-256 prompt fingerprints ensure complete data isolation across varying models and temperatures.

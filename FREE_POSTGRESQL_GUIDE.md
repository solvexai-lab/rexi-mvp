# Free PostgreSQL Hosting for REXI — Honest Comparison

## Quick Pick (No Thinking Required)

| Stage | Provider | Why |
|-------|----------|-----|
| **Development / Testing** | **Neon** | 500MB, 191 compute-hours/mo, instant branches, no credit card |
| **Production MVP (0-6 months)** | **Aiven** | 5GB storage, 1GB RAM, 1 CPU, no time limit |
| **Full-stack backend (auth + storage)** | **Supabase** | 500MB DB + auth + file storage + realtime |
| **Indian data residency** | **AWS RDS Free Tier** | 12 months free, Mumbai region |

---

## 1. NEON — Best for Development & Branching

**Free Tier:**
- 500 MB storage per project
- 191 compute-hours per month
- 10 database branches (like git branches for schema/data)
- Scale-to-zero (stops billing when idle)
- No credit card required

**Pros:**
- Instant provisioning (10 seconds)
- Database branching = test schema changes without copying data
- Serverless = costs $0 when idle
- pgvector extension supported (for Phase 2 vector search)
- Apache-2.0 open source

**Cons:**
- 500MB limits you to ~500 contracts with full text
- Cold start latency (~1s) after idle
- Compute hours can run out if always-on

**Connection string:**
```bash
postgresql+asyncpg://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb
```

**Best for:** REXI development, testing migrations, preview environments per PR.

🔗 https://neon.tech

---

## 2. AIVEN — Best Free Production Tier

**Free Tier:**
- 5 GB storage
- 1 GB RAM
- 1 CPU
- 20 max connections
- Backups included
- Bangalore region available

**Pros:**
- Largest free storage (5GB = ~5,000 contracts)
- No expiration, no "pause after inactivity"
- Terraform / CLI automation
- Monitoring + logs included
- EU/India data residency options

**Cons:**
- No connection pooling on free tier
- DigitalOcean-only on free tier
- Limited to 1 service

**Connection string:**
```bash
postgresql+asyncpg://user:pass@rexi-db.aivencloud.com:12648/defaultdb?ssl=require
```

**Best for:** REXI production MVP — 5GB is enough for months of real usage.

🔗 https://aiven.io

---

## 3. SUPABASE — Best Full-Stack Bundle

**Free Tier:**
- 500 MB PostgreSQL
- 1 GB file storage (for PDFs!)
- 50,000 auth users/month
- 5 GB bandwidth
- Realtime subscriptions
- Edge functions

**Pros:**
- Built-in auth (could replace fastapi-users)
- File storage = no MinIO needed
- Realtime = live notifications
- Row Level Security (RLS) = built-in multi-tenancy
- Instant REST API from tables

**Cons:**
- 500MB DB is tight for legal docs
- Project pauses after 7 days inactivity (free tier)
- $25/mo to remove pausing
- Lock-in to Supabase ecosystem

**Connection string:**
```bash
postgresql+asyncpg://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

**Best for:** If you want to drop MinIO, replace auth, and get file storage + realtime in one platform.

🔗 https://supabase.com

---

## 4. RENDER — Simple but Time-Limited

**Free Tier:**
- 1 GB storage
- 256 MB RAM
- 0.1 CPU
- All regions

**Pros:**
- 1GB is decent for testing
- Easy integration with Render app hosting

**Cons:**
- **30-day limit** (database deleted after 30 days!)
- No backups
- Single instance only

**Verdict:** Skip for REXI. 30-day deletion is a trap.

---

## 5. RAILWAY — Usage-Based, Developer-Friendly

**Free Tier:**
- $5/month credit (usage-based)
- ~1GB storage + shared compute
- No hard limits, just credits

**Pros:**
- Deploy from GitHub instantly
- Usage-based = pay only for what you use
- Good for variable workloads

**Cons:**
- Credit runs out → database stops
- Less predictable than fixed free tiers

**Best for:** If you also host the backend on Railway.

🔗 https://railway.app

---

## 6. Self-Hosted on Cheap VPS (India)

If you want **full control** and **Indian data residency** (DPDP compliance):

| Provider | Location | Price | Specs |
|----------|----------|-------|-------|
| DigitalOcean | Bangalore | $6/mo | 1GB RAM, 25GB SSD |
| Hetzner | Nuremberg | €4.51/mo | 2GB RAM, 20GB SSD |
| AWS Lightsail | Mumbai | $5/mo | 1GB RAM, 40GB SSD |
| Contabo | Germany | €4.99/mo | 4GB RAM, 100GB SSD |

**Pros:**
- Unlimited storage within VM limit
- Full pgvector, no restrictions
- No vendor lock-in
- DPDP data residency compliance

**Cons:**
- You manage backups, updates, security
- No high availability

**Best for:** Production when you're ready to pay $5-6/month and need DPDP compliance.

---

## Recommended REXI Path

### Phase 1 (Now — Development)
```bash
# Use Neon — zero friction, instant, branching for testing
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb
```

### Phase 2 (Private Beta — 3 months)
```bash
# Switch to Aiven for 5GB + no pausing + Bangalore region
DATABASE_URL=postgresql+asyncpg://user:pass@rexi-db.aivencloud.com:12648/defaultdb?ssl=require
```

### Phase 3 (Production — 6+ months)
```bash
# Option A: AWS RDS Mumbai (if you have AWS credits)
# Option B: Self-hosted on DigitalOcean Bangalore ($6/mo)
# Option C: Supabase Pro ($25/mo) if you want auth + storage bundle
```

---

## One-Command Neon Setup

```bash
# 1. Sign up (no credit card)
# 2. Create project → Get connection string
# 3. Update .env
echo "DATABASE_URL=postgresql+asyncpg://YOUR_NEON_URL" >> rexi-mvp/backend/.env

# 4. REXI auto-creates tables on startup (init_db in lifespan)
cd rexi-mvp/backend && uvicorn app.main:app --reload
```

---

## pgvector Note (Phase 2 Prep)

All recommended providers support **pgvector**:
- **Neon:** `CREATE EXTENSION vector;` — works on all plans
- **Aiven:** pgvector available, may need support ticket on free tier
- **Supabase:** pgvector enabled by default
- **Self-hosted:** `apt install postgresql-16-pgvector`

---

*Last updated: 2026-05-24*

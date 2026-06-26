# Autonomous Research & Report Generation Agent

A production-grade multi-agent AI system deployed on AWS. You give it a research topic, it autonomously searches, summarizes, writes a full report, checks it for safety, and returns it — with caching, long-term memory, red teaming, and multiple output formats.

---

## What This Project Covers

- **FastAPI** — fully async REST API
- **LangGraph** — multi-agent pipeline (search → summarize → report → verify)
- **TensorZero** — LLM gateway routing GPT-4o and Groq Llama-3
- **AWS Bedrock Guardrails** — content safety on both input and output
- **Redis (ElastiCache)** — semantic cache + job queue (Streams) + session memory
- **PostgreSQL + pgvector (RDS)** — long-term memory, report versioning, semantic search
- **PyRIT** — automated red teaming with jailbreak, XPIA, Crescendo, Skeleton Key attacks
- **LangSmith** — full observability (traces every agent run) + LLM-as-judge evaluation
- **Terraform** — all AWS infrastructure as code in one file
- **GitHub Actions** — CI/CD, no Docker needed locally

---


## Prerequisites

Install these on your machine before starting:

| Tool | Download | Verify |
|---|---|---|
| AWS CLI | https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html | `aws --version` |
| Terraform | https://developer.hashicorp.com/terraform/install | `terraform --version` |
| Git | https://git-scm.com/downloads | `git --version` |
| GitHub account | https://github.com | — |

**Docker is NOT required on your machine.** GitHub Actions builds and pushes all Docker images automatically on every push to main.

---

## Project File Structure

```
PROJECT/
├── app/
│   ├── main.py           FastAPI app — endpoints, lifespan, background worker
│   ├── agents.py         LangGraph 4-node graph: search, summarize, report, verify
│   ├── cache.py          Redis semantic cache (cosine similarity with embeddings)
│   ├── guardrails.py     Bedrock Guardrails — validates input AND output
│   ├── memory.py         Redis session memory + pgvector long-term memory + db_migrate
│   ├── queue.py          Redis Streams job queue — push, consume, ack
│   ├── multimodal.py     GPT-4o vision — reads images and PDFs from URLs
│   ├── output.py         PDF export, structured JSON, report diff
│   ├── eval.py           LangSmith evaluators (relevance, completeness, hallucination, quality)
│   ├── config.py         Loads all secrets from AWS Secrets Manager, enables LangSmith tracing
│   └── Dockerfile
├── pyrit_dashboard/
│   ├── main.py           PyRIT red team dashboard (FastAPI + auto-refresh HTML)
│   ├── requirements.txt
│   └── Dockerfile
├── tensorzero/
│   └── tensorzero.toml   LLM routing — GPT-4o primary, Groq fallback
├── terraform/
│   └── main.tf           All AWS infrastructure in one file
├── .github/
│   └── workflows/
│       └── deploy.yml    CI/CD — build, push ECR, deploy ECS
├── bootstrap.bat         One-time setup script (Windows CMD)
├── bootstrap.sh          One-time setup script (Mac/Linux or Git Bash)
├── db_init.sql           Database schema reference (runs automatically on app start)
├── requirements.txt      Python dependencies for the main app
├── index.html            Frontend — single HTML file, vanilla JS, no frameworks
├── .gitattributes        Enforces correct line endings per file type
└── README.md             This file
```

---

## Step-by-Step Setup

### Step 1 — Configure AWS CLI

```cmd
aws configure
```

Enter when prompted:
- **AWS Access Key ID** — AWS Console → top-right your name → Security Credentials → Create access key
- **AWS Secret Access Key** — shown once at creation time, copy it immediately
- **Default region** — `us-east-1`
- **Default output format** — `json`

---

### Step 2 — Run the Bootstrap Script (one time only)

Terraform needs an S3 bucket to store state and a DynamoDB table for locking. Terraform cannot create its own backend, so we use AWS CLI for this one-time step.

**Windows CMD:**
```cmd
bootstrap.bat
```

**Mac/Linux or Git Bash:**
```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

You will see:
```
S3 bucket  : research-agent-tfstate  (versioned, encrypted, private)
DynamoDB   : research-agent-tf-locks (state locking)
Bootstrap complete.
```

The Bedrock Guardrail, Redis, RDS, and all other AWS resources are created by Terraform in the next step — no manual console clicks needed.

---

### Step 3 — Create a GitHub Repository and Add Secrets

1. Go to https://github.com and create a new repository named `research-agent`

2. Push this project:
   ```cmd
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/research-agent.git
   git push -u origin main
   ```

3. Add these two secrets to GitHub (repo → Settings → Secrets and variables → Actions → New repository secret):

   | Secret Name | Value |
   |---|---|
   | `AWS_ACCESS_KEY_ID` | Your AWS access key ID |
   | `AWS_SECRET_ACCESS_KEY` | Your AWS secret access key |

---

### Step 4 — Deploy All AWS Infrastructure with Terraform

```cmd
cd terraform
terraform init
terraform plan -var="app_image=placeholder" -var="pyrit_image=placeholder"
terraform apply -var="app_image=placeholder" -var="pyrit_image=placeholder"
```

Type `yes` when asked to confirm. This takes 5–10 minutes and creates everything: VPC, subnets, ECS cluster, two services, ALB, ElastiCache Redis, RDS PostgreSQL, Bedrock Guardrail, Secrets Manager secret, ECR repositories, IAM roles, VPC endpoints, EventBridge rule.

After it finishes, copy the output values — you will need them:
```
alb_dns       = "research-agent-alb-123456.us-east-1.elb.amazonaws.com"
app_ecr_url   = "123456789.dkr.ecr.us-east-1.amazonaws.com/research-agent-app"
pyrit_ecr_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/research-agent-pyrit"
redis_endpoint = "research-agent-redis.abc123.cfg.use1.cache.amazonaws.com"
```

---

### Step 5 — Get a LangSmith API Key (Free)

LangSmith provides full observability into every agent run and stores evaluation results. Adding the API key is the only manual step — everything else (traces, evaluations, dataset, project) is created automatically when the app first runs.

1. Go to https://smith.langchain.com and sign up — it is free
2. Click your profile (top left) → **API Keys** → **Create API Key**
3. Copy the key — it starts with `ls__`

You will add this in the next step. After that, no further LangSmith setup is needed.

---

### Step 6 — Add Your API Keys to Secrets Manager

Terraform already filled in Redis URL, database URL, Guardrail ID, and region. You need to add three keys.

Go to: AWS Console → Secrets Manager → `research-agent/config` → Retrieve secret value → Edit

Replace the three `REPLACE_ME` values:
```json
{
  "OPENAI_API_KEY":   "sk-...",
  "GROQ_API_KEY":     "gsk_...",
  "LANGSMITH_API_KEY": "ls__..."
}
```

- `OPENAI_API_KEY` — https://platform.openai.com/api-keys
- `GROQ_API_KEY` — https://console.groq.com/keys
- `LANGSMITH_API_KEY` — https://smith.langchain.com → API Keys

Leave all other fields as Terraform set them.

---

### Step 7 — Push to Main to Trigger the First Deployment

The first `git push` in Step 3 already triggered GitHub Actions. Go check it now:

GitHub repo → Actions tab → you should see a workflow running or completed.

If it is still running, wait for it to turn green (5–10 minutes). This is what it does:
1. Builds both Docker images on a Ubuntu runner
2. Pushes them to ECR (tagged with the commit SHA)
3. Reads the ECS task definition, swaps in the real image URL
4. Registers a new task definition revision
5. Updates both ECS services to use it
6. Waits for the app service to become stable

Once green, your app is live.

---


## Application URLs

- **Main App:** http://research-agent-alb-521507763.us-east-1.elb.amazonaws.com/
- **PyRIT Dashboard:** http://research-agent-alb-521507763.us-east-1.elb.amazonaws.com:8001/
- **Redis Stats:** http://research-agent-alb-521507763.us-east-1.elb.amazonaws.com/stats
- **LangSmith Traces:** https://smith.langchain.com *(Project: `research-agent`)*
---

## Destroy Everything

```yaml
terraform destroy -var="app_image=placeholder" -var="pyrit_image=placeholder" -auto-approve

```
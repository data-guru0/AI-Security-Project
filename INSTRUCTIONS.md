Build a production-grade Autonomous Research & Report Generation Agent. Deploy everything on AWS. No local docker-compose, no local setup instructions.

## Tech Stack
- Backend: FastAPI (fully async)
- AI Agents: LangGraph (async)
- LLM Gateway: TensorZero (GPT-4o primary via OpenAI, Groq llama-3 fallback)
- Safety: AWS Bedrock Guardrails (check user input + final report output)
- Redis: AWS ElastiCache Redis — semantic cache + Redis Streams job queue + short-term session memory (TTL 30min)
- Red Teaming: PyRIT with its own simple FastAPI dashboard (separate ECS service)
- UI: Single index.html, vanilla JS, fetch() to FastAPI — no frameworks
- Infrastructure: Terraform (AWS ECS Fargate, ECR, ALB, ElastiCache, Secrets Manager, IAM)
- CI/CD: GitHub Actions → build Docker → push ECR → deploy ECS
- Make this multi agent project
- For short term memory we have redis but for long term memory use pgvector on RDS. Every generated report gets embedded and stored. Next time someone researches a similar topic, agent first checks if a recent report already exists before hitting the web. Saves cost, adds intelligence.
- Multiple output formats

Right now output is plain text report. Add:

PDF export
Structured JSON for downstream systems

Report versioning

If you research the same topic twice, system shows you a diff — "what changed since last week?" Very useful for market research, competitive analysis.

- Multi-modal research

Agent can also process images, charts, PDFs found on the web — not just text. Uses GPT-4o vision capability. Research on a company could include reading their annual report PDF directly.
Adversarial robustness via PyRIT expansion

Right now PyRIT runs basic jailbreak + XPIA. Add:

Crescendo attack (multi-turn manipulation)
Skeleton key attacks
Custom attack plugins for your specific domain
Automated weekly red team runs via EventBridge, results stored and trended over time

Fine-tuned routing in TensorZero

After collecting 500+ research jobs, use TensorZero's optimizer to learn — "for finance topics, GPT-4o performs better; for coding topics, Groq is faster and cheaper". True data-driven model routing.
## Rules
1. All FastAPI endpoints async def, all LangGraph nodes async
2. Redis semantic cache: embed query with sentence-transformers, cosine similarity check before every LLM call
3. Redis Streams: POST /research pushes job to stream, background worker consumes it, GET /result/{job_id} polls for result
4. Redis session memory: last 5 messages per session_id, 30min TTL
Also i need that RedisInsight dahboard where u will tell me how i can see all queries and all in the readme.md
5. TensorZero: all LLM calls go through TZ client only — never call OpenAI or Groq directly. Two functions in tensorzero.toml: research_summarize (GPT-4o) and report_write (GPT-4o, Groq fallback)
6. Bedrock Guardrails: validate raw user input before agent starts, validate final report before returning. Use boto3 via asyncio.to_thread
7. PyRIT dashboard: runs XPIA + jailbreak attacks against /research endpoint, shows results in auto-refreshing HTML table with pass/fail and risk score
8. Terraform: ECS Fargate 0.25 vCPU / 0.5GB memory (prototype scale), one cluster, two services (app + pyrit), ElastiCache t3.micro single node, one ALB, no NAT gateway — use VPC endpoints. Store all secrets in AWS Secrets Manager
9. GitHub Actions: on push to main — docker build, push to ECR, force new ECS deployment for both services
10. No helper files unless used in 3+ places. Every file under 200 lines. No over-engineering
11. Terraform main.tf puts everything in one file — ECS cluster, task definitions, services, ALB, ElastiCache, IAM roles, security groups, Secrets Manager entries
12. Don't include emojis and comments in the code only in things where i have told u to add commnts there only add rest dont add any comment or emijis in the whole code
## ENV vars (loaded from AWS Secrets Manager via config.py)
OPENAI_API_KEY, GROQ_API_KEY, AWS_REGION, BEDROCK_GUARDRAIL_ID, BEDROCK_GUARDRAIL_VERSION, REDIS_URL, TENSORZERO_URL

Also in readme.md mention from ehre i will get these varibles environemnt

## README.md must include
- Prerequisites (AWS CLI, Terraform, GitHub Actions secrets)
- Step by step: Everything from start to end even a  beginner can undertand and do the project evryhting in deatiled that first you have to do this then this like that 
- How to run PyRIT red teaming from the dashboard URL
- How to explored Redis Dahbaord 
- All env vars table with descriptions


Start from root directory. Create every file. Do not ask clarifying questions.

If anything else is needed and all add it but dont make a complex folder structure keep it minimal and easy so i can explain it to user file by file i dont have to inside many subfolders to explain a topic 

I told u to make a production grade project but make sure you use less resources thata re suffcient to teach student and prototyping because we are just imitating the production environment
Just mark that place with commebnts that in production we use this much with commenbts so i can tell students

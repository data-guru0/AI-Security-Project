import os
import boto3
import json
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_secret() -> dict:
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId="research-agent/config")
    return json.loads(response["SecretString"])


class Config:
    def __init__(self):
        data = _load_secret()
        self.openai_api_key: str = data["OPENAI_API_KEY"]
        self.groq_api_key: str = data["GROQ_API_KEY"]
        self.aws_region: str = data.get("AWS_REGION", "us-east-1")
        self.bedrock_guardrail_id: str = data["BEDROCK_GUARDRAIL_ID"]
        self.bedrock_guardrail_version: str = data["BEDROCK_GUARDRAIL_VERSION"]
        self.redis_url: str = data["REDIS_URL"]
        self.tensorzero_url: str = data["TENSORZERO_URL"]
        self.database_url: str = data.get("DATABASE_URL", "")
        self.langsmith_api_key: str = data.get("LANGSMITH_API_KEY", "")
        self.langchain_project: str = data.get("LANGCHAIN_PROJECT", "research-agent")

        if self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

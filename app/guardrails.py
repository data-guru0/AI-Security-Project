import asyncio
import boto3
from app.config import Config


def _apply_guardrail_sync(config: Config, text: str, source: str) -> dict:
    client = boto3.client("bedrock-runtime", region_name=config.aws_region)
    return client.apply_guardrail(
        guardrailIdentifier=config.bedrock_guardrail_id,
        guardrailVersion=config.bedrock_guardrail_version,
        source=source,
        content=[{"text": {"text": text}}],
    )


async def validate_input(config: Config, text: str) -> tuple[bool, str]:
    response = await asyncio.to_thread(_apply_guardrail_sync, config, text, "INPUT")
    if response.get("action") == "GUARDRAIL_INTERVENED":
        return False, "Input blocked by safety guardrail."
    return True, ""


async def validate_output(config: Config, text: str) -> tuple[bool, str]:
    response = await asyncio.to_thread(_apply_guardrail_sync, config, text, "OUTPUT")
    if response.get("action") == "GUARDRAIL_INTERVENED":
        return False, "Output blocked by safety guardrail."
    return True, ""

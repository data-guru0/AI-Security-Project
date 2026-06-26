import base64
import httpx
from app.config import Config


async def fetch_url_content(url: str) -> tuple[str, bytes]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        content_type = response.headers.get("content-type", "")
        if "pdf" in content_type or url.lower().endswith(".pdf"):
            return "pdf", response.content
        if any(t in content_type for t in ["image/jpeg", "image/png", "image/gif", "image/webp"]):
            return "image", response.content
        return "text", response.content


async def _tz_vision_call(config: Config, messages: list) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{config.tensorzero_url}/v1/inference",
            json={"function_name": "research_summarize", "input": {"messages": messages}},
        )
        data = response.json()
        return data["content"][0]["text"]


async def analyze_image(config: Config, image_bytes: bytes, prompt: str) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    return await _tz_vision_call(config, [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ],
    }])


async def analyze_pdf(config: Config, pdf_bytes: bytes, prompt: str) -> str:
    b64_preview = base64.b64encode(pdf_bytes[:8192]).decode()
    return await _tz_vision_call(config, [{
        "role": "user",
        "content": [
            {"type": "text", "text": f"PDF base64 preview (first 8KB): {b64_preview}"},
            {"type": "text", "text": prompt},
        ],
    }])


async def process_url(config: Config, url: str, prompt: str) -> str:
    content_type, raw = await fetch_url_content(url)
    if content_type == "image":
        return await analyze_image(config, raw, prompt)
    if content_type == "pdf":
        return await analyze_pdf(config, raw, prompt)
    return raw.decode(errors="replace")[:4000]

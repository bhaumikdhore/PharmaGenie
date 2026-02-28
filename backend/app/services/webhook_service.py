import httpx
from fastapi import HTTPException


async def trigger_n8n_webhook(webhook_url: str, payload: dict):
    normalized_url = (webhook_url or "").strip().rstrip("/")
    if not normalized_url:
        raise HTTPException(status_code=500, detail="N8N_ORDER_WEBHOOK is not set")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            print(f"[n8n] webhook_url={normalized_url}")
            print(f"[n8n] payload={payload}")
            response = await client.post(normalized_url, json=payload)
            print(f"[n8n] response.status_code={response.status_code}")
            print(f"[n8n] response.text={response.text}")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"n8n webhook failed with status {response.status_code}: {response.text}",
                )

            return {"ok": True, "status_code": response.status_code, "response": response.text}
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=f"n8n webhook exception: {exc}") from exc

import asyncio
import json
from datetime import datetime
from pathlib import Path
from time import time
from typing import Any, Self

import httpx
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from pydantic import BaseModel, Field


class Config(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=9000, ge=1, le=65535)
    access_log: bool = Field(default=False)
    webhook_url: str = Field(default="http://127.0.0.1:8000/webhook")
    webhook_secret_token: str | None = Field(default=None)
    sleep: int = Field(default=0, ge=0)
    skip_commands: bool = Field(default=True)
    max_messages: int = Field(default=0, ge=0)
    chat_id_to_chat_id: dict[int, int] = Field(default=dict())
    chat_id_to_user_id: dict[int, int] = Field(default=dict())
    chat_id_to_username: dict[int, str] = Field(default=dict())
    chat_id_to_first_name: dict[int, str] = Field(default=dict())
    chat_id_to_last_name: dict[int, str] = Field(default=dict())

    @classmethod
    def load(cls: type[Self]) -> Self:
        path = Path.cwd() / "config.yml"

        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")

        obj = cls()

        with path.open("r", encoding="utf-8") as f:
            obj = yaml.safe_load(f) or {}

        if isinstance(obj, dict):
            obj = cls.model_validate(obj)

        return obj


app = FastAPI()
config = Config.load()


def main():
    app.state.message_counter = 0

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        access_log=config.access_log,
    )


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{ts}] {msg}"

    print(msg, flush=True)


def now_s() -> int:
    return int(time())


def dumps(obj: dict[str, Any]) -> str:
    return json.dumps(obj)


async def extract_payload(req: Request) -> dict[str, Any]:
    payload: dict[str, Any]
    ct = req.headers.get("content-type", "")

    if "application/json" in ct:
        payload = await req.json()
    else:
        form = await req.form()
        payload = dict(form)

    return payload


async def save_document(req: Request) -> Path:
    form = await req.form()
    document = form.get("document")

    if document is None:
        raise ValueError("Missing document upload")

    if not isinstance(document, UploadFile):
        raise TypeError("Document upload must be a file")

    filename = document.filename or str(now_s())
    content = await document.read()
    path = Path.cwd() / filename

    path.write_bytes(content)

    return path


def payload_to_update(payload: dict[str, Any]) -> dict[str, Any]:
    date = now_s()
    chat_id = int(payload.get("chat_id", -1))

    if chat_id == -1:
        raise ValueError("chat_id is missing in the payload")

    update = {
        "update_id": date * 1000,
        "message": {
            "message_id": date * 1000,
            "chat": {
                "id": config.chat_id_to_chat_id.get(chat_id, chat_id),
                "type": "private",
            },
            "from": {
                "id": config.chat_id_to_user_id.get(chat_id, 0),
                "username": config.chat_id_to_username.get(chat_id, ""),
                "first_name": config.chat_id_to_first_name.get(chat_id, ""),
                "last_name": config.chat_id_to_last_name.get(chat_id, ""),
            },
            "date": date,
            "text": payload.get("text", ""),
        },
    }

    return update


async def send_webhook(update: dict[str, Any]) -> None:
    headers: dict[str, str] = {}

    if config.webhook_secret_token:
        headers["X-Telegram-Bot-Api-Secret-Token"] = config.webhook_secret_token

    async with httpx.AsyncClient() as client:
        response = await client.post(config.webhook_url, json=update, headers=headers)
        response.raise_for_status()


@app.post("/bot{token}/sendMessage")
async def handle_sendMessage(token: str, request: Request) -> JSONResponse:
    payload = await extract_payload(request)
    payload_s = dumps(payload)

    update = payload_to_update(payload)
    update_s = dumps(update)

    response = JSONResponse(
        {
            "ok": True,
            "result": {
                "message_id": update["message"]["message_id"],
                "chat": {
                    "id": payload.get("chat_id", 0),
                    "type": "private",
                },
                "date": now_s(),
                "text": payload.get("text", ""),
            },
        }
    )

    is_command = payload.get("text", "").startswith("/")
    is_reply_to_command = (
        payload.get("reply_to_message_id") or
        payload.get("parse_mode") == "Markdown"
    )

    if config.skip_commands and (is_command or is_reply_to_command):
        log(f"[sendMessage] {payload_s}")

        return response

    limit_reached = (request.app.state.message_counter + 1) > config.max_messages

    if config.max_messages and limit_reached:
        log(f"[sendMessage] {payload_s}")

        raise HTTPException(status_code=429, detail="Message forwarding limit reached")

    request.app.state.message_counter += 1

    log(f"[sendMessage] {payload_s} -> {update_s} -> {config.webhook_url}")

    if config.sleep:
        await asyncio.sleep(config.sleep)

    await send_webhook(update)

    return response


@app.post("/bot{token}/sendChatAction")
async def handle_sendChatAction(token: str, request: Request) -> JSONResponse:
    payload = await extract_payload(request)
    payload_s = dumps(payload)

    log(f"[sendChatAction] {payload_s}")

    return JSONResponse(
        {
            "ok": True,
            "result": True,
        }
    )


@app.post("/bot{token}/sendDocument")
async def handle_sendDocument(token: str, request: Request) -> JSONResponse:
    payload = await extract_payload(request)
    payload.pop("document")
    payload_s = dumps(payload)

    path = await save_document(request)
    date = now_s()

    log(f"[sendDocument] {payload_s} -> {path}")

    return JSONResponse(
        {
            "ok": True,
            "result": {
                "message_id": date * 1000,
                "chat": {
                    "id": payload.get("chat_id", 0),
                    "type": "private",
                },
                "date": date,
                "document": {
                    "file_name": path.name,
                },
            },
        }
    )


if __name__ == "__main__":
    main()

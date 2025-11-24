import azure.functions as func
import datetime
import json
import logging
from typing import Any, Dict

import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

MCP_ROUTE = "mcp"
WEATHER_ENDPOINT = "https://weather.tsukumijima.net/api/forecast/city/230010"
RESOURCE_URI = "https://www.musashi.co.jp/company/message.html"


def _json_response(payload: Dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
    )


def _build_capabilities() -> Dict[str, Any]:
    return {
        "protocol": "model-context-protocol/1.0",
        "tools": [
            {
                "name": "health_check",
                "description": "疎通確認用のツール。引数なしで呼び出し可。",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "nagoya_weather",
                "description": "日本の公開天気予報APIから名古屋の最新天気を取得。",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        ],
        "resources": [
            {
                "name": "musashi_message",
                "uri": RESOURCE_URI,
                "description": "回答時に準拠する企業メッセージ。",
                "mimeType": "text/html",
            }
        ],
        "prompts": [
            {
                "name": "resource_aligned_reply",
                "description": "リソースに準拠した応答を指示。",
                "content": (
                    "回答は常にリソースの内容と整合させること。"
                    " 事実はリソース由来であると明示し、無根拠な補完は避ける。"
                    " 足りない情報は不足として伝える。"
                ),
            }
        ],
        "usage": {
            "invoke": {
                "method": "POST",
                "route": f"/api/{MCP_ROUTE}",
                "body": {"tool": "tool name", "arguments": {}},
            },
            "discovery": {"method": "GET", "route": f"/api/{MCP_ROUTE}"},
        },
    }


def _health_check() -> Dict[str, Any]:
    now = datetime.datetime.now().isoformat() + "Z"
    return {"tool": "health_check", "status": "ok", "timestamp": now}


def _fetch_nagoya_weather() -> Dict[str, Any]:
    try:
        response = requests.get(WEATHER_ENDPOINT, timeout=5)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logging.exception("Weather API error")
        return {
            "tool": "nagoya_weather",
            "status": "error",
            "message": "天気情報の取得に失敗しました。",
            "details": str(exc),
        }
    except ValueError:
        logging.exception("Weather API returned non-JSON")
        return {
            "tool": "nagoya_weather",
            "status": "error",
            "message": "天気情報の読み取りに失敗しました。",
        }

    forecasts = payload.get("forecasts") or []
    if not forecasts:
        return {
            "tool": "nagoya_weather",
            "status": "error",
            "message": "天気情報が空でした。",
        }

    today = forecasts[0]
    detail = today.get("detail") or {}
    weather = detail.get("weather") or today.get("telop") or "天気不明"
    updated = payload.get("publicTime") or payload.get("publicTimeFormatted")

    return {
        "tool": "nagoya_weather",
        "status": "ok",
        "city": "名古屋",
        "weather": weather,
        "updated_at": updated,
        "source": WEATHER_ENDPOINT,
    }


@app.function_name(name="mcp_entrypoint")
@app.route(route=MCP_ROUTE, methods=["GET", "POST"])
def mcp_entrypoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "GET":
        return _json_response(_build_capabilities())

    try:
        payload = req.get_json()
    except ValueError:
        return _json_response({"error": "JSON bodyが必要です。"}, status_code=400)

    tool = payload.get("tool")
    if not tool:
        return _json_response({"error": "toolフィールドを指定してください。"}, status_code=400)

    if tool == "health_check":
        return _json_response(_health_check())

    if tool == "nagoya_weather":
        return _json_response(_fetch_nagoya_weather())

    return _json_response({"error": f"未知のツールです: {tool}"}, status_code=400)

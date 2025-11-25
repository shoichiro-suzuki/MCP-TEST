import datetime
import json
import logging
from typing import Any, Dict

import azure.functions as func
import requests

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

WEATHER_ENDPOINT = "https://weather.tsukumijima.net/api/forecast/city/230010"


def _load_arguments(context: str) -> Dict[str, Any]:
    try:
        payload = json.loads(context or "{}")
        return payload.get("arguments", {}) or {}
    except json.JSONDecodeError:
        logger.warning("Invalid JSON context for MCP tool call")
        return {}


def _health_check() -> Dict[str, Any]:
    return {
        "tool": "health_check",
        "status": "ok",
    }


def _fetch_nagoya_weather() -> Dict[str, Any]:
    try:
        response = requests.get(WEATHER_ENDPOINT, timeout=5)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.exception("Weather API error")
        return {
            "tool": "nagoya_weather",
            "status": "error",
            "message": "天気情報の取得に失敗しました。",
            "details": str(exc),
        }
    except ValueError:
        logger.exception("Weather API returned non-JSON")
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


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="health_check",
    description="MCPサーバーの疎通確認",
    toolProperties="[]",
)
def health_check(context: str) -> str:
    args = _load_arguments(context)
    if args:
        logger.warning("health_check received unexpected arguments: %s", args)
    return json.dumps(_health_check(), ensure_ascii=False)


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="nagoya_weather",
    description="名古屋の最新天気を返すMCPツール",
    toolProperties=json.dumps(
        [
            {
                "propertyName": "unit",
                "propertyType": "string",
                "description": "温度単位指定。現在は無視されるが後方互換のため保持。",
            }
        ],
        ensure_ascii=False,
    ),
)
def nagoya_weather(context: str) -> str:
    args = _load_arguments(context)
    unit = args.get("unit")
    if unit is not None:
        logger.info("nagoya_weather received unit=%s (currently ignored)", unit)
    return json.dumps(_fetch_nagoya_weather(), ensure_ascii=False)

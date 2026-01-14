from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def resolve_default_output_dir() -> str:
    override_dir = os.getenv("FAIZAN_OUTPUT_DIR")
    if override_dir:
        return str(Path(override_dir))
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata and getattr(sys, "frozen", False):
        return str(Path(local_appdata) / "FaizanReportStudio" / "output")
    return str(BASE_DIR / "output")


def resolve_db_config_file() -> Path:
    override_dir = os.getenv("FAIZAN_DB_CONFIG_DIR")
    if override_dir:
        return Path(override_dir) / "db_config.json"
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata and getattr(sys, "frozen", False):
        return Path(local_appdata) / "FaizanReportStudio" / "settings" / "db_config.json"
    return BASE_DIR / "settings" / "db_config.json"


DB_CONFIG_FILE = resolve_db_config_file()

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "report_system",
    "user": "postgres",
    "password": "rayyanshah04",
    "output_dir": resolve_default_output_dir(),
}
LEGACY_HOSTS = {"192.168.0.205"}


def normalize_db_config(config: dict[str, Any]) -> dict[str, Any]:
    host = (config.get("host") or "").strip()
    if not host or host in LEGACY_HOSTS:
        config["host"] = "127.0.0.1"
    output_dir = (config.get("output_dir") or "").strip()
    if not output_dir:
        config["output_dir"] = resolve_default_output_dir()
    return config


def load_db_config() -> dict[str, Any]:
    if DB_CONFIG_FILE.exists():
        with open(DB_CONFIG_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            payload = {**DEFAULT_CONFIG, **(data or {})}
            return normalize_db_config(payload)
    return normalize_db_config(DEFAULT_CONFIG.copy())


def save_db_config(config: dict[str, Any]) -> dict[str, Any]:
    DB_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = normalize_db_config({**DEFAULT_CONFIG, **(config or {})})
    with open(DB_CONFIG_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload


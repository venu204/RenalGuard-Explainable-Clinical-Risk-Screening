"""Thin, bounded API client for calling the FastAPI backend."""
from __future__ import annotations

import json
import requests
import streamlit as st

BASE = "http://localhost:8000"

def _headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}

def post(path: str, json: dict = None, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", 30)
    response = requests.post(f"{BASE}{path}", json=json, headers=_headers(), **kwargs)
    # Any successful write can change a dashboard, directory, or history view.
    # Refresh cached reads once rather than repeatedly fetching on every rerun.
    if response.status_code in (200, 201):
        _cached_json_get.clear()
    return response

def get(path: str, params: dict = None) -> requests.Response:
    return requests.get(f"{BASE}{path}", params=params, headers=_headers(), timeout=12)


@st.cache_data(ttl=30, max_entries=160, show_spinner=False)
def _cached_json_get(path: str, params_json: str, token: str):
    """Cache safe, user-scoped GET payloads to avoid repeated page-rerun calls."""
    params = json.loads(params_json)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{BASE}{path}", params=params or None, headers=headers, timeout=12)
    return handle(response)


def get_json(path: str, params: dict | None = None):
    """Return a cached JSON payload. Token is part of the cache key to prevent sharing."""
    token = st.session_state.get("token", "")
    return _cached_json_get(path, json.dumps(params or {}, sort_keys=True), token)


def clear_read_cache() -> None:
    """Invalidate cached GET data after a write changes visible clinical records."""
    _cached_json_get.clear()

def handle(r: requests.Response):
    """Return json on success, raise with message on error."""
    if r.status_code in (200, 201):
        return r.json()
    detail = r.json().get("detail", r.text) if r.headers.get("content-type","").startswith("application/json") else r.text
    raise Exception(str(detail))

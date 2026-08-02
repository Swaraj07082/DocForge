"""Backblaze B2 upload helpers using the Native API."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set in the environment")
    return value


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> dict[str, Any]:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"B2 request failed ({exc.code}) for {url}: {detail}") from exc


def authorize_account() -> dict[str, Any]:
    """Call b2_authorize_account and return the auth payload."""
    key_id = _require_env("B2_APPLICATION_KEY_ID")
    app_key = _require_env("B2_APPLICATION_KEY")
    token = base64.b64encode(f"{key_id}:{app_key}".encode("utf-8")).decode("ascii")
    return _request_json(
        "https://api.backblazeb2.com/b2api/v4/b2_authorize_account",
        headers={"Authorization": f"Basic {token}"},
    )


def get_upload_url(api_url: str, auth_token: str, bucket_id: str) -> dict[str, Any]:
    """Call b2_get_upload_url for the given bucket."""
    query = urllib.parse.urlencode({"bucketId": bucket_id})
    return _request_json(
        f"{api_url}/b2api/v4/b2_get_upload_url?{query}",
        headers={"Authorization": auth_token},
    )


def _resolve_bucket_name(auth: dict[str, Any], bucket_id: str) -> str:
    env_name = os.getenv("B2_BUCKET_NAME")
    if env_name:
        return env_name

    buckets = (
        auth.get("apiInfo", {})
        .get("storageApi", {})
        .get("allowed", {})
        .get("buckets")
        or []
    )
    for bucket in buckets:
        if bucket.get("id") == bucket_id and bucket.get("name"):
            return bucket["name"]

    raise ValueError(
        "Could not resolve B2 bucket name. Set B2_BUCKET_NAME in the environment."
    )


def public_file_url(download_url: str, bucket_name: str, file_name: str) -> str:
    """Build the friendly public download URL for a B2 object."""
    base = download_url.rstrip("/")
    encoded_name = "/".join(urllib.parse.quote(part, safe="") for part in file_name.split("/"))
    return f"{base}/file/{bucket_name}/{encoded_name}"


def upload_bytes(
    data: bytes,
    *,
    file_name: str,
    content_type: str = "application/json",
) -> dict[str, Any]:
    """Authorize, get an upload URL, and upload `data` to B2.

    Requires env vars:
      - B2_APPLICATION_KEY_ID
      - B2_APPLICATION_KEY
      - B2_BUCKET_ID
      - B2_BUCKET_NAME (optional if the key is restricted to one named bucket)

    Returns the B2 upload response plus `publicUrl`.
    """
    bucket_id = _require_env("B2_BUCKET_ID")
    auth = authorize_account()
    storage = auth["apiInfo"]["storageApi"]
    bucket_name = _resolve_bucket_name(auth, bucket_id)
    upload = get_upload_url(storage["apiUrl"], auth["authorizationToken"], bucket_id)

    sha1 = hashlib.sha1(data).hexdigest()
    encoded_name = urllib.parse.quote(file_name, safe="/")
    headers = {
        "Authorization": upload["authorizationToken"],
        "X-Bz-File-Name": encoded_name,
        "Content-Type": content_type,
        "Content-Length": str(len(data)),
        "X-Bz-Content-Sha1": sha1,
    }
    result = _request_json(upload["uploadUrl"], method="POST", headers=headers, body=data)
    result["publicUrl"] = public_file_url(storage["downloadUrl"], bucket_name, file_name)
    return result


def _b2_configured() -> bool:
    return all(
        os.getenv(name)
        for name in ("B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY", "B2_BUCKET_ID")
    )


def upload_report(report: str, file_name: str) -> dict[str, Any]:
    """Upload a DocForge final report to B2, or save locally if B2 is not configured."""
    if not _b2_configured():
        os.makedirs("reports", exist_ok=True)
        local_path = os.path.join("reports", file_name)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(report)
        return {"publicUrl": local_path, "local": True}

    object_name = f"reports/{file_name}"
    return upload_bytes(
        report.encode("utf-8"),
        file_name=object_name,
        content_type="application/json",
    )

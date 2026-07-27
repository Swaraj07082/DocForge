import time

from groq import Groq, RateLimitError


def _retry_after_seconds(err: RateLimitError, default: float) -> float:
    try:
        header = err.response.headers.get("retry-after")
        if header:
            return float(header)
    except Exception:
        pass
    return default


def create_chat_completion(client: Groq, *, max_retries: int = 6, base_delay: float = 5.0, **kwargs):
    """Call Groq chat completions, retrying on rate-limit (429) with exponential backoff.

    A 429 means the request fits but the per-minute token/request budget is
    momentarily exhausted (common with parallel fan-out on the free tier), so
    waiting and retrying eventually succeeds. Non-rate-limit errors (e.g. 413
    "request too large") are not retried since they cannot succeed unchanged.
    """
    delay = base_delay
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as err:
            if attempt == max_retries - 1:
                raise
            wait = _retry_after_seconds(err, delay)
            print(
                f"[groq] rate limited; retrying in {wait:.0f}s "
                f"(attempt {attempt + 1}/{max_retries})",
                flush=True,
            )
            time.sleep(wait)
            delay = min(delay * 2, 60.0)

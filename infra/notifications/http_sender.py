from __future__ import annotations
import http.client, json
from urllib.parse import urlparse
from .delivery import DeliveryUncertain

class HttpSender:
    def __init__(self, channels: dict[str, str], timeout: int = 10, local_only: bool = False):
        if set(channels) != {"development", "activity"} or channels["development"] == channels["activity"]:
            raise ValueError("two distinct channel endpoints required")
        self.channels, self.timeout, self.local_only = channels, timeout, local_only
    def __call__(self, channel: str, text: str) -> tuple[int, str, int]:
        if channel not in self.channels: raise ValueError("unknown channel")
        parsed = urlparse(self.channels[channel])
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("invalid webhook URL")
        if self.local_only and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("local profile requires loopback")
        cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = cls(parsed.hostname, parsed.port, timeout=self.timeout)
        try:
            connection.request("POST", parsed.path or "/", body=json.dumps({"text": text}, ensure_ascii=False).encode(), headers={"Content-Type": "application/json"})
            response = connection.getresponse(); body = response.read().decode()
            retry = int(response.getheader("Retry-After", "0") or 0)
        except (OSError, http.client.HTTPException) as exc:
            # request를 시작한 뒤 끊기면 Slack 수신 여부를 증명할 수 없다.
            raise DeliveryUncertain from exc
        finally:
            connection.close()
        return response.status, body, retry

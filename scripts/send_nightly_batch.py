#!/usr/bin/env python3
"""Send the nightly goodnight email batch via mail-cli."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from goodnight_manager import (
    compose_goodnight,
    default_state_path,
    load_state,
    normalize_email,
    save_state,
    today_iso,
    unique_active_subscribers,
)


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = SKILL_ROOT / "data" / "send-log.jsonl"
PROXY_ENV_KEYS = (
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
)
RETRYABLE_ERROR_SNIPPETS = (
    "JWT_FETCH_FAILED",
    "AJAX_REQUEST_FAILED",
    "ENOTFOUND",
    "ECONNRESET",
    "ETIMEDOUT",
    "EPERM 127.0.0.1:7890",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send nightly goodnight emails with mail-cli.")
    parser.add_argument(
        "--state",
        default=str(default_state_path()),
        help="Path to the JSON state file.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Send date in YYYY-MM-DD. Defaults to today in local time.",
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="mail-cli profile to send from.",
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG_PATH),
        help="Path to the JSONL run log.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compose messages without sending or mutating state.",
    )
    return parser.parse_args()


def build_send_env(use_direct_env: bool) -> dict[str, str]:
    env = os.environ.copy()
    if use_direct_env:
        for key in PROXY_ENV_KEYS:
            env.pop(key, None)
    return env


def is_retryable_error(message: str) -> bool:
    return any(snippet in message for snippet in RETRYABLE_ERROR_SNIPPETS)


def send_one(profile: str, to: str, subject: str, body: str) -> None:
    if shutil.which("mail-cli") is None:
        raise RuntimeError("mail-cli is not installed or not on PATH")

    cmd = [
        "mail-cli",
        "--profile",
        profile,
        "compose",
        "send",
        "--to",
        to,
        "--subject",
        subject,
        "--body",
        body,
    ]
    attempts: list[tuple[str, dict[str, str]]] = [
        ("direct", build_send_env(use_direct_env=True)),
        ("ambient", build_send_env(use_direct_env=False)),
    ]
    last_error: Exception | None = None

    for env_name, env in attempts:
        for retry_index in range(3):
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
                return
            except subprocess.CalledProcessError as exc:
                error_text = (exc.stderr or exc.stdout or str(exc)).strip()
                last_error = subprocess.CalledProcessError(
                    exc.returncode,
                    exc.cmd,
                    output=exc.output,
                    stderr=f"[{env_name} attempt {retry_index + 1}] {error_text}",
                )
                if retry_index < 2 and is_retryable_error(error_text):
                    time.sleep(1.5 * (retry_index + 1))
                    continue
                break
            except Exception as exc:  # pragma: no cover - defensive fallback
                last_error = RuntimeError(f"[{env_name} attempt {retry_index + 1}] {exc}")
                break

    if last_error is None:  # pragma: no cover - unreachable guard
        raise RuntimeError("mail-cli send failed without an error")
    raise last_error


def append_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    state_path = Path(args.state)
    log_path = Path(args.log)
    send_on = args.date or today_iso()
    state = load_state(state_path)
    outputs: list[dict[str, Any]] = []
    sent = 0
    failed = 0
    seen_emails: set[str] = set()

    for subscriber in unique_active_subscribers(state):
        email_key = normalize_email(subscriber.get("email", ""))
        if not email_key:
            continue
        if email_key in seen_emails:
            continue
        seen_emails.add(email_key)
        if subscriber.get("last_sent_on") == send_on:
            continue

        sent_index = int(subscriber.get("sent_count", 0)) + 1
        subject, body = compose_goodnight(subscriber["name"], send_on, sent_index)
        item = {
            "to": subscriber["email"],
            "name": subscriber["name"],
            "subject": subject,
            "body": body,
        }

        if args.dry_run:
            outputs.append({**item, "status": "dry_run"})
            continue

        try:
            send_one(args.profile, item["to"], item["subject"], item["body"])
        except subprocess.CalledProcessError as exc:
            failed += 1
            outputs.append(
                {
                    **item,
                    "status": "failed",
                    "error": (exc.stderr or exc.stdout or str(exc)).strip(),
                }
            )
            continue
        except Exception as exc:  # pragma: no cover - defensive fallback
            failed += 1
            outputs.append({**item, "status": "failed", "error": str(exc)})
            continue

        subscriber["sent_count"] = sent_index
        subscriber["last_sent_on"] = send_on
        sent += 1
        outputs.append({**item, "status": "sent"})

    if not args.dry_run and sent > 0:
        save_state(state_path, state)

    summary = {
        "date": send_on,
        "profile": args.profile,
        "dry_run": args.dry_run,
        "sent": sent,
        "failed": failed,
        "count": len(outputs),
        "messages": outputs,
    }
    append_log(
        log_path,
        {
            "ran_at": datetime.now().isoformat(timespec="seconds"),
            **summary,
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

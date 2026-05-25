from __future__ import annotations
#!/usr/bin/env python3
"""CLI wrapper for standalone ChatGPT Plus checkout conversion.

Input: ChatGPT accessToken
Output: checkout URLs JSON
"""
import argparse
import asyncio
import json
import os
import sys

from app import (
    Settings,
    build_plus_checkout_payload,
    build_request_headers,
    build_checkout_url,
    build_converted_chatgpt_checkout_url,
    choose_error_status,
    extract_access_token,
    find_hosted_checkout_url,
    looks_like_cloudflare_challenge,
    normalize_payment_method,
    normalize_proxy_url,
    parse_response_json,
    OPENAI_CHECKOUT_URL,
    DEFAULT_CONVERTED_CHECKOUT_PROCESSOR_ENTITY,
)
from curl_cffi import requests as curl_requests


def read_token(args):
    token = args.access_token or os.getenv("CHATGPT_ACCESS_TOKEN", "")
    if args.token_file:
        token = open(args.token_file, "r", encoding="utf-8").read()
    if not token and not sys.stdin.isatty():
        token = sys.stdin.read()
    token = extract_access_token(token)
    if not token:
        raise SystemExit("missing valid ChatGPT accessToken; pass --access-token, --token-file, env CHATGPT_ACCESS_TOKEN, or stdin")
    return token


async def convert(args):
    settings = Settings()
    payment_method = normalize_payment_method(args.payment_method)
    access_token = read_token(args)
    processor_entity = args.processor_entity or DEFAULT_CONVERTED_CHECKOUT_PROCESSOR_ENTITY
    proxy_url = normalize_proxy_url(args.proxy_url or settings.default_proxy_url)

    payload = build_plus_checkout_payload(args, payment_method)
    request_options = {
        "json": payload,
        "headers": build_request_headers(access_token),
        "proxy": proxy_url or None,
    }
    if args.impersonate:
        request_options["impersonate"] = args.impersonate

    async with curl_requests.AsyncSession(timeout=args.timeout) as session:
        response = await session.post(OPENAI_CHECKOUT_URL, **request_options)
        text = response.text
        if looks_like_cloudflare_challenge(text):
            raise SystemExit("upstream blocked by Cloudflare challenge; try a cleaner proxy with --proxy-url")
        data = parse_response_json(text)
        status = int(response.status_code)
        checkout_session_id = str(data.get("checkout_session_id") or "").strip()
        if status >= 400 or not checkout_session_id:
            detail = data.get("detail") or data.get("message") or data.get("error") or f"upstream returned HTTP {status}"
            raise SystemExit(f"conversion failed: HTTP {choose_error_status(status)}: {detail}")

    hosted_checkout_url = find_hosted_checkout_url(data)
    checkout_url = build_checkout_url(checkout_session_id, payment_method)
    chatgpt_checkout_url = build_converted_chatgpt_checkout_url(checkout_session_id, processor_entity)
    preferred_checkout_url = hosted_checkout_url if payment_method == "paypal" and hosted_checkout_url else chatgpt_checkout_url
    result = {
        "ok": True,
        "paymentMethod": payment_method,
        "checkoutSessionId": checkout_session_id,
        "checkoutUrl": checkout_url,
        "chatgptCheckoutUrl": chatgpt_checkout_url,
        "hostedCheckoutUrl": hosted_checkout_url,
        "preferredCheckoutUrl": preferred_checkout_url,
        "processorEntity": processor_entity,
        "upstreamProcessorEntity": str(data.get("processor_entity") or "").strip(),
        "country": payload["billing_details"]["country"],
        "currency": payload["billing_details"]["currency"],
        "upstreamStatus": status,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


def main():
    p = argparse.ArgumentParser(description="Convert ChatGPT accessToken to Plus checkout URL")
    p.add_argument("--access-token", dest="access_token", help="ChatGPT accessToken / JWT")
    p.add_argument("--token-file", help="file containing accessToken")
    p.add_argument("--payment-method", default="paypal", choices=["paypal", "gopay"])
    p.add_argument("--country", default=None, help="billing country override, e.g. US")
    p.add_argument("--currency", default=None, help="billing currency override, e.g. USD")
    p.add_argument("--processor-entity", default="openai_llc")
    p.add_argument("--proxy-url", default=None, help="optional outbound proxy, e.g. http://host:port or socks5h://user:pass@host:port")
    p.add_argument("--impersonate", default=os.getenv("IMPERSONATE_BROWSER", "chrome136"))
    p.add_argument("--timeout", type=float, default=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")))
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()
    asyncio.run(convert(args))


if __name__ == "__main__":
    main()

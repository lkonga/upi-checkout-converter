# ChatGPT Plus Checkout Converter Standalone

从 GuJumpgate 剥离出的单独功能：输入 ChatGPT `accessToken`，生成 Plus checkout 支付链接。

## 1. CLI 一次性转换

```bash
cd checkout-converter-standalone
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

python cli.py --access-token 'eyJ...' --pretty
```

也支持 stdin / 文件：

```bash
cat token.txt | python cli.py --pretty
python cli.py --token-file token.txt --pretty
```

如果上游风控，用干净出口代理：

```bash
python cli.py --token-file token.txt --proxy-url 'socks5h://user:pass@host:port' --pretty
```

输出里优先用：

- `preferredCheckoutUrl`
- 其次 `hostedCheckoutUrl`
- 再其次 `chatgptCheckoutUrl`

## 2. API 服务模式

```bash
cp .env.example .env
# 编辑 .env，建议设置 CHECKOUT_CONVERTER_API_KEY
./start.sh
```

请求：

```bash
curl -X POST 'http://127.0.0.1:8080/api/checkout' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-me' \
  -d '{
    "accessToken":"eyJ...",
    "paymentMethod":"paypal",
    "country":"US",
    "currency":"USD",
    "processorEntity":"openai_llc"
  }'
```

健康检查：

```bash
curl http://127.0.0.1:8080/healthz
```

## 3. Docker

```bash
docker build -t checkout-converter .
docker run -d --name checkout-converter \
  -p 8080:8080 \
  -e CHECKOUT_CONVERTER_API_KEY=change-me \
  -e OPENAI_PROXY_URL='socks5h://user:pass@host:port' \
  checkout-converter
```

## 注意

- 这个工具不是“已有 Stripe 长链接转换器”；它是 `accessToken -> checkout session -> 支付链接`。
- 不要把 `accessToken` 写进日志或发给第三方。
- 如果返回 Cloudflare / 403 / 429，优先换干净出口或降低并发。

## Source / Attribution

This standalone version was extracted from `FoundZiGu/GuJumpgate` `services/checkout-converter` and keeps the original MIT-style attribution requirement from that project.

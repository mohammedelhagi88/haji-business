# Haji AI Integration

## AI provider
Set `HAJI_AI_API_KEY` and optionally `HAJI_AI_BASE_URL`, `HAJI_AI_MODEL`, and `HAJI_TRANSCRIPTION_MODEL`.

## API security
Set `HAJI_API_TOKEN` in production. The API accepts `Authorization: Bearer <token>` or `X-Haji-API-Key`.

## Market data
Haji now reads public Binance Spot klines through `BinancePublicMarketData`. No exchange credentials are required for market-data analysis. Configure `HAJI_MARKET_DATA_URL` and `HAJI_MARKET_INTERVAL` if needed.

## Trading safety
Trading analysis returns concrete candidates and an approval ID. The approval endpoint can only execute the **PaperBroker** simulation. No live order adapter is enabled by this project.

Endpoints:
- `POST /v1/trading/analyze` with `{ "symbols": ["BTCUSDT", "ETHUSDT"], "limit": 200 }`
- `POST /v1/trading/approval/{approvalId}` to approve the selected candidate for paper simulation.

The normal Haji agent approval endpoint remains available for other financial/sensitive intents.

## Mobile
Set `EXPO_PUBLIC_HAJI_AI_API_URL` to the API base URL. The existing app supports text, camera/gallery images, voice recording and approval actions.

# media-import-notifier

Small internal webhook receiver for Sonarr/Radarr import events. It formats media metadata and sends Telegram messages with IMDB/TVDB links.

## Required secrets

Add these to `/workspace/docker/.secrets.env` on the host; do not commit the values:

```env
MEDIA_IMPORT_TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
MEDIA_IMPORT_TELEGRAM_CHAT_ID=123456789
MEDIA_IMPORT_WEBHOOK_TOKEN=random-shared-token-for-sonarr-radarr-webhooks
```

The service accepts:

- `POST http://media-import-notifier:8080/webhook/sonarr?token=$MEDIA_IMPORT_WEBHOOK_TOKEN`
- `POST http://media-import-notifier:8080/webhook/radarr?token=$MEDIA_IMPORT_WEBHOOK_TOKEN`

## Notification contents

Episode notifications include series title, season/episode number, episode title, quality, IMDB link, TVDB episode/series link, and a poster/cover image when Sonarr sends one.

Movie notifications include movie title, year, quality, IMDB link, TMDB link, and a poster/cover image when Radarr sends one.

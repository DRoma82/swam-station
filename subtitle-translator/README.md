# Jellyfin subtitle translator

`subtitle-translate` creates a selectable Brazilian Portuguese SRT without replacing existing subtitles.

## Install

Host dependencies on Arch Linux:

```bash
sudo pacman -S --needed mkvtoolnix-cli tesseract tesseract-data-eng python-pipx
pipx install ./subtitle-translator
```

The translator calls 9Router's OpenAI-compatible API directly. By default it reads `NINE_ROUTER_ENDPOINT` and `NINE_ROUTER_API_KEY` from `~/dotfiles/.9router.env` and uses `gh/claude-sonnet-5`. Set `NINE_ROUTER_ENV_FILE` to use another env file, or export either setting to override the file.

## Use

```bash
subtitle-translate "/mnt/seagate/media/radarr/Movie (2024)/Movie (2024).mkv"
subtitle-translate "/path/to/Movie.en.srt"
```

For video input, choose an English sidecar or embedded subtitle stream. Text streams are extracted with `ffmpeg`. PGS streams are converted with Tesseract, saved as `<video>.OCR.en.srt`, and paused for review before translation.

The final file is `<video>.AI.pt-BR.srt`. The command asks before replacing an existing OCR draft or translation candidate. Jellyfin discovers the sidecar through its normal file watching.

VobSub OCR is intentionally deferred. The command reports it as unsupported instead of producing unreliable text.

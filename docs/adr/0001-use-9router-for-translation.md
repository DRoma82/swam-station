# Use 9Router for translation

The translator will call the machine's 9Router OpenAI-compatible endpoint directly and use its configured `gh/claude-sonnet-5` route. This removes the Pi subprocess and keeps provider authentication and routing in 9Router. The HTTP call remains isolated in the translation step so another compatible endpoint can replace it without changing subtitle extraction, OCR, or publishing.

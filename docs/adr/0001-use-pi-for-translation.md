# Use Pi for translation

The translator will invoke Pi as a restricted, non-interactive subprocess so translation requests use the operator's existing GitHub Copilot login and fixed Claude Sonnet 5 model. The official Copilot SDK was rejected because it exposed only automatic model routing for this account. This choice couples translation to the installed Pi command, but the call remains isolated in the translation step so a future provider can replace it without changing subtitle extraction, OCR, or publishing.

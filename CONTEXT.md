# Subtitle translation

This context covers manually creating Brazilian Portuguese subtitle alternatives for media served by Jellyfin.

## Language

**Source subtitle**:
An English subtitle selected as the input for translation. It may be a sidecar file or a subtitle stream embedded in the media file.
_Avoid_: Original subtitle, English captions

**Translation candidate**:
A natural, uncensored Brazilian Portuguese subtitle generated from a source subtitle. It preserves the source cue timing and presentation, and remains selectable beside existing Portuguese subtitles.
_Avoid_: Replacement subtitle, fixed subtitle

**Subtitle transcription**:
Text recovered from an image-based subtitle stream before translation.
_Avoid_: Subtitle extraction, OCR output

**OCR draft**:
A subtitle transcription saved for inspection before it can become the source subtitle for a translation job.
_Avoid_: Translation candidate, final subtitle

**Translation job**:
A manually requested translation of one selected source subtitle into one translation candidate.
_Avoid_: Scan, agent run

#!/usr/bin/env python3
"""Generate the narration with ElevenLabs, one take per scene, with sentence timings.

Reads the key from the environment (ELEVENLABS_API_KEY); it is never written anywhere.
For each escenas/eNN.txt writes voz/eNN.mp3 and voz/eNN.json (start and end of each sentence, in
seconds from the start of that take), which build_timeline.py picks up.

  ELEVENLABS_API_KEY=... python3 animacion/voz_elevenlabs.py <voice_id> [model_id] [scene ...]
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True,
            "speed": float(os.environ.get("VOZ_VELOCIDAD", "1.05"))}


def synthesize(voice: str, model: str, text: str, before: str, after: str) -> dict:
    body = {"text": text, "model_id": model, "voice_settings": SETTINGS, "language_code": "es"}
    if before:
        body["previous_text"] = before
    if after:
        body["next_text"] = after
    for attempt in (body, {k: v for k, v in body.items() if k not in ("previous_text", "next_text", "language_code")}):
        request = urllib.request.Request(API.format(voice=voice), data=json.dumps(attempt).encode(), method="POST",
                                         headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"],
                                                  "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")[:300]
            print(f"  HTTP {error.code}: {detail}", file=sys.stderr)
    raise SystemExit("ElevenLabs rejected the request")


def main() -> None:
    voice = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "eleven_multilingual_v2"
    only = set(sys.argv[3:])
    (ROOT / "voz").mkdir(exist_ok=True)
    files = sorted((ROOT / "escenas").glob("e*.txt"))
    texts = [" ".join(line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()) for p in files]
    used = 0
    for i, path in enumerate(files):
        if only and path.stem[1:] not in only:
            continue
        sentences = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        text = " ".join(sentences)
        result = synthesize(voice, model, text, texts[i - 1] if i else "", texts[i + 1] if i + 1 < len(texts) else "")
        (ROOT / "voz" / f"{path.stem}.mp3").write_bytes(base64.b64decode(result["audio_base64"]))
        align = result.get("alignment") or result.get("normalized_alignment") or {}
        starts, ends = align.get("character_start_times_seconds", []), align.get("character_end_times_seconds", [])
        cues, position = [], 0
        for sentence in sentences:
            first, last = position, position + len(sentence) - 1
            if starts and last < len(ends) and "".join(align["characters"][first:last + 1]) == sentence:
                cues.append({"start": round(starts[first], 3), "end": round(ends[last], 3), "text": sentence})
            position = last + 2
        if len(cues) == len(sentences):
            (ROOT / "voz" / f"{path.stem}.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            (ROOT / "voz" / f"{path.stem}.json").unlink(missing_ok=True)
        used += len(text)
        print(f"{path.stem}: {len(text)} characters, cues {'exact' if len(cues) == len(sentences) else 'estimated'}")
    print(f"characters sent: {used}")


if __name__ == "__main__":
    main()

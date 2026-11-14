#!/usr/bin/env python3
"""Build the narration track and the timeline that drives the animation.

Each file escenas/eNN.txt holds one scene, one sentence per line. For every scene:
  - if voz/eNN.mp3 or voz/eNN.wav exists (for example an ElevenLabs take of the whole scene) it is
    used, and the start of each sentence is estimated from its share of the characters;
  - otherwise every sentence is synthesized with the macOS voice in $VOZ (default Paulina).
Writes <workdir>/audio.wav and animacion/timeline.js (window.TL = {...}).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = os.environ.get("FFMPEG", "/opt/homebrew/bin/ffmpeg")
VOICE = os.environ.get("VOZ", "Paulina")
RATE = 48000
LEAD = 0.35           # silence before the first sentence
SENTENCE_GAP = 0.16   # between sentences of one scene
SCENE_GAP = 0.32      # between scenes
TAIL = 2.3            # closing card stays after the last word
EXTRA_HOLD = {"04": 0.5, "05": 0.6}   # product captures stay a little longer
SAY_SPELLING = {"AgentDojo": "Éiyent Doyo"}   # only for the macOS voice; ElevenLabs gets the real word
LIMIT = 120.0
TEMPO = float(os.environ.get("VOZ_TEMPO", "1.0"))   # time-stretch of recorded takes (pitch kept); 1.0 = untouched


def to_pcm(src: Path, dst: Path, tempo: float = 1.0) -> bytes:
    stretch = ["-af", f"atempo={tempo}"] if tempo != 1.0 else []
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(src), *stretch, "-ar", str(RATE), "-ac", "2",
                    "-c:a", "pcm_s16le", str(dst)], check=True)
    with wave.open(str(dst), "rb") as w:
        return w.readframes(w.getnframes())


def silence(seconds: float) -> bytes:
    return b"\x00" * (int(round(seconds * RATE)) * 4)


def seconds(pcm: bytes) -> float:
    return len(pcm) / 4 / RATE


def main() -> None:
    work = Path(sys.argv[1])
    work.mkdir(parents=True, exist_ok=True)
    track = silence(LEAD)
    scenes = []
    files = sorted((ROOT / "escenas").glob("e*.txt"))
    for index, path in enumerate(files):
        ident = path.stem[1:]
        sentences = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        start = seconds(track)
        take = next((p for p in (ROOT / "voz" / f"e{ident}.mp3", ROOT / "voz" / f"e{ident}.wav") if p.exists()), None)
        cues = []
        if take:
            pcm = to_pcm(take, work / f"e{ident}.wav", TEMPO)
            exact = take.with_suffix(".json")
            at = seconds(track)
            if exact.exists():   # sentence timings returned by ElevenLabs
                timings = [{**c, "start": c["start"] / TEMPO, "end": c["end"] / TEMPO}
                           for c in json.loads(exact.read_text(encoding="utf-8"))]
                pcm = pcm[:int((timings[-1]["end"] + 0.1) * RATE) * 4]   # drop the silence after the last word
                for cue in timings:
                    cues.append({"start": round(at + cue["start"], 3), "end": round(at + cue["end"], 3), "text": cue["text"]})
            else:                # estimate each sentence from its share of the characters
                total_chars = sum(len(s) for s in sentences)
                for text in sentences:
                    share = seconds(pcm) * len(text) / total_chars
                    cues.append({"start": round(at, 3), "end": round(at + share, 3), "text": text})
                    at += share
            track += pcm
        else:
            for n, text in enumerate(sentences):
                spoken = text
                for word, spelling in SAY_SPELLING.items():
                    spoken = spoken.replace(word, spelling)
                aiff = work / f"e{ident}-{n}.aiff"
                subprocess.run(["say", "-v", VOICE, "-o", str(aiff), spoken], check=True)
                pcm = to_pcm(aiff, work / f"e{ident}-{n}.wav")
                if n:
                    track += silence(SENTENCE_GAP)
                at = seconds(track)
                cues.append({"start": round(at, 3), "end": round(at + seconds(pcm), 3), "text": text})
                track += pcm
        last = index == len(files) - 1
        track += silence(EXTRA_HOLD.get(ident, 0.0) + (TAIL if last else SCENE_GAP))
        scenes.append({"id": ident, "start": round(start if index else 0.0, 3), "end": round(seconds(track), 3),
                       "voice": os.environ.get("VOZ_NOMBRE", "toma grabada") if take else f"macOS, voz {VOICE}", "s": cues})
    total = seconds(track)
    with wave.open(str(work / "audio.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(track)
    timeline = {"fps": 30, "total": round(total, 3), "scenes": scenes}
    (ROOT / "animacion" / "timeline.js").write_text(
        "window.TL = " + json.dumps(timeline, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    with (ROOT / "tiempos.tsv").open("w", encoding="utf-8") as out:
        out.write("escena\tfrase\tinicio_s\tfin_s\ttexto\n")
        for scene in scenes:
            for n, cue in enumerate(scene["s"], 1):
                out.write(f"{scene['id']}\t{n}\t{cue['start']:.2f}\t{cue['end']:.2f}\t{cue['text']}\n")
            out.write(f"{scene['id']}\tfin\t{scene['end']:.2f}\t{scene['end']:.2f}\t\n")
    print(f"total {total:.2f}s, {sum(len(s['s']) for s in scenes)} sentences")
    if total > LIMIT:
        sys.exit(f"ERROR: the narration track is {total:.2f}s, over the {LIMIT:.0f}s limit")


if __name__ == "__main__":
    main()

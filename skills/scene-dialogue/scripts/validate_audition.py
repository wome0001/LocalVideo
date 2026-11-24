"""Validate a PCM listening cut against the captions and scene timing manifest."""
import argparse
import json
from pathlib import Path
import re
import wave

TIMING = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})")


def caption_windows(file):
    text = file.read_text(encoding="utf-8-sig").strip()
    for index, block in enumerate(re.split(r"\n[ \t]*\n", text), 1):
        count, stamp, words = block.split("\n", 2)
        match = TIMING.fullmatch(stamp)
        if int(count) != index or not match or not words.strip():
            raise ValueError(f"Invalid caption {index}: {stamp}")
        value = [int(n) for n in match.groups()]
        times = []
        for h, m, s, ms in (value[:4], value[4:]):
            times.append(((h * 60 + m) * 60 + s) * 1000 + ms)
        yield times


def validate(audio, captions, manifest=None):
    with wave.open(str(audio)) as read:
        frames, rate, channels = read.getnframes(), read.getframerate(), read.getnchannels()
    duration = frames / rate
    previous = 0
    count = 0
    for start, end in caption_windows(captions):
        if not previous <= start < end <= round(duration * 1000):
            raise ValueError(f"Caption {count + 1} is unordered, overlapping or outside the track")
        previous = end
        count += 1
    if not count:
        raise ValueError("The subtitle file has no cues")

    summary = {"seconds": duration, "samples_per_channel": frames, "sample_rate": rate,
               "channels": channels, "subtitle_count": count}
    if manifest is not None:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if abs(data["seconds"] - duration) > .001 or data["sample_rate"] != rate:
            raise ValueError("Manifest timebase differs from the listening cut")
        previous_end = 0.
        expanded = 0
        for scene in data["dialogue_scenes"]:
            start = scene["listen_offset"]
            length = scene["duration"]
            if not previous_end - .001 <= start < start + length <= duration + .001:
                raise ValueError(f"Invalid or overlapping scene {scene['id']}")
            previous_end = start + length
            for cue in scene["cues"]:
                if not 0 <= cue["start"] < cue["end"] <= length + .001:
                    raise ValueError(f"Cue outside scene: {cue['id']}")
                expanded += 1
        if not any(cue.get("kind") == "pilot" for sc in data["dialogue_scenes"] for cue in sc["cues"]):
            if expanded != count:
                raise ValueError(f"Cue count differs: {expanded} manifest / {count} captions")
        summary["scene_count"] = len(data["dialogue_scenes"])
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", type=Path)
    parser.add_argument("srt", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.wave, args.srt, args.manifest), ensure_ascii=False))

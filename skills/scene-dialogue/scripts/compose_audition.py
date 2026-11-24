"""Create uninterrupted scene performances and their cue sheets. No video is changed."""
import argparse
import json
from pathlib import Path
import subprocess


SR = 48_000
VOICE_LEVEL = {}
ROLE_PROFILES = {}


def read_audio(path):
    x, rate = sf.read(path, dtype="float32", always_2d=True)
    if rate != SR:
        from math import gcd
        factor = gcd(SR, rate)
        x = resample_poly(x, SR // factor, rate // factor, axis=0)
    return x.mean(axis=1)


def edge(length, msec):
    width = min(round(msec*SR/1000), length//2)
    return (.5 - .5*np.cos(np.linspace(0,np.pi,width))).astype(np.float32)


def soften(x, start=10, end=24):
    head, tail = edge(len(x), start), edge(len(x), end)
    x[:len(head)] *= head
    if len(tail):
        x[-len(tail):] *= tail[::-1]
    return x


def envelope(x):
    step = SR//100
    steps = len(x)//step
    return np.sqrt(np.mean(x[:steps*step].reshape(-1,step)**2, axis=1))


def speech_range(x):
    e = envelope(x)
    threshold = np.clip(np.quantile(e,.88)*.055, .0033, .0100)
    active = np.flatnonzero(e >= threshold)
    if len(active) < 4:
        raise ValueError("No usable delivery in the source line")
    return active[0]/100, (active[-1]+1)/100


def level(x, role):
    e = envelope(x)
    high = e[e >= max(.010, np.percentile(e,80)*.24)]
    rms = max(.009, float(np.sqrt(np.mean(high**2)))) if len(high) else .009
    gain = 10**((VOICE_LEVEL.get(role,-23.4)+3.6)/20)/rms
    return x * np.clip(gain, .20, 5.0)


def filters(x, role, scene):
    profile = ROLE_PROFILES.get(role,{})
    hp = float(profile.get('highpass_hz',75))
    x = sosfilt(butter(2,hp,btype="highpass",fs=SR,output="sos"),x).astype(np.float32)
    if profile.get('phone',False):
        filtered = sosfilt(butter(2,[265,4300],fs=SR,btype="bandpass",output="sos"),x)
        x = (.42*x + .58*filtered).astype(np.float32)
    x = level(x, role)
    if not profile.get('phone',False) and profile.get('reflection',True):
        # A close reflection, audible as space at a low level.
        delay = max(1,round(float(scene.get('reflection_delay_ms',11))/1000 * SR))
        if delay<len(x):x[delay:] += x[:-delay] * float(scene.get('reflection_gain',.02))
    return x


def get_room(src, scene, size):
    if src is None:
        return np.zeros(size, np.float32)
    early = round(scene["picture_in"]*SR)
    donor = src[early:early+round(5.0*SR)].copy()
    e = envelope(donor)
    span = 55
    filtered = np.convolve(e**2, np.ones(span)/span, "valid")
    order = np.argsort(filtered)
    pos = next((a for a in order if np.max(np.abs(donor[a*480:(a+span)*480]))<.019), None)
    if pos is None:
        raise ValueError(f"No quiet reference for scene {scene['name']}")
    room = donor[pos*480:(pos+span)*480].copy()
    rms = max(.00001,float(np.sqrt(np.mean(room**2))))
    room *= min(2.8, float(scene.get('room_rms',.0013)) / rms)
    soften(room,35,35)
    return np.resize(room, size)


def get_pilot(name, pilot_root):
    if pilot_root is None:
        raise ValueError("An input pilot requires --pilot-root")
    stem = pilot_root / name
    x = read_audio(stem.with_suffix(".wav"))
    if len(x) < SR*.16:
        raise ValueError(f"Unexpected pilot length for {name}")
    return x, stem.with_suffix(".srt")


def cue_times(subtitle):
    for block in subtitle.read_text(encoding="utf-8-sig").strip().split("\n\n"):
        _, time, *words = block.splitlines()
        a,b = time.split(" --> ")
        def convert(x):
            h,m,rest = x.split(":")
            s,ms = rest.split(",")
            return float(int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000)
        yield convert(a),convert(b),"\n".join(words)


def clock(sec):
    sec, ms = divmod(round(sec*1000),1000)
    mm, ss = divmod(sec,60)
    hh, mm = divmod(mm,60)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def srt_at(path, events):
    blocks = []
    for i,(start,end,text) in enumerate(events,1):
        if i < len(events):
            end = min(end,events[i][0])
        if end <= start:
            raise ValueError(f"Invalid speech cue {i}")
        blocks.append(f"{i}\n{clock(start)} --> {clock(end)}\n{text}")
    path.write_text("\n\n".join(blocks)+"\n",encoding="utf-8")


def preview(ffmpeg,infile,outfile):
    subprocess.run([ffmpeg,"-hide_banner","-v","error","-y","-i",infile,"-c:a","libmp3lame",
                    "-b:a","160k",outfile],check=True)


def render(args):
    global np,sf,butter,sosfilt,resample_poly
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter,sosfilt,resample_poly
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    VOICE_LEVEL.update(plan.get("role_levels", {}))
    ROLE_PROFILES.update(plan.get('role_profiles',{}))
    manifest_dir = args.output
    manifest_dir.mkdir(parents=True,exist_ok=False)
    previous = read_audio(args.reference_mix) if args.reference_mix else None
    total, overall_events, report = [],[],[]
    story_time=0.
    for scene in plan["scenes"]:
        position=float(scene.get('lead_seconds',.25))
        pieces, subtitles, stats = [],[],[]
        for row in scene["lines"]:
            if row["kind"]=="pilot":
                audio, cue = get_pilot(row["pilot"],args.pilot_root)
                # Retain the approved cut and its internal timing as a block.
                audio = audio * .67
                pieces.append((round(position*SR),audio))
                subtitles.extend((position+a,position+b,t) for a,b,t in cue_times(cue))
                start, end = position, position + len(audio)/SR
                stats.append({"id":row["id"],"kind":"pilot","name":row["pilot"],"start":start,"end":end})
                position = end + row["hold"]
                continue
            if row["kind"]=="archive":
                archive = read_audio(Path(row["file"])) if row.get("file") else previous
                if archive is None:
                    raise ValueError(f"Missing archive source for {row['id']}")
                a,b = row.get("range", (0,len(archive)/SR))
                original = archive[round(a*SR):round(b*SR)].copy()
            else:
                take = row.get("take", row["id"])
                original = read_audio(args.takes/f"{take}.wav")
            first,last = speech_range(original)
            guard_head = round(max(0.,first-.050)*SR)
            guard_tail = round(min(len(original)/SR,last+.075)*SR)
            audio = filters(original[guard_head:guard_tail],row["role"],scene)
            audio *= 10**(row.get("gain_db",0)/20)
            soften(audio,10,25)
            at = round(position*SR)
            lead=first-guard_head/SR
            voiced_end=position+last-guard_head/SR
            pieces.append((at,audio))
            subtitles.append((position+lead,voiced_end,row["text"]))
            stat={"id":row["id"],"kind":row["kind"],"role":row["role"],"text":row["text"],
                  "start":round(position+lead,4),"end":round(voiced_end,4),"hold":row["hold"],
                  "natural_utterance_s":round(last-first,4)}
            if row["kind"]=="tts":
                metadata=json.loads((args.takes/f"{take}.json").read_text(encoding="utf-8"))
                if metadata["text"] != row["text"]:
                    raise ValueError(f"Incorrect version on disk: {row['id']}")
                stat["voice"]=metadata["voice"]
            stats.append(stat)
            position=voiced_end+row["hold"]
        size = max(max(at+len(x) for at,x in pieces)+round(.28*SR),round((position+.27)*SR))
        room=get_room(previous, scene, size)
        mix=np.zeros(size, np.float32)
        for at, take in pieces:
            mix[at:at+len(take)] += take
        mix += room
        # Softly catch only the strongest transients to keep scene levels even.
        magnitude=np.abs(mix)
        high=magnitude>.60
        mix[high]=np.sign(mix[high])*(.60+.18*np.tanh((magnitude[high]-.60)/.18))
        soften(mix,70,90)
        stem = manifest_dir/f"{scene['id']:02d}_{scene['name']}"
        wav=stem.with_suffix(".wav")
        sf.write(wav,mix,SR,subtype="PCM_24")
        preview(args.ffmpeg,wav,stem.with_suffix(".mp3"))
        srt_at(stem.with_suffix(".srt"),subtitles)
        report.append({"id":scene["id"],"name":scene["name"],"direction":scene["beat"],
                       "picture_range":[scene["picture_in"],scene["picture_out"]],
                       "listen_offset":round(story_time,4),"duration":round(len(mix)/SR,4),
                       "mono_peak":round(float(np.max(np.abs(mix))),6),"cues":stats})
        overall_events.extend((story_time+a,story_time+b,t) for a,b,t in subtitles)
        total.append(mix)
        story_time += len(mix)/SR
        if scene["id"] != len(plan["scenes"]):
            silence=np.zeros(round(.84*SR),np.float32)
            total.append(silence)
            story_time += len(silence)/SR
        print(scene["id"],scene["name"],f"{len(mix)/SR:.2f}s",len(subtitles),"cues",flush=True)

    wav=manifest_dir/"dialogue-audition.wav"
    sf.write(wav,np.concatenate(total),SR,subtype="PCM_24")
    preview(args.ffmpeg,wav,wav.with_suffix(".mp3"))
    srt_at(wav.with_suffix(".srt"),overall_events)
    record={"seconds":round(story_time,5),"sample_rate":SR,"dialogue_scenes":report,
            "unchanged_picture":True,"video_muxed":False}
    (manifest_dir/"timeline.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    print(wav,round(story_time,3),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--takes",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--ffmpeg",type=Path,required=True)
    parser.add_argument("--reference-mix",type=Path)
    parser.add_argument("--pilot-root",type=Path)
    render(parser.parse_args())

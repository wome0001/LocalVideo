"""Submit a ComfyUI API workflow and validate terminal history and actual outputs."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
OUTPUT_COLLECTIONS = ("images", "gifs", "videos", "latents")
DETAIL_LIMIT = 2000


class ComfyError(RuntimeError):
    """ComfyUI answered, but the answer is an error."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class TransportError(ComfyError):
    """ComfyUI was unreachable or did not answer with JSON."""


def parse_base_url(value):
    """Return the loopback service URL, rejecting anything that only looks local."""
    parts = urllib.parse.urlsplit(value)
    if parts.scheme != "http":
        raise ValueError("--url must use http and a loopback host")
    if parts.hostname not in LOOPBACK_HOSTS:
        raise ValueError("This runner is restricted to the local ComfyUI service")
    if parts.username or parts.password:
        raise ValueError("--url must not embed credentials")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise ValueError("--url must not carry a path, query or fragment")
    try:
        parts.port
    except ValueError as error:
        raise ValueError(f"Invalid port in --url: {error}") from error
    return value.rstrip("/")


def request(base, endpoint, payload=None, timeout=30):
    body = None if payload is None else json.dumps(payload).encode("utf8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + endpoint, data=body, headers=headers,
                                 method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        try:
            detail = error.read().decode("utf8", "replace")[:DETAIL_LIMIT]
        except OSError:
            detail = "no response body"
        raise ComfyError(f"ComfyUI {error.code} on {endpoint}: {detail}",
                         status=error.code) from error
    except (urllib.error.URLError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise TransportError(f"ComfyUI unreachable at {base}{endpoint}: {reason}") from error
    if not raw:
        raise TransportError(f"Empty response from ComfyUI {endpoint}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise TransportError(
            f"Non-JSON response from ComfyUI {endpoint}: {raw[:200]!r}") from error
    if not isinstance(data, dict):
        raise TransportError(f"Unexpected JSON payload from ComfyUI {endpoint}")
    return data


def validate_history(history):
    """Raise for a terminal failure, otherwise report whether the run completed."""
    status = history.get("status")
    if not isinstance(status, dict):
        raise ComfyError("History record has no status block")
    failures = []
    for message in status.get("messages") or []:
        if not isinstance(message, (list, tuple)) or not message:
            continue
        if message[0] in ("execution_error", "execution_interrupted"):
            failures.append(message)
    if failures or status.get("status_str") == "error":
        details = [{"event": item[0], **{key: item[1].get(key) for key in
                   ("node_id", "exception_type", "exception_message")}} for item in failures if isinstance(item[1], dict)]
        raise ComfyError(f"ComfyUI execution failed: {details or status.get('status_str')}")
    return status.get("completed") is True and status.get("status_str") == "success"


def file_hash(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def inspect_media(path, args):
    if path.suffix.lower() == '.latent':
        from safetensors import safe_open
        import torch
        with safe_open(str(path),framework='pt',device='cpu') as saved:
            if 'latent_tensor' not in saved.keys() or 'latent_format_version_0' not in saved.keys():
                raise ComfyError('Saved latent is missing its tensor/version metadata')
            latent=saved.get_tensor('latent_tensor')
        if latent.ndim!=5 or not bool(torch.isfinite(latent).all()):
            raise ComfyError('Saved video latent has invalid shape or nonfinite values')
        return {'kind':'latent','shape':list(latent.shape),'dtype':str(latent.dtype),'finite':True}
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        from PIL import Image
        with Image.open(path) as frame:
            frame.verify()
        with Image.open(path) as frame:
            width, height = frame.size
            count = getattr(frame, "n_frames", 1)
            for index in range(count):
                frame.seek(index)
                frame.load()
        result = {"kind": "image", "width": width, "height": height, "frames": count}
    elif path.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
        probe = subprocess.check_output(
            [os.environ.get('LOCALVIDEO_FFPROBE','ffprobe'), "-v", "error", "-count_frames",
             "-show_streams", "-show_format", "-of", "json", str(path)], timeout=180)
        metadata = json.loads(probe)
        stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        duration = float(stream.get("duration", metadata.get("format", {}).get("duration", 0)))
        if duration <= 0:
            raise ComfyError(f"No positive video duration: {path}")
        subprocess.run([os.environ.get('LOCALVIDEO_FFMPEG','ffmpeg'), "-v", "error", "-xerror",
                        "-i", str(path), "-f", "null", "NUL"], check=True, timeout=180)
        width, height = stream["width"], stream["height"]
        result = {"kind": "video", "width": width, "height": height, "duration": duration,
                  "frames": stream.get("nb_read_frames"), "fully_decoded": True}
        if args.min_duration is not None and duration < args.min_duration:
            raise ComfyError(f"Video is too short: {duration}")
        if args.max_duration is not None and duration > args.max_duration:
            raise ComfyError(f"Video is too long: {duration}")
    else:
        raise ComfyError(f"Unsupported media extension: {path}")
    if args.expected_width is not None and width != args.expected_width:
        raise ComfyError(f"Unexpected width {width}: {path}")
    if args.expected_height is not None and height != args.expected_height:
        raise ComfyError(f"Unexpected height {height}: {path}")
    return result


def collect_outputs(record, root, args):
    """Verify every reported output exists inside root and hash it once."""
    outputs = []
    seen = set()
    for node_id, node in sorted((record.get("outputs") or {}).items()):
        if not isinstance(node, dict):
            continue
        for collection in OUTPUT_COLLECTIONS:
            entries = node.get(collection) or []
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("type") != "output":
                    continue
                name = entry.get("filename")
                if not isinstance(name, str) or not name:
                    raise ComfyError(f"Node {node_id} reported an output without a filename")
                path = (root / str(entry.get("subfolder") or "") / name).resolve()
                if not path.is_relative_to(root):
                    raise ComfyError(f"Output path leaves the local output directory: {path}")
                if not path.is_file():
                    raise ComfyError(f"Output not complete: {path}")
                size = path.stat().st_size
                if not size:
                    raise ComfyError(f"Output is empty: {path}")
                if str(path) in seen:
                    continue
                seen.add(str(path))
                digest = file_hash(path)
                outputs.append({"node": node_id, "path": str(path),
                                "bytes": size, "sha256": digest,
                                "media": inspect_media(path, args)})
    return outputs


def wait_for_history(base, prompt_id, deadline, interval):
    """Poll the history endpoint until the prompt finishes, surviving brief outages."""
    attempts = 0
    last_error = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            detail = f" (last poll error: {last_error})" if last_error else ""
            raise TimeoutError(
                f"Local prompt did not finish before the deadline: {prompt_id}{detail}")
        attempts += 1
        try:
            history = request(base, "/history/" + urllib.parse.quote(prompt_id),
                              timeout=max(1.0, min(30.0, remaining)))
        except TransportError as error:
            last_error = error
            history = None
        except ComfyError as error:
            if error.status is None or error.status < 500:
                raise
            last_error = error
            history = None
        if history:
            record = history.get(prompt_id)
            if isinstance(record, dict) and validate_history(record):
                return record, attempts
        pause = min(interval, max(0.0, deadline - time.monotonic()))
        if pause > 0:
            time.sleep(pause)


def cancel_prompt(base, prompt_id):
    """Best-effort removal of this prompt from the local queue."""
    try:
        request(base, "/queue", {"delete": [prompt_id]}, timeout=10)
        return "requested"
    except ComfyError as error:
        return f"failed: {error}"


def write_receipt(path, receipt):
    """Write the receipt atomically so a killed runner never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2), encoding="utf8")
    os.replace(temporary, path)


def load_workflow(path):
    try:
        graph = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise ValueError(f"Cannot read workflow {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Workflow is not valid JSON: {error}") from error
    if not isinstance(graph, dict) or not graph:
        raise ValueError("Workflow must be a non-empty API prompt graph")
    for node_id, node in graph.items():
        if not isinstance(node, dict) or "class_type" not in node:
            raise ValueError(f"Node {node_id} has no class_type; export the API format")
        if not isinstance(node.get("inputs"), dict):
            raise ValueError(f"Node {node_id} has no inputs object")
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8192")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--prompt-id")
    parser.add_argument("--client-id", help="Optional local websocket timing correlation ID")
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--min-duration", type=float)
    parser.add_argument("--max-duration", type=float)
    parser.add_argument("--min-output-files", type=int, default=1)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be a positive number of seconds")
    if args.poll_interval <= 0:
        parser.error("--poll-interval must be positive")
    try:
        base = parse_base_url(args.url)
    except ValueError as error:
        parser.error(str(error))
    root = args.output_dir.resolve()
    if not root.is_dir():
        parser.error(f"--output-dir must be an existing directory: {root}")

    start = time.monotonic()
    receipt = {
        "url": base,
        "workflow": str(args.workflow.resolve()),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "state": "starting",
    }
    prompt_id = None
    try:
        graph = load_workflow(args.workflow)
        receipt["workflow_sha256"] = file_hash(args.workflow)
        receipt["inputs"] = []
        if args.input_dir:
            input_root = args.input_dir.resolve()
            for node in graph.values():
                if node["class_type"] in ("LoadImage", "LoadAudio", "LoadLatent"):
                    field = {"LoadImage":"image","LoadAudio":"audio","LoadLatent":"latent"}[node["class_type"]]
                    image_path = (input_root / node["inputs"][field]).resolve()
                    if not image_path.is_relative_to(input_root):
                        raise ComfyError("Input image leaves the permitted input folder")
                    receipt["inputs"].append({"path": str(image_path), "sha256": file_hash(image_path)})
        result = {"prompt_id": args.prompt_id} if args.prompt_id else request(
            base, "/prompt", {"prompt": graph, "client_id": args.client_id or str(uuid.uuid4())})
        prompt_id = result.get("prompt_id")
        receipt["resumed"] = bool(args.prompt_id)
        receipt.update(prompt_id=prompt_id, state="submitted")
        if result.get("node_errors"):
            rejected = json.dumps(result["node_errors"])[:DETAIL_LIMIT]
            raise ComfyError(f"Workflow rejected: {rejected}")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ComfyError(f"Workflow rejected: {json.dumps(result)[:DETAIL_LIMIT]}")
        submission_path = root.parent / "task-submissions" / (prompt_id + ".json")
        if args.prompt_id:
            if not submission_path.is_file():
                raise ComfyError("Resume requires the original local submission receipt")
            original = json.loads(submission_path.read_text(encoding="utf8"))
            if original.get("workflow_sha256") != receipt["workflow_sha256"] or original.get("inputs") != receipt["inputs"]:
                raise ComfyError("Resume workflow or input content differs from the original submission")
        else:
            write_receipt(submission_path, receipt)
        receipt["submission_receipt"] = str(submission_path)
        write_receipt(args.report, receipt)

        record, polls = wait_for_history(base, prompt_id, start + args.timeout,
                                         args.poll_interval)
        actual_prompt = record.get("prompt", [])
        if len(actual_prompt) < 3 or actual_prompt[2] != graph:
            raise ComfyError("Completed history belongs to a different workflow")
        outputs = collect_outputs(record, root, args)
        if len(outputs) < args.min_output_files:
            raise ComfyError("Successful history had no verified output files")
        if any(n['class_type']=='SaveVideo' for n in graph.values()) and not any(o['media']['kind']=='video' for o in outputs):
            raise ComfyError('Saved latent alone does not satisfy a requested video output')
        receipt.update(state="success", polls=polls, outputs=outputs, history=record)
    except Exception as error:
        receipt.update(state="failed", error=f"{type(error).__name__}: {error}")
        if isinstance(error, TimeoutError):
            receipt["state"] = "timed_out"
            receipt["cancellation"] = "not_requested; the server job may still be running"
        raise
    finally:
        receipt["seconds"] = round(time.monotonic() - start, 3)
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_receipt(args.report, receipt)
    print(prompt_id, receipt["state"], receipt["seconds"], flush=True)


if __name__ == "__main__":
    main()

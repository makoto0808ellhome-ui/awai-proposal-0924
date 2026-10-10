"""Resumable HTTPS range download, strict byte ranges and full asset SHA256."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
from pathlib import Path
import shutil
import time
import requests
import pipeline as p

BLOCK = 128 * 1024 * 1024


def download_asset(asset):
    target = p.WAN / asset["local_relative_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    size = asset["bytes"]
    if target.is_file() and target.stat().st_size == size:
        print("Present", asset["remote_path"], flush=True)
        return
    chunks = target.parent / (target.name + ".range-chunks")
    chunks.mkdir(exist_ok=True)
    total_blocks = (size + BLOCK - 1) // BLOCK

    def get_block(i):
        begin, end = i * BLOCK, min((i + 1) * BLOCK, size) - 1
        chunk = chunks / f"{i:05d}.bin"
        if chunk.is_file() and chunk.stat().st_size == end - begin + 1:
            return chunk
        for attempt in range(3):
            try:
                url = asset["url"] + f"?download=true&kariju_range={begin}"
                with requests.get(url, headers={"Range": f"bytes={begin}-{end}"},
                                  stream=True, timeout=(20, 30)) as response:
                    response.raise_for_status()
                    if size >= BLOCK:
                        expected = f"bytes {begin}-{end}/{size}"
                        if response.status_code != 206 or response.headers.get("Content-Range") != expected:
                            raise RuntimeError("Server range mismatch")
                    with chunk.open("wb") as stream:
                        for data in response.iter_content(1024 * 1024):
                            stream.write(data)
                if chunk.stat().st_size != end - begin + 1:
                    raise RuntimeError("Truncated range")
                return chunk
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)

    complete = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(get_block, i) for i in range(total_blocks)]
        for future in as_completed(futures):
            future.result()
            complete += 1
            if complete % 8 == 0 or complete == total_blocks:
                p.write_json("download_progress.json", {"asset": asset["remote_path"],
                    "completed_blocks": complete, "total_blocks": total_blocks,
                    "timestamp": time.time(), "ai_generation_executed": False})
                print(f"{asset['remote_path']}: {complete}/{total_blocks} blocks", flush=True)
    assembled = target.with_suffix(target.suffix + ".assembling")
    with assembled.open("wb") as output:
        for i in range(total_blocks):
            with (chunks / f"{i:05d}.bin").open("rb") as source:
                shutil.copyfileobj(source, output, 16 * 1024 * 1024)
    if assembled.stat().st_size != size:
        raise RuntimeError("Assembled size mismatch")
    if asset.get("sha256") and p.digest(assembled) != asset["sha256"]:
        raise RuntimeError("Assembled SHA256 mismatch")
    assembled.replace(target)
    # Remove only task-created verified chunk files, after the final file is verified.
    expected_root = p.WAN.resolve()
    if not chunks.resolve().is_relative_to(expected_root):
        raise RuntimeError("Chunk cleanup path outside task environment")
    for chunk in chunks.glob("*.bin"):
        chunk.unlink()
    chunks.rmdir()
    print("Verified", asset["remote_path"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    if not args.approved:
        raise SystemExit("User approval required")
    manifest, missing = p.required_assets()
    for asset in missing:
        download_asset(asset)
    p.write_json("download_progress.json", {"status": "all_assets_verified", "timestamp": time.time(),
                                            "total_bytes": manifest["total_bytes"]})
    print("ALL_ASSETS_VERIFIED", flush=True)

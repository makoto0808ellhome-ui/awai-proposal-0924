"""Kariju: prepare / explicit download / WanGP generation / source restoration.
Run with Desktop/Wan2GP-kariju-latest/venv/Scripts/python.exe. No website files are edited.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
WAN = Path(r"C:/Users/User/Desktop/Wan2GP-kariju-latest")
ORIGINAL_WAN = Path(r"C:/Users/User/Desktop/Wan2GP")
SOURCE = HERE.parents[1] / "materials/揚げ動画/揚げ_3.mp4"
FPS, FRAMES, WIDTH, HEIGHT = 24, 145, 1024, 576
START = 19.0
POSITIVE = (
    "A realistic close-up commercial food video showing freshly fried Japanese karaage "
    "chicken being lifted from bubbling hot oil using a metal fryer scoop. Extend the "
    "existing fryer, bubbling oil, and stainless steel kitchen environment naturally to "
    "the left and right. Preserve the original chicken appearance, lifting movement, "
    "camera angle, lighting, and timing. Fixed camera, realistic food photography, "
    "natural oil bubbles and steam, consistent visual details across all frames. "
    "Keep all existing chicken, scoop and hands confined to the original central video. "
    "The extended side areas contain only the existing fryer, oil and stainless steel."
)
NEGATIVE = (
    "extra hands, duplicate chicken, duplicate scoop, deformed frying basket, distorted "
    "food, warped stainless steel, unnatural oil movement, flickering, inconsistent "
    "geometry, camera movement, text, watermark, new objects."
)
REFINED_POSITIVE = (
    "A photorealistic fixed-camera view of a stainless steel commercial deep fryer. "
    "The existing central video is preserved. Only one scoop of karaage and one hand "
    "exist, exclusively inside the original narrow central video. Extend the background "
    "to both sides as continuous empty stainless steel walls, metal fryer rims and "
    "an empty oil surface. The left and right extended regions are completely empty "
    "of food, chicken, hands and utensils. The right oil bay contains clear hot oil "
    "and small natural bubbles only, with plain steel reflections. All food stays "
    "in the single central scoop. Match the central lighting, perspective and timing. "
    "Stable metal geometry, consistent realistic oil motion throughout the video."
)


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run(args):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result.stdout


def ffmpeg(*args):
    return run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args])


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                           "-of", "json", path]))


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_rect(w, h, source_w, source_h):
    # Read only the pure geometry functions; do not import/initialize the AI runtime.
    tree = ast.parse((WAN / "shared/utils/utils.py").read_text(encoding="utf-8-sig"))
    names = {"parse_outpainting_ratio", "_split_outpainting_padding",
             "resolve_outpainting_dims", "_quantize_outpainting_axis",
             "get_outpainting_frame_location"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in names]
    if len(selected) != len(names):
        raise RuntimeError("WanGP geometry API changed; inspect before generating")
    scope = {"math": math}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "WanGP geometry", "exec"), scope)
    return scope["get_outpainting_frame_location"](
        h, w, [0, 0, 0, 0], 1, "16:9", source_h, source_w, quantize_margins=0)


def prepare():
    info = probe(SOURCE)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    if float(info["format"]["duration"]) < START + FRAMES / FPS:
        raise RuntimeError("Source does not cover the entire selected interval")
    if v["width"] / v["height"] >= WIDTH / HEIGHT:
        raise RuntimeError("Expected portrait source")
    ffmpeg("-i", SOURCE, "-ss", START, "-vf", "fps=24,setpts=PTS-STARTPTS",
           "-frames:v", FRAMES, "-an", "-c:v", "libx264", "-crf", "12",
           "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           HERE / "source_clip_24fps.mp4")
    # Exact 9:16 mapping, no crop. Use this same decoded control file for restoration.
    ffmpeg("-i", HERE / "source_clip_24fps.mp4", "-vf", "scale=324:576:flags=lanczos,setsar=1",
           "-an", "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", HERE / "control_video.mp4")
    ffmpeg("-i", HERE / "source_clip_24fps.mp4", "-vf", "fps=1,scale=180:320,tile=3x2",
           "-frames:v", "1", HERE / "selected-contact-sheet.jpg")
    ffmpeg("-i", HERE / "control_video.mp4", "-vf", "pad=1024:576:350:0:color=0x313536",
           "-frames:v", "1", HERE / "layout-preview.jpg")
    write_json("source_manifest.json", {
        "source": str(SOURCE), "source_sha256": digest(SOURCE), "source_probe": info,
        "start_seconds": START, "end_seconds": START + FRAMES / FPS,
        "frames": FRAMES, "fps": FPS, "speed_changed": False, "crop": None,
        "control_probe": probe(HERE / "control_video.mp4"),
        "control_sha256": digest(HERE / "control_video.mp4"),
        "native_source_rect_y_x_h_w": [0, 350, 576, 324],
        "layout_preview_note": "Side areas are placeholders, NOT AI-generated content."
    })
    print("Prepared source clip and layout; no AI generation performed.")


def required_assets():
    manifest = json.loads((HERE / "download_manifest.json").read_text(encoding="utf-8"))
    missing = []
    for a in manifest["assets"]:
        target = WAN / a["local_relative_path"]
        if not target.is_file() or target.stat().st_size != a["bytes"]:
            missing.append(a)
    return manifest, missing


def download(approved):
    if not approved:
        raise RuntimeError("Downloading requires the user's prior approval; add --approved only after approval")
    from huggingface_hub import hf_hub_download
    manifest, missing = required_assets()
    for a in missing:
        target = WAN / a["local_relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        download_root = WAN / ("loras/ltx2" if a["local_relative_path"].startswith("loras/") else "ckpts")
        print("Downloading", a["remote_path"], flush=True)
        path = hf_hub_download(repo_id=manifest["repo_id"], filename=a["remote_path"],
                               revision=manifest["revision"], local_dir=str(download_root))
        if Path(path).stat().st_size != a["bytes"]:
            raise RuntimeError("Unexpected downloaded asset size: " + a["remote_path"])
        if a.get("sha256") and digest(path) != a["sha256"]:
            raise RuntimeError("Asset SHA256 mismatch: " + a["remote_path"])
        print("Verified", a["remote_path"], flush=True)


def generate(smoke=False, refined=False):
    _, missing = required_assets()
    if missing:
        raise RuntimeError(f"{len(missing)} assets missing; no download or generation attempted")
    if not (HERE / "control_video.mp4").is_file():
        raise RuntimeError("Run prepare first")
    if not smoke:
        smoke_status = HERE / "generation_smoke_status.json"
        if not smoke_status.is_file() or json.loads(smoke_status.read_text(encoding="utf-8")).get("status") != "generated_unreviewed":
            raise RuntimeError("Complete smoke first; full-length 10GB compatibility remains unverified")
    # Do not let runtime asset resolution initiate any hidden model downloads.
    os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_PROGRESS_BARS="1")
    sys.path.insert(0, str(WAN))
    import torch
    params = {
        "model_type": "ltx2_25_22B_distilled", "prompt": REFINED_POSITIVE if refined else POSITIVE,
        "negative_prompt": NEGATIVE, "seed": 20261011 if refined else 20261010,
        "resolution": "1024x576", "video_length": 17 if smoke else FRAMES,
        "num_inference_steps": 8, "guidance_phases": 1,
        "video_prompt_type": "VG", "video_guide": str(HERE / "control_video.mp4"),
        "video_guide_outpainting": "0 0 0 0", "video_guide_outpainting_ratio": "16:9",
        "denoising_strength": 1.0, "audio_prompt_type": "A",
        "audio_source": None, "audio_guide": None, "image_prompt_type": "",
        "spatial_upsampling": "", "temporal_upsampling": "", "self_refiner_setting": 0,
    }
    suffix = "smoke" if smoke else ("refined" if refined else "full")
    state = {"status": "starting", "parameters_submitted": params,
             "wangp_version": "17.17",
             "wangp_commit": run(["git", "-C", WAN, "rev-parse", "HEAD"]).strip(),
             "runtime_configuration": {"profile": 4, "attention": "sdpa", "vae_config": 0,
                 "transformer_quantization": "int8_convrot", "text_encoder_quantization": "int8_convrot",
                 "outpaint_method": 1, "distilled_effective_guidance_scale": 1.0},
             "model_manifest": "download_manifest.json",
             "gpu": run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]).strip(), "started_unix": time.time(),
             "vram_10gb_verified": False, "audio_mode": "null audio conditioning; output stripped with FFmpeg"}
    write_json(f"generation_{suffix}_status.json", state)
    monitor_stop = threading.Event()
    memory_samples = []
    def monitor_gpu():
        while not monitor_stop.is_set():
            try:
                values = run(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                              "--format=csv,noheader,nounits"]).strip().splitlines()[0].split(",")
                memory_samples.append((int(values[0]), int(values[1])))
            except Exception:
                pass
            monitor_stop.wait(2)
    threading.Thread(target=monitor_gpu, daemon=True).start()
    # Copy config for this process; keep the existing WanGP configuration untouched.
    config = json.loads((ORIGINAL_WAN / "wgp_config.json").read_text(encoding="utf-8"))
    config.update(attention_mode="sdpa", transformer_quantization="int8",
                  text_encoder_quantization="int8", profile=4, video_profile=4,
                  vae_config=0, enhancer_enabled=0, deepy_enabled=0)
    config.update(checkpoints_paths=[str(WAN / "ckpts"), str(ORIGINAL_WAN / "ckpts")],
                  loras_root=str(WAN / "loras"))
    config_path = WAN / "wgp_config.json"
    write_json(str(config_path), config)
    try:
        from shared.api import init
        session = init(root=WAN, config_path=config_path, output_dir=HERE / f"raw-{suffix}",
                       cli_args=["--attention", "sdpa", "--profile", "4"])
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        # Guard the direct downloader as well as huggingface_hub offline mode.
        import shared.utils.download as dl
        def blocked_download(*args, **kwargs):
            raise RuntimeError("Unexpected missing runtime asset; download blocked pending approval")
        dl.download_file = blocked_download
        session._ensure_runtime().module.download_file = blocked_download
        defaults = session.get_default_settings("ltx2_25_22B_distilled")
        defaults.update(params)
        write_json(f"submitted_settings_{suffix}.json", defaults)
        torch.cuda.reset_peak_memory_stats()
        result = session.run_task(defaults)
        if not result.success:
            raise RuntimeError("; ".join(e.message for e in result.errors))
        videos = [Path(f) for f in result.generated_files if Path(f).suffix.lower() == ".mp4"]
        if len(videos) != 1:
            raise RuntimeError(f"Expected one generated MP4, got {len(videos)}")
        target = HERE / ("smoke_outpaint.mp4" if smoke else
                        ("kariju_pc_outpaint_refined.mp4" if refined else "kariju_pc_outpaint_test.mp4"))
        ffmpeg("-i", videos[0], "-map", "0:v:0", "-c:v", "copy", "-an",
               "-movflags", "+faststart", target)
        output_probe = probe(target)
        output_video = next(s for s in output_probe["streams"] if s["codec_type"] == "video")
        if int(output_video.get("nb_frames", 0)) != params["video_length"]:
            raise RuntimeError("Generated frame count differs from the requested workload")
        state.update(status="generated_unreviewed", output=str(target),
                     output_probe=output_probe, finished_unix=time.time(),
                     vram_10gb_verified=torch.cuda.get_device_properties(0).total_memory <= 10240*1024**2,
                     verified_workload_frames=params["video_length"],
                     nvidia_smi_peak_used_mib_sampled=max((s[0] for s in memory_samples), default=None),
                     gpu_memory_sampling_interval_seconds=2,
                     torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                     torch_peak_reserved_bytes=torch.cuda.max_memory_reserved())
        write_json(f"generation_{suffix}_status.json", state)
        if not smoke:
            write_json("generation_settings.json", state)
        print("Generated but needs visual review:", target)
    except Exception as exc:
        state.update(status="failed", error=f"{type(exc).__name__}: {exc}", finished_unix=time.time())
        write_json(f"generation_{suffix}_status.json", state)
        if not smoke:
            write_json("generation_settings.json", state)
        raise
    finally:
        monitor_stop.set()


def finalize():
    state = json.loads((HERE / "generation_settings.json").read_text(encoding="utf-8"))
    candidate = Path(state["output"])
    if candidate.resolve().parent != HERE.resolve():
        raise RuntimeError("Candidate path must be in the task folder")
    p = probe(candidate)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    if (v["width"], v["height"]) != (WIDTH, HEIGHT) or int(v.get("nb_frames", 0)) != FRAMES:
        raise RuntimeError("Generated dimensions/frame count differ; inspect alignment first")
    if v["avg_frame_rate"] != "24/1":
        raise RuntimeError("Unexpected generated FPS; do not silently change timing")
    h, w, top, left = source_rect(WIDTH, HEIGHT, 324, 576)
    if (h, w, top, left) != (576, 324, 0, 350):
        raise RuntimeError("Geometry differs; inspect before compositing")
    filters = (
        "[0:v]setpts=PTS-STARTPTS[ai];"
        "[1:v]setpts=PTS-STARTPTS,setparams=colorspace=unknown:range=unspecified[src];"
        "[ai][src]overlay=350:0:shortest=1,setsar=1,format=yuv420p[out]"
    )
    # Restore every central source pixel without blending AI into the product.
    ffmpeg("-i", candidate, "-i", HERE / "control_video.mp4", "-filter_complex", filters,
           "-map", "[out]", "-frames:v", FRAMES, "-an", "-c:v", "libx264", "-crf", "0",
           "-movflags", "+faststart", HERE / "central_restored_lossless.mp4")
    # Use the higher-resolution real clip directly for the final product region.
    # 405x720 is exactly 9:16; the integer placement leaves margins 438/437 pixels.
    final_filters = (
        "[0:v]setpts=PTS-STARTPTS,scale=1280:720:flags=lanczos,format=rgb24[bg];"
        "[1:v]setpts=PTS-STARTPTS,scale=405:720:flags=lanczos,format=rgb24[src];"
        "[bg][src]overlay=438:0:format=rgb:shortest=1,setsar=1,format=gbrp[out]"
    )
    ffmpeg("-i", candidate, "-i", HERE / "source_clip_24fps.mp4",
           "-filter_complex", final_filters, "-map", "[out]", "-frames:v", FRAMES,
           "-an", "-c:v", "libx264rgb", "-crf", "0", "-pix_fmt", "gbrp",
           HERE / "final_source_restored_rgb.mp4")
    ffmpeg("-i", HERE / "final_source_restored_rgb.mp4",
           "-frames:v", FRAMES, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_trc", "bt709",
           "-color_primaries", "bt709", "-color_range", "tv",
           "-movflags", "+faststart", HERE / "kariju_pc_final.mp4")
    ffmpeg("-ss", "3.5", "-i", HERE / "kariju_pc_final.mp4", "-frames:v", "1",
           "-q:v", "2", HERE / "kariju_pc_poster.jpg")
    a = run(["ffmpeg", "-v", "error", "-i", HERE / "central_restored_lossless.mp4", "-vf",
             "crop=324:576:350:0", "-an", "-f", "framemd5", "-"])
    b = run(["ffmpeg", "-v", "error", "-i", HERE / "control_video.mp4", "-an", "-f", "framemd5", "-"])
    def checksums(text):
        return [line.rsplit(",", 1)[-1].strip() for line in text.splitlines() if not line.startswith("#")]
    if checksums(a) != checksums(b):
        raise RuntimeError("Restored central pixels differ from control video")
    highres_a = run(["ffmpeg", "-v", "error", "-i", HERE / "final_source_restored_rgb.mp4", "-vf",
                    "crop=405:720:438:0,format=gbrp", "-an", "-f", "framemd5", "-"])
    highres_b = run(["ffmpeg", "-v", "error", "-i", HERE / "source_clip_24fps.mp4", "-vf",
                    "scale=405:720:flags=lanczos,format=rgb24,format=gbrp", "-an", "-f", "framemd5", "-"])
    if checksums(highres_a) != checksums(highres_b):
        raise RuntimeError("High-resolution source restoration differs from the scaled original")
    final_info = probe(HERE / "kariju_pc_final.mp4")
    if any(s["codec_type"] == "audio" for s in final_info["streams"]):
        raise RuntimeError("Unexpected final audio stream")
    state = json.loads((HERE / "generation_settings.json").read_text(encoding="utf-8"))
    state.update(status="encoded_unreviewed", source_manifest="source_manifest.json",
                 central_pixels_before_web_encode="145/145 frame checksums match control",
                 high_resolution_central_pixels_before_web_encode="145/145 RGB frame checksums match scaled real source",
                 final_source_rect={"x":438,"y":0,"width":405,"height":720},
                 final_probe=final_info, final_bytes=(HERE / "kariju_pc_final.mp4").stat().st_size,
                 final_sha256=digest(HERE / "kariju_pc_final.mp4"),
                 resize_note="1024x576 AI output enlarged to 1280x720; no AI upscaler",
                 visual_review="pending: side continuity, seams, duplicates, bubbling oil, temporal stability")
    write_json("generation_settings.json", state)
    print("Encoded; central pixels verified. Visual review still required.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "check", "download", "smoke", "generate", "refine", "finalize"])
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare": prepare()
    elif args.action == "check":
        _, missing = required_assets()
        print(json.dumps({"missing_assets": len(missing), "missing_bytes": sum(a["bytes"] for a in missing),
                          "generation_attempted_by_this_check": False}, indent=2))
    elif args.action == "download": download(args.approved)
    elif args.action in ("smoke", "generate"): generate(args.action == "smoke")
    elif args.action == "refine": generate(refined=True)
    elif args.action == "finalize": finalize()


if __name__ == "__main__":
    main()

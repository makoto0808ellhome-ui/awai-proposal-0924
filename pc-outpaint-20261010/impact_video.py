"""Encode the approved 1.43x composition, restoring detail from the real source."""
import json
import struct
import pipeline as p


def frame_hashes(path, filters):
    output = p.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", filters,
        "-frames:v", str(p.FRAMES), "-an", "-pix_fmt", "gbrp", "-f", "framemd5", "-"])
    return [line.split(",")[-1].strip() for line in output.splitlines()
            if line.strip() and not line.startswith("#")]


def mp4_atoms(path):
    atoms = []
    with path.open("rb") as file:
        while True:
            header = file.read(8)
            if len(header) != 8:
                break
            length, kind = struct.unpack(">I4s", header)
            if length == 1:
                length = struct.unpack(">Q", file.read(8))[0]
                skip = length - 16
            else:
                skip = length - 8
            atoms.append(kind.decode("ascii"))
            if length == 0:
                break
            file.seek(skip, 1)
    return atoms


def main():
    master = p.HERE / "impact_source_restored_rgb.mp4"
    output = p.HERE / "kariju_pc_impact.mp4"
    filters = (
        "[0:v]crop=896:504:192:90,scale=1280:720:flags=lanczos,format=rgb24[bg];"
        "[1:v]scale=579:1029:flags=lanczos,format=rgb24,crop=579:720:0:129[src];"
        "[bg][src]overlay=351:0:format=rgb[out]"
    )
    p.ffmpeg("-i", p.HERE / "final_source_restored_rgb.mp4",
        "-i", p.HERE / "source_clip_24fps.mp4", "-filter_complex", filters,
        "-map", "[out]", "-frames:v", p.FRAMES, "-an", "-c:v", "libx264rgb",
        "-preset", "veryfast", "-crf", "0", "-pix_fmt", "gbrp", master)
    actual = frame_hashes(master, "format=rgb24,crop=579:720:351:0,format=gbrp")
    expected = frame_hashes(p.HERE / "source_clip_24fps.mp4",
        "scale=579:1029:flags=lanczos,format=rgb24,crop=579:720:0:129,format=gbrp")
    assert len(actual) == len(expected) == p.FRAMES and actual == expected, "Real-source integrity failed"
    p.ffmpeg("-i", master, "-vf",
        "scale=1280:720:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-frames:v", p.FRAMES, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_trc", "bt709",
        "-color_primaries", "bt709", "-color_range", "tv", "-movflags", "+faststart", output)
    p.ffmpeg("-ss", "5.5", "-i", output, "-frames:v", "1", "-q:v", "2",
        p.HERE / "kariju_pc_impact_poster.jpg")
    p.ffmpeg("-i", output, "-vf", "fps=2,scale=640:360,tile=3x4", "-frames:v", "1",
        p.HERE / "impact-final-contact-sheet.jpg")
    probe = p.probe(output)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], video["nb_frames"], video["avg_frame_rate"],
        video["codec_name"], video["pix_fmt"]) == (1280, 720, "145", "24/1", "h264", "yuv420p")
    assert not any(s["codec_type"] == "audio" for s in probe["streams"])
    atoms = mp4_atoms(output)
    assert atoms.index("moov") < atoms.index("mdat")
    state = {
        "filename": output.name, "status": "encoded_unreviewed", "approved_by_user": True,
        "zoom_factor": 1280 / 896, "crop": {"x": 192, "y": 90, "width": 896, "height": 504},
        "source": "final_source_restored_rgb.mp4", "ai_regenerated": False,
        "real_source_restoration": {"source": "source_clip_24fps.mp4", "scale": [579, 1029],
            "crop": {"x": 0, "y": 129, "width": 579, "height": 720}, "overlay": [351, 0],
            "integrity": {"checked_frames": len(actual), "matched_frames": len(actual),
                "method": "Independent RGB frame MD5 comparison before lossy Web encoding"}},
        "filter_complex": filters, "poster_seconds": 5.5,
        "encoding": {"codec": "libx264", "preset": "slow", "crf": 20, "pixel_format": "yuv420p",
            "colorspace": "bt709", "faststart": True, "audio": False},
        "mp4_atoms": atoms, "bytes": output.stat().st_size, "sha256": p.digest(output), "output_probe": probe}
    p.write_json("impact_settings.json", state)
    print(json.dumps({"zoom": state["zoom_factor"], "bytes": state["bytes"], "source_frames_matched": len(actual)}))


if __name__ == "__main__":
    main()

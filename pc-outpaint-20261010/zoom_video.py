"""Create a fixed 1.194x zoom from the restored real-source RGB master."""
import json
import pipeline as p

def main():
    output = p.HERE / "kariju_pc_zoom.mp4"
    p.ffmpeg("-i", p.HERE / "final_source_restored_rgb.mp4", "-vf",
        "crop=1072:603:104:58,scale=1280:720:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-frames:v", p.FRAMES, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_trc", "bt709",
        "-color_primaries", "bt709", "-color_range", "tv", "-movflags", "+faststart", output)
    p.ffmpeg("-ss", "3.5", "-i", output, "-frames:v", "1", "-q:v", "2",
             p.HERE / "kariju_pc_zoom_poster.jpg")
    p.ffmpeg("-i", output, "-vf", "fps=2,scale=640:360,tile=3x4", "-frames:v", "1",
             p.HERE / "zoom-contact-sheet.jpg")
    probe = p.probe(output)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], video["nb_frames"], video["avg_frame_rate"]) == (1280,720,"145","24/1")
    assert not any(s["codec_type"] == "audio" for s in probe["streams"])
    state = {"filename":output.name, "status":"encoded_unreviewed", "zoom_factor":1280/1072,
        "crop":{"x":104,"y":58,"width":1072,"height":603},
        "source":"final_source_restored_rgb.mp4", "ai_regenerated":False,
        "encoding":{"codec":"libx264","preset":"slow","crf":20,"pixel_format":"yuv420p","colorspace":"bt709","faststart":True,"audio":False},
        "bytes":output.stat().st_size,"sha256":p.digest(output),"output_probe":probe}
    p.write_json("zoom_settings.json",state)
    print(json.dumps({"zoom":state["zoom_factor"],"bytes":state["bytes"]}))

if __name__ == "__main__":
    main()

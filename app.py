import os
import json
import uuid
import subprocess
import threading
import re
import sys
import shutil
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    Response,
    stream_with_context,
)

app = Flask(__name__)
app.config["DOWNLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloads"
)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

os.makedirs(app.config["DOWNLOAD_FOLDER"], exist_ok=True)

download_progress = {}

YT_DLP_EXE = "yt-dlp"


def check_ffmpeg():
    local_ffmpeg = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "bin", "ffmpeg", "bin", "ffmpeg.exe"
    )
    if os.path.exists(local_ffmpeg):
        return True
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_location():
    local_ffmpeg_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "bin", "ffmpeg", "bin"
    )
    if os.path.exists(os.path.join(local_ffmpeg_dir, "ffmpeg.exe")):
        return local_ffmpeg_dir
    return None


def check_ytdlp():
    return shutil.which("yt-dlp") is not None


def format_duration(seconds):
    if seconds is None:
        return "Unknown"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def sanitize_filename(title):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, "")
    title = title.strip()
    if len(title) > 100:
        title = title[:100]
    return title


def get_video_info_cli(url):
    cmd = [YT_DLP_EXE, "--dump-json", "--no-download", "--no-playlist", "-q", url]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                info = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip():
                        try:
                            info = json.loads(line)
                            break
                        except:
                            continue
                else:
                    return {"error": "Failed to parse video info"}

            formats = []
            for f in info.get("formats", []):
                if f.get("ext") in ["mp4", "webm", "m4a"]:
                    height = f.get("height", 0) or 0
                    formats.append(
                        {
                            "format_id": f.get("format_id"),
                            "ext": f.get("ext"),
                            "resolution": f.get("resolution")
                            or (
                                str(f.get("height", "")) + "p"
                                if f.get("height")
                                else "audio"
                            ),
                            "height": height,
                            "filesize": f.get("filesize")
                            or f.get("filesize_approx", 0),
                            "vcodec": f.get("vcodec", "none"),
                            "acodec": f.get("acodec", "none"),
                        }
                    )

            formats.sort(key=lambda x: x.get("height", 0), reverse=True)

            unique_formats = []
            seen_res = set()
            for f in formats:
                res = f.get("resolution", "")
                if res not in seen_res:
                    seen_res.add(res)
                    unique_formats.append(f)

            return {
                "type": "video",
                "id": info.get("id"),
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": format_duration(info.get("duration")),
                "formats": unique_formats[:20],
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
            }
        else:
            error_msg = result.stderr or "Failed to fetch video info"
            return {"error": error_msg}

    except subprocess.TimeoutExpired:
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        return {"error": str(e)}


def get_playlist_info_cli(url):
    cmd = [YT_DLP_EXE, "--dump-json", "--no-download", "--yes-playlist", "-q", url]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            return get_video_info_cli(url)

        lines = result.stdout.strip().split("\n")
        entries = []

        for line in lines:
            if line.strip():
                try:
                    entry = json.loads(line)
                    entries.append(
                        {
                            "id": entry.get("id"),
                            "title": entry.get("title"),
                            "thumbnail": entry.get("thumbnail"),
                            "duration": format_duration(entry.get("duration")),
                        }
                    )
                except:
                    continue

        if not entries:
            return get_video_info_cli(url)

        return {
            "type": "playlist",
            "title": f"Playlist ({len(entries)} videos)",
            "videos": entries,
        }

    except Exception as e:
        return get_video_info_cli(url)


def get_video_info(url):
    url = url.strip()

    if "watch?v=" in url:
        import urllib.parse

        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        video_id = parsed.get("v", [None])[0]
        list_id = parsed.get("list", [None])[0]

        if video_id and list_id:
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
            return get_video_info_cli(clean_url)

    if "playlist" in url.lower() or "list=" in url.lower():
        return get_playlist_info_cli(url)

    return get_video_info_cli(url)


def parse_progress(line, task_id):
    if task_id not in download_progress:
        return

    progress_match = re.search(r"(\d+\.?\d*)%", line)
    if progress_match:
        try:
            percent = float(progress_match.group(1))
            download_progress[task_id]["progress"] = int(percent)
        except:
            pass

    speed_match = re.search(r"of\s+([\d.]+\w+)\s+at\s+([\d.]+\w+/s)", line)
    if speed_match:
        download_progress[task_id]["downloaded"] = speed_match.group(1)
        download_progress[task_id]["speed"] = speed_match.group(2)

    if "Destination:" in line:
        download_progress[task_id]["status"] = "processing"

    if "Merging formats into" in line:
        download_progress[task_id]["status"] = "merging"

    if "Postprocessing" in line:
        download_progress[task_id]["status"] = "postprocessing"


def download_video(url, format_id, task_id, audio_only=False):
    if not check_ffmpeg():
        download_progress[task_id] = {
            "status": "error",
            "progress": 0,
            "filename": None,
            "error": "FFmpeg is not installed. Please install FFmpeg to process videos. Visit: https://ffmpeg.org/download.html",
        }
        return

    try:
        download_progress[task_id] = {
            "status": "downloading",
            "progress": 0,
            "filename": None,
            "speed": "0",
        }

        # Add FFmpeg to PATH for DLL loading
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            os.environ["PATH"] = ffmpeg_loc + os.pathsep + os.environ.get("PATH", "")

        # Get video title for filename
        video_title = task_id
        try:
            info_cmd = [
                YT_DLP_EXE,
                "--dump-json",
                "--no-download",
                "--no-playlist",
                "-q",
                url,
            ]
            result = subprocess.run(
                info_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    info = json.loads(result.stdout.strip())
                    video_title = sanitize_filename(info.get("title", task_id))
                except:
                    pass
        except:
            pass

        output_path = os.path.join(app.config["DOWNLOAD_FOLDER"], video_title)

        ffmpeg_arg = ["--ffmpeg-location", ffmpeg_loc] if ffmpeg_loc else []

        if audio_only:
            cmd = (
                [
                    YT_DLP_EXE,
                    "--format",
                    "bestaudio/best",
                    "--output",
                    output_path + ".%(ext)s",
                    "--extract-audio",
                    "--audio-format",
                    "mp3",
                    "--audio-quality",
                    "0",
                    "--no-playlist",
                    "-q",
                ]
                + ffmpeg_arg
                + [url]
            )
        else:
            if format_id == "best":
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                fmt = f"{format_id}+bestaudio[ext=m4a]/bestvideo[ext=webm]+bestaudio/best[ext=mp4]/best"

            cmd = (
                [
                    YT_DLP_EXE,
                    "--format",
                    fmt,
                    "--output",
                    output_path + ".%(ext)s",
                    "--merge-output-format",
                    "mp4",
                    "--no-playlist",
                    "-q",
                ]
                + ffmpeg_arg
                + [url]
            )

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        stderr_stream = process.stderr

        if stderr_stream:
            stderr_lines = []
            while True:
                char = stderr_stream.read(1)
                if not char:
                    if process.poll() is not None:
                        break
                    continue

                if char == "\r" or char == "\n":
                    line = "".join(stderr_lines).strip()
                    if line:
                        parse_progress(line, task_id)
                    stderr_lines = []
                else:
                    stderr_lines.append(char)

        process.wait()

        if process.returncode != 0:
            stdout, stderr = process.communicate()
            error_msg = stderr or "Download failed"
            if "ERROR" in error_msg:
                download_progress[task_id]["status"] = "error"
                download_progress[task_id]["error"] = error_msg
            else:
                download_progress[task_id]["status"] = "error"
                download_progress[task_id]["error"] = (
                    f"Download failed with code {process.returncode}"
                )
            return

        output_file = None
        for ext in [".mp3", ".mp4", ".mkv", ".webm", ".m4a"]:
            potential_file = output_path + ext
            if os.path.exists(potential_file):
                output_file = potential_file
                break

        if output_file and os.path.exists(output_file):
            filename = os.path.basename(output_file)
            download_progress[task_id]["status"] = "completed"
            download_progress[task_id]["filename"] = filename
            download_progress[task_id]["progress"] = 100
        else:
            download_progress[task_id]["status"] = "error"
            download_progress[task_id]["error"] = "Output file not found"

    except subprocess.TimeoutExpired:
        download_progress[task_id]["status"] = "error"
        download_progress[task_id]["error"] = "Download timed out"
    except Exception as e:
        download_progress[task_id]["status"] = "error"
        download_progress[task_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    if not check_ytdlp():
        return jsonify(
            {"error": "yt-dlp is not installed. Please run: pip install yt-dlp"}
        ), 400

    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    info = get_video_info(url)

    if "error" in info:
        return jsonify(info), 400

    return jsonify(info)


@app.route("/api/download", methods=["POST"])
def start_download():
    if not check_ytdlp():
        return jsonify(
            {"error": "yt-dlp is not installed. Please run: pip install yt-dlp"}
        ), 400

    data = request.get_json()
    url = data.get("url", "").strip()
    format_id = data.get("format_id", "best")
    audio_only = data.get("audio_only", False)

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    task_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=download_video, args=(url, format_id, task_id, audio_only)
    )
    thread.start()

    return jsonify({"task_id": task_id, "message": "Download started"})


@app.route("/api/progress/<task_id>")
def get_progress(task_id):
    def generate():
        checked_statuses = set()
        while True:
            if task_id in download_progress:
                progress = download_progress[task_id]
                yield f"data: {json.dumps(progress)}\n\n"
                if progress["status"] in ["completed", "error"]:
                    break
                status = progress.get("status", "")
                if status in checked_statuses and progress.get("progress", 0) == 100:
                    break
                checked_statuses.add(status)
            else:
                yield f"data: {json.dumps({'status': 'unknown'})}\n\n"
                break
            import time

            time.sleep(0.5)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/download/<task_id>")
def download_file(task_id):
    if task_id in download_progress:
        info = download_progress[task_id]
        if info["status"] == "completed" and info.get("filename"):
            filepath = os.path.join(app.config["DOWNLOAD_FOLDER"], info["filename"])
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)

    return "File not found", 404


@app.route("/api/cleanup/<task_id>", methods=["POST"])
def cleanup(task_id):
    if task_id in download_progress:
        info = download_progress[task_id]
        if info.get("filename"):
            filepath = os.path.join(app.config["DOWNLOAD_FOLDER"], info["filename"])
            if os.path.exists(filepath):
                os.remove(filepath)
        del download_progress[task_id]
        return jsonify({"message": "Cleaned up"})
    return jsonify({"error": "Task not found"}), 404


@app.route("/api/check", methods=["GET"])
def check_tools():
    ffmpeg_ok = check_ffmpeg()
    ytdlp_ok = check_ytdlp()

    return jsonify(
        {
            "ffmpeg": ffmpeg_ok,
            "yt-dlp": ytdlp_ok,
            "message": "All tools ready"
            if (ffmpeg_ok and ytdlp_ok)
            else "Some tools are missing",
        }
    )


if __name__ == "__main__":
    print("=" * 50)
    print("  Zen Downloader - Starting Server")
    print("  Open: http://localhost:5000")
    print("=" * 50)

    ffmpeg_ok = check_ffmpeg()
    ytdlp_ok = check_ytdlp()

    if not ffmpeg_ok:
        print("\n  WARNING: FFmpeg not found!")
        print("  Please install FFmpeg to process videos:")
        print("  - Windows: choco install ffmpeg")
        print("  - Or download from: https://ffmpeg.org/download.html")

    if not ytdlp_ok:
        print("\n  WARNING: yt-dlp not found!")
        print("  Please install: pip install yt-dlp")

    if ffmpeg_ok and ytdlp_ok:
        print("\n  All tools ready! ✓")

    print("=" * 50)

    app.run(debug=True, host="0.0.0.0", port=5000)

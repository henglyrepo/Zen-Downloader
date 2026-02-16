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
download_queue = []
discover_tasks = {}
app_settings = {
    "concurrent_downloads": 1,
    "default_quality": "best",
    "default_format": "mp4",
}

YT_DLP_EXE = "yt-dlp"
queue_lock = threading.Lock()
processing_queue = False


def get_default_download_path():
    if sys.platform == "win32":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads")


def get_download_folder():
    return app.config["DOWNLOAD_FOLDER"]


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

    playlist_match = re.search(r"\[download\]\s+(\d+)\s+of\s+(\d+)", line)
    if playlist_match:
        current = int(playlist_match.group(1))
        total = int(playlist_match.group(2))
        download_progress[task_id]["current_video"] = current
        download_progress[task_id]["total_videos"] = total


def download_video(url, format_id, task_id, audio_only=False, download_path=None):
    if download_path is None:
        download_path = app.config["DOWNLOAD_FOLDER"]
    
    os.makedirs(download_path, exist_ok=True)
    
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

        output_path = os.path.join(download_path, video_title)

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
            
            with queue_lock:
                for item in download_queue:
                    if item.get("task_id") == task_id:
                        item["status"] = "completed"
                        break
            
            threading.Thread(target=process_queue, daemon=True).start()
        else:
            download_progress[task_id]["status"] = "error"
            download_progress[task_id]["error"] = "Output file not found"
            
            with queue_lock:
                for item in download_queue:
                    if item.get("task_id") == task_id:
                        item["status"] = "error"
                        break
            
            threading.Thread(target=process_queue, daemon=True).start()

    except subprocess.TimeoutExpired:
        download_progress[task_id]["status"] = "error"
        download_progress[task_id]["error"] = "Download timed out"
        
        with queue_lock:
            for item in download_queue:
                if item.get("task_id") == task_id:
                    item["status"] = "error"
                    break
        
        threading.Thread(target=process_queue, daemon=True).start()
        
    except Exception as e:
        download_progress[task_id]["status"] = "error"
        download_progress[task_id]["error"] = str(e)
        
        with queue_lock:
            for item in download_queue:
                if item.get("task_id") == task_id:
                    item["status"] = "error"
                    break
        
        threading.Thread(target=process_queue, daemon=True).start()


def download_playlist(url, format_id, task_id, audio_only=False, download_path=None, concurrent=3):
    if download_path is None:
        download_path = app.config["DOWNLOAD_FOLDER"]
    
    os.makedirs(download_path, exist_ok=True)

    if not check_ffmpeg():
        download_progress[task_id] = {
            "status": "error",
            "progress": 0,
            "filename": None,
            "error": "FFmpeg is not installed. Please install FFmpeg to process videos.",
        }
        return

    try:
        download_progress[task_id] = {
            "status": "downloading",
            "progress": 0,
            "filename": None,
            "speed": "0",
            "current_video": 0,
            "total_videos": 0,
        }

        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            os.environ["PATH"] = ffmpeg_loc + os.pathsep + os.environ.get("PATH", "")

        playlist_title = "playlist"
        try:
            info_cmd = [YT_DLP_EXE, "--dump-json", "--no-download", "--flat-playlist", "-q", url]
            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                count = sum(1 for line in lines if line.strip())
                download_progress[task_id]["total_videos"] = count
                if count > 0:
                    try:
                        first = json.loads(lines[0])
                        playlist_title = sanitize_filename(first.get("playlist_title", "playlist"))
                    except:
                        pass
        except:
            pass

        output_template = os.path.join(download_path, playlist_title, "%(title)s.%(ext)s")
        
        ffmpeg_arg = ["--ffmpeg-location", ffmpeg_loc] if ffmpeg_loc else []

        if audio_only:
            cmd = [
                YT_DLP_EXE,
                "--format", "bestaudio/best",
                "--output", output_template,
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--yes-playlist",
                "-q",
            ] + ffmpeg_arg + [url]
        else:
            if format_id == "best":
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                fmt = f"{format_id}+bestaudio[ext=m4a]/bestvideo[ext=webm]+bestaudio/best[ext=mp4]/best"

            cmd = [
                YT_DLP_EXE,
                "--format", fmt,
                "--output", output_template,
                "--merge-output-format", "mp4",
                "--yes-playlist",
                "-q",
            ] + ffmpeg_arg + [url]

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
            download_progress[task_id]["status"] = "error"
            download_progress[task_id]["error"] = f"Playlist download failed with code {process.returncode}"
            return

        download_progress[task_id]["status"] = "completed"
        download_progress[task_id]["progress"] = 100
        download_progress[task_id]["filename"] = f"Playlist: {playlist_title}"

    except Exception as e:
        download_progress[task_id]["status"] = "error"
        download_progress[task_id]["error"] = str(e)


def process_queue():
    global processing_queue
    with queue_lock:
        if processing_queue:
            return
        processing_queue = True
    
    while True:
        with queue_lock:
            active_count = sum(1 for item in download_queue if item.get("status") == "downloading")
            available_slots = app_settings["concurrent_downloads"] - active_count
            
            if available_slots <= 0:
                break
            
            pending_items = [item for item in download_queue if item.get("status") == "pending"]
            if not pending_items:
                break
            
            items_to_process = pending_items[:available_slots]
        
        for item in items_to_process:
            item["status"] = "downloading"
            item["started_at"] = str(uuid.uuid4())
            
            thread = threading.Thread(
                target=download_video,
                args=(
                    item["url"],
                    item["format_id"],
                    item["task_id"],
                    item.get("audio_only", False),
                    item.get("download_path", app.config["DOWNLOAD_FOLDER"])
                )
            )
            thread.start()
    
    with queue_lock:
        active = sum(1 for item in download_queue if item.get("status") == "downloading")
        if active == 0:
            processing_queue = False


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


@app.route("/api/discover", methods=["POST"])
def start_discover():
    if not check_ytdlp():
        return jsonify(
            {"error": "yt-dlp is not installed. Please run: pip install yt-dlp"}
        ), 400

    data = request.get_json()
    url = data.get("url", "").strip()
    max_videos = data.get("max_videos", 50)

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    task_id = str(uuid.uuid4())
    
    # Store discover task
    discover_tasks[task_id] = {
        "url": url,
        "max_videos": max_videos,
        "videos": [],
        "status": "running"
    }

    # Start discovery in background thread
    thread = threading.Thread(
        target=discover_videos,
        args=(url, max_videos, task_id)
    )
    thread.start()

    return jsonify({"task_id": task_id, "message": "Discovery started"})


def discover_videos(url, max_videos, task_id):
    try:
        ffmpeg_loc = get_ffmpeg_location()
        ffmpeg_arg = ["--ffmpeg-location", ffmpeg_loc] if ffmpeg_loc else []

        cmd = [
            YT_DLP_EXE,
            "--dump-json",
            "--yes-playlist",
            "--playlist-end", str(max_videos),
            "-q",
        ] + ffmpeg_arg + [url]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            if task_id not in discover_tasks:
                process.terminate()
                break
            
            try:
                entry = json.loads(line.strip())
                video_info = {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "thumbnail": entry.get("thumbnail"),
                    "duration": format_duration(entry.get("duration")),
                    "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                }
                
                with queue_lock:
                    if task_id in discover_tasks:
                        discover_tasks[task_id]["videos"].append(video_info)
                        
            except:
                continue

        process.wait()
        
        with queue_lock:
            if task_id in discover_tasks:
                discover_tasks[task_id]["status"] = "completed"

    except Exception as e:
        with queue_lock:
            if task_id in discover_tasks:
                discover_tasks[task_id]["status"] = "error"
                discover_tasks[task_id]["error"] = str(e)


@app.route("/api/discover/<task_id>")
def stream_discover(task_id):
    def generate():
        checked_indices = set()
        while True:
            with queue_lock:
                if task_id not in discover_tasks:
                    yield f"data: {json.dumps({'status': 'error', 'error': 'Task not found'})}\n\n"
                    break
                
                task = discover_tasks[task_id]
                videos = task.get("videos", [])
                status = task.get("status", "running")
                
                # Send new videos
                for i, video in enumerate(videos):
                    if i not in checked_indices:
                        checked_indices.add(i)
                        yield f"data: {json.dumps({'type': 'video', 'video': video, 'count': len(videos), 'status': status})}\n\n"
                
                if status == "completed":
                    yield f"data: {json.dumps({'status': 'completed', 'count': len(videos)})}\n\n"
                    break
                
                if status == "error":
                    yield f"data: {json.dumps({'status': 'error', 'error': task.get('error', 'Unknown error')})}\n\n"
                    break

            import time
            time.sleep(0.5)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


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
    download_path = data.get("download_path", app.config["DOWNLOAD_FOLDER"])
    playlist_mode = data.get("playlist_mode", False)

    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    task_id = str(uuid.uuid4())

    if playlist_mode or "playlist" in url.lower() or "list=" in url.lower() or "/channel/" in url.lower() or "/@" in url.lower():
        thread = threading.Thread(
            target=download_playlist, 
            args=(url, format_id, task_id, audio_only, download_path)
        )
    else:
        thread = threading.Thread(
            target=download_video, 
            args=(url, format_id, task_id, audio_only, download_path)
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


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify({
        "download_path": get_default_download_path(),
        "app_download_path": app.config["DOWNLOAD_FOLDER"],
        "concurrent_downloads": app_settings["concurrent_downloads"],
        "default_quality": app_settings["default_quality"],
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json()
    if "concurrent_downloads" in data:
        app_settings["concurrent_downloads"] = max(1, min(5, int(data["concurrent_downloads"])))
    if "default_quality" in data:
        app_settings["default_quality"] = data["default_quality"]
    return jsonify({"message": "Settings updated", "settings": app_settings})


@app.route("/api/queue", methods=["GET"])
def get_queue():
    queue_data = []
    for item in download_queue:
        task_id = item.get("task_id")
        progress = download_progress.get(task_id, {}) if task_id else {}
        queue_data.append({
            "id": item.get("task_id"),
            "url": item.get("url"),
            "title": item.get("title", "Unknown"),
            "status": item.get("status", "pending"),
            "progress": progress.get("progress", 0),
            "speed": progress.get("speed", ""),
            "filename": progress.get("filename", ""),
            "error": progress.get("error", ""),
            "added_at": item.get("added_at", ""),
        })
    return jsonify({
        "queue": queue_data,
        "settings": app_settings,
        "total": len(queue_data),
        "pending": sum(1 for q in queue_data if q["status"] == "pending"),
        "downloading": sum(1 for q in queue_data if q["status"] == "downloading"),
        "completed": sum(1 for q in queue_data if q["status"] == "completed"),
        "failed": sum(1 for q in queue_data if q["status"] == "error"),
    })


@app.route("/api/queue", methods=["POST"])
def add_to_queue():
    data = request.get_json()
    url = data.get("url", "").strip()
    format_id = data.get("format_id", "best")
    audio_only = data.get("audio_only", False)
    download_path = data.get("download_path", app.config["DOWNLOAD_FOLDER"])
    title = data.get("title", "Video")
    
    if not url:
        return jsonify({"error": "Please enter a URL"}), 400
    
    task_id = str(uuid.uuid4())
    
    queue_item = {
        "task_id": task_id,
        "url": url,
        "format_id": format_id,
        "audio_only": audio_only,
        "download_path": download_path,
        "title": title,
        "status": "pending",
        "added_at": str(uuid.uuid4()),
    }
    
    with queue_lock:
        download_queue.append(queue_item)
        download_progress[task_id] = {
            "status": "pending",
            "progress": 0,
            "filename": None,
            "speed": "",
            "title": title,
        }
    
    return jsonify({
        "task_id": task_id,
        "message": "Added to queue",
        "queue_position": len(download_queue)
    })


@app.route("/api/queue/start", methods=["POST"])
def start_queue():
    threading.Thread(target=process_queue, daemon=True).start()
    return jsonify({"message": "Queue processing started"})


@app.route("/api/queue/<task_id>", methods=["DELETE"])
def remove_from_queue(task_id):
    with queue_lock:
        for i, item in enumerate(download_queue):
            if item.get("task_id") == task_id:
                if item.get("status") == "downloading":
                    return jsonify({"error": "Cannot remove downloading item"}), 400
                download_queue.pop(i)
                if task_id in download_progress:
                    del download_progress[task_id]
                return jsonify({"message": "Removed from queue"})
    return jsonify({"error": "Item not found"}), 404


@app.route("/api/queue/clear", methods=["POST"])
def clear_queue():
    data = request.get_json()
    clear_type = data.get("type", "completed")
    
    with queue_lock:
        if clear_type == "all":
            download_queue.clear()
            download_progress.clear()
        elif clear_type == "completed":
            download_queue[:] = [item for item in download_queue if item.get("status") != "completed"]
        elif clear_type == "failed":
            download_queue[:] = [item for item in download_queue if item.get("status") != "error"]
    
    return jsonify({"message": f"Cleared {clear_type} items from queue"})


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
  
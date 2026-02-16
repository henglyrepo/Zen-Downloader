# Zen Downloader

<p align="center">
  <img src="https://img.shields.io/github/stars/henglyrepo/Zen-Downloader?style=social" alt="Stars">
  <img src="https://img.shields.io/github/forks/henglyrepo/Zen-Downloader?style=social" alt="Forks">
  <img src="https://img.shields.io/github/downloads/henglyrepo/Zen-Downloader/total" alt="Downloads">
  <img src="https://img.shields.io/badge/Zen-Downloader-v2.2.0-ff0050" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

<p align="center">
  A modern, feature-rich multi-platform video downloader with a beautiful web interface. Download videos in up to 4K quality, extract audio as MP3, or grab entire playlists with just one click.
</p>

<p align="center">
  <a href="#screenshots">View Demo</a> •
  <a href="#features">Features</a> •
  <a href="#quick-start">Get Started</a> •
  <a href="#faq">FAQ</a> •
  <a href="#contributing">Contribute</a>
</p>

---

## Screenshots

![Zen Downloader UI](image.png)

---

## Why Use Zen Downloader?

| Feature | Benefit |
|---------|---------|
| 🖥️ **Web Interface** | No command line needed - use your browser |
| ⚡ **One-Click Setup** | Just run `run.bat` - everything auto-configures |
| 🎬 **Up to 4K Quality** | Download videos in the highest available resolution |
| 🎵 **MP3 Extraction** | Convert videos to high-quality audio |
| 📺 **Playlist Support** | Download entire channels or playlists at once |
| 📋 **Download Queue** | Queue multiple downloads and manage in one place |
| 🔍 **Video Discovery** | Discover channel videos before downloading |
| 📂 **Custom Path** | Save files to any folder you choose |
| 🔄 **Auto Updates** | yt-dlp updates automatically |
| 🌐 **Cross-Platform** | Works on Windows, macOS, and Linux |

---

## Features

- ✅ **Video Download** - Download videos from 1700+ sites in up to 4K quality
- ✅ **Multi-Platform Support** - YouTube, TikTok, Facebook, Instagram, Twitter, and more
- ✅ **Audio Extraction** - Extract audio as high-quality MP3
- ✅ **Quality Selection** - Choose from 144p to 4K resolution
- ✅ **Real-time Progress** - Live download progress with speed indicator
- ✅ **Download Queue** - Queue multiple downloads and manage them in one place
- ✅ **Channel/Playlist Discovery** - Discover videos progressively before downloading
- ✅ **Custom Download Path** - Choose where to save your files
- ✅ **Concurrent Downloads** - Download multiple videos simultaneously (1-5)
- ✅ **Modern UI** - Sleek, responsive dark theme interface
- ✅ **Auto Tool Check** - Automatically detects if FFmpeg and yt-dlp are installed
- ✅ **One-Click Run** - Just double-click `run.bat` to start

---

## Supported Platforms

Zen Downloader supports **1700+ websites** including:

| Platform | Website |
|----------|---------|
| 🎬 YouTube | youtube.com, youtu.be |
| 🎵 TikTok | tiktok.com |
| 📘 Facebook | facebook.com, fb.watch |
| 📸 Instagram | instagram.com |
| 🐦 Twitter/X | twitter.com, x.com |
| 👽 Reddit | reddit.com |
| 🎥 Vimeo | vimeo.com |
| 📺 Dailymotion | dailymotion.com |
| 🎮 Twitch | twitch.tv |
| 📌 Pinterest | pinterest.com |

Plus 1700+ more! [View full list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## Download Queue

Zen Downloader features a powerful queue system for managing multiple downloads:

- 📋 **Queue Panel** - View all pending, downloading, and completed downloads
- ⚙️ **Concurrent Downloads** - Download up to 5 videos simultaneously
- 🎛️ **Queue Controls** - Start queue, clear completed, remove individual items
- 📊 **Real-time Progress** - See live progress for each download
- 🔄 **Auto-retry** - Failed downloads can be retried easily

### Progressive Video Discovery

For channels and playlists, use the **Discover** feature to:

- 🔍 **Find Videos** - Discover videos progressively as they're found
- 📝 **Select Videos** - Choose which videos to download with checkboxes
- 🎯 **Set Limits** - Limit how many videos to discover (1-500)
- ⏩ **Real-time List** - Videos appear in the list as they're discovered

---

## Quick Start

### Windows (Recommended)

```batch
:: Just double-click run.bat - that's it!
run.bat
```

The `run.bat` will automatically:
- ✓ Check if Python, FFmpeg, and dependencies are installed
- ✓ Run setup.bat if anything is missing
- ✓ Start the server
- ✓ Open your browser to the app

### macOS / Linux

```bash
# Install FFmpeg
# macOS:
brew install ffmpeg
# Linux (Ubuntu/Debian):
sudo apt install ffmpeg

# Install dependencies
pip install -r requirements.txt
pip install -U yt-dlp

# Run the server
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Usage Guide

### For Single Videos

1. **Open the app** - Browser opens to http://localhost:5000
2. **Paste URL** - Paste any supported video URL
3. **Get Info** - Click to fetch video details
4. **Select Quality** - Choose your preferred resolution (144p to 4K)
5. **Add to Queue** - Click "Add to Queue" to add to download queue
6. **Start** - Go to Queue panel and click "Start"

### For Playlists & Channels

1. **Paste URL** - Paste playlist or channel URL
2. **Discover** - Click "Discover Videos" to find all videos
3. **Select Videos** - Check the videos you want to download
4. **Configure** - Set quality and MP3 options
5. **Add to Queue** - Click "Add Selected to Queue"
6. **Start** - Go to Queue panel and click "Start"

### Download Options

| Option | Description |
|--------|-------------|
| **Video Quality** | Select from available resolutions or "Best Quality" |
| **MP3 Mode** | Check "Download as MP3" to extract audio only |
| **Download Path** | Choose where to save your files |
| **Max Videos** | Limit how many videos to discover (for playlists) |
| **Concurrent Downloads** | Download multiple videos at once (1-5) |

---

## FAQ

### Q: Is this legal?
A: This tool is for educational purposes. Please respect YouTube's Terms of Service and only download content you have the right to download.

### Q: Why is the video muted/no audio?
A: Make sure FFmpeg is installed. The app automatically merges video and audio tracks. If issues persist, try selecting a different quality or use "Best" quality option.

### Q: How do I update yt-dlp?
A: Run `pip install -U yt-dlp` or simply run `setup.bat` again.

### Q: Can I download private videos?
A: No, this tool only works with publicly available YouTube videos.

### Q: Does it work with other video sites?
A: Yes! yt-dlp supports 1700+ websites. Check [supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

### Q: Where do downloaded files go?
A: Files are downloaded to your browser's default download folder.

---

## Troubleshooting

### "FFmpeg is not installed" Error
Just run `run.bat` - it will automatically install FFmpeg if needed.

**Manual Install:**
```batch
# Windows (with Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### YouTube blocked / No video found
- Ensure the URL is correct
- Try updating yt-dlp: `pip install -U yt-dlp`
- Some videos may be region-locked or private

### Port 5000 already in use
```bash
# Edit app.py to change port=5000 to port=8080
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main page |
| GET | `/api/check` | Check if FFmpeg and yt-dlp are installed |
| POST | `/api/info` | Get video/channel metadata |
| POST | `/api/download` | Start download |
| GET | `/api/progress/<task_id>` | Stream download progress |
| GET | `/download/<task_id>` | Serve downloaded file |
| POST | `/api/cleanup/<task_id>` | Cleanup temp files |

---

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 💻 Submit code improvements

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| [Flask](https://flask.palletsprojects.com/) | Web framework |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Video downloading |
| [Tailwind CSS](https://tailwindcss.com/) | Modern styling |
| [FFmpeg](https://ffmpeg.org/) | Media processing |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and only download content that you have the right to download. The developers are not responsible for any misuse of this software.

---

<p align="center">
  <strong>Star ⭐ this repo if you find it useful!</strong><br>
  Made with ❤️ by <a href="https://github.com/henglyrepo">Zen Downloader Team</a>
</p>

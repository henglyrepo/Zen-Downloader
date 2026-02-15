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
  A modern, feature-rich YouTube video downloader with a beautiful web interface. Download videos in up to 4K quality, extract audio as MP3, or grab entire playlists with just one click.
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
| 🔄 **Auto Updates** | yt-dlp updates automatically |
| 🌐 **Cross-Platform** | Works on Windows, macOS, and Linux |

---

## Features

- ✅ **Video Download** - Download YouTube videos in up to 4K quality
- ✅ **Channel/Playlist Support** - Download entire YouTube channels or playlists
- ✅ **Audio Extraction** - Extract audio as high-quality MP3
- ✅ **Quality Selection** - Choose from 144p to 4K resolution
- ✅ **Real-time Progress** - Live download progress with speed indicator
- ✅ **Modern UI** - Sleek, responsive dark theme interface
- ✅ **Auto Tool Check** - Automatically detects if FFmpeg and yt-dlp are installed
- ✅ **One-Click Run** - Just double-click `run.bat` to start

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

1. **Open the app** - Browser opens to http://localhost:5000
2. **Paste URL** - Paste any YouTube video or playlist URL
3. **Select Quality** - Choose your preferred resolution (144p to 4K)
4. **Download** - Click "Download Now" - file downloads automatically!

### Download Options

| Option | Description |
|--------|-------------|
| **Video Quality** | Select from available resolutions |
| **MP3 Mode** | Check "Download as MP3" to extract audio only |
| **Best Quality** | Select "best" for highest available quality |

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

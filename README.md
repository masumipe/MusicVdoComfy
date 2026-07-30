# MusicVDO Comfy - AI Music Video Generation Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive, automated pipeline for generating AI-powered music videos using ComfyUI, audio separation, voice conversion, and video generation workflows.

## 🎯 Features

- **YouTube Audio Download**: Extract audio from YouTube videos
- **Vocal Separation**: Isolate vocals using AI-powered audio separation
- **Voice Conversion**: Convert vocals to any voice using RVC (Retrieval-based Voice Conversion)
- **Audio Segmentation**: Intelligent silence-based audio splitting
- **Image Generation**: Create custom images with ComfyUI workflows
- **Video Generation**: Generate synchronized videos for each audio segment
- **Modern GUI**: Beautiful NiceGUI-based interface with real-time monitoring
- **Modular Architecture**: Easy to extend and customize individual components

## 📋 Prerequisites

### System Requirements

- **OS**: Windows 10/11 (Linux/macOS support coming soon)
- **Python**: 3.8 or higher
- **GPU**: NVIDIA GPU with CUDA support (recommended for faster processing)
- **RAM**: Minimum 16GB (32GB recommended)
- **VRAM**: Minimum 8GB (12GB+ recommended for video generation)
- **Storage**: At least 50GB free space for models and outputs

### Required Software

1. **FFmpeg**: For audio/video processing
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use package manager
   - Add to system PATH

2. **ComfyUI**: For image and video generation
   - Install from [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
   - Recommended: Use the standalone build

3. **Ultimate-RVC** (optional): For voice conversion
   - Install from [Ultimate-RVC GitHub](https://github.com/daswer123/ultimate-rvc)

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/musicvdo-comfy.git
cd musicvdo-comfy
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Additional Dependencies

```bash
# Audio separation
pip install audio-separator-gpu

# Optional: PyTorch with CUDA (if not already installed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Step 5: Configure the Application

1. Copy the example configuration:
```bash
copy configure.json.example configure.json  # Windows
cp configure.json.example configure.json    # Linux/macOS
```

2. Edit `configure.json` with your settings:

```json
{
  "llm": {
    "provider": "openai",
    "api_key": "your-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "theme_model": "gpt-4o-mini",
    "vision_model": "gpt-4o"
  },
  "comfyui": {
    "host": "127.0.0.1",
    "port": 8188,
    "python_exe": "C:\\path\\to\\ComfyUI\\python_embeded\\python.exe",
    "main_py": "C:\\path\\to\\ComfyUI\\ComfyUI\\main.py",
    "args": ["--windows-standalone-build", "--use-sage-attention"]
  },
  "paths": {
    "root": ".",
    "img_inputs": "img_inputs",
    "outputs": "outputs",
    "logs": "logs"
  },
  "rvc": {
    "ultimate_rvc_dir": "C:\\path\\to\\ultimate-rvc",
    "voice_model": "YourVoiceModel"
  }
}
```

## 📖 Usage

### Option 1: Web GUI (Recommended)

Start the NiceGUI web interface:

```bash
python music_vdo_app.py
```

Then open your browser to `http://localhost:8080`

The GUI provides:
- Visual pipeline stage monitoring
- Real-time logs and progress tracking
- Easy configuration and file management
- One-click workflow execution

### Option 2: Command Line Scripts

#### Stage 1: Download YouTube Audio

```bash
python 1_yt_dl.py --url "https://youtube.com/watch?v=VIDEO_ID" --output ./outputs
```

#### Stage 2: Separate Vocals

```bash
python 2_Audio_separator.py --input ./outputs/audio.wav --output ./outputs
```

#### Stage 3: Segment Audio

```bash
python 3_SegmentAudio.py ./outputs/vocals.wav --min-segment 5 --max-segment 20
```

#### Stage 4: Image Generation

```bash
python comfyui_st_sg.py --workflow qwen_image_edit_2imgs_1_rashed.json
```

#### Stage 5: Video Generation

```bash
python 5_wan_infinite.py --workflow infinite_API_34s
```

### Option 3: Run Complete Pipeline

```bash
# Run all stages sequentially
python -m src.pipeline.run_all --config configure.json
```

## 🏗️ Project Structure

```
musicvdo-comfy/
├── core/                      # Core modules
│   ├── __init__.py
│   ├── comfy_client.py        # ComfyUI API client
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging utilities
│   └── memory.py              # Memory management
├── src/                       # Source code (refactored)
│   ├── pipeline/              # Pipeline stages
│   ├── utils/                 # Utility functions
│   └── cli.py                 # Command-line interface
├── img_inputs/                # Input images directory
├── outputs/                   # Generated outputs
├── AudioSegments/             # Audio segments
├── logs/                      # Log files
├── 1_yt_dl.py                 # YouTube download script
├── 2_Audio_separator.py       # Vocal separation script
├── 3_SegmentAudio.py          # Audio segmentation script
├── 4_qwen_image_edit_auto.py  # Image generation automation
├── 5_wan_infinite.py          # Video generation script
├── comfyui_st_sg.py           # ComfyUI server starter
├── music_vdo_app.py           # NiceGUI web application
├── configure.json             # Configuration file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## ⚙️ Configuration

### LLM Configuration

Configure your preferred LLM provider for theme expansion and image description:

```json
{
  "llm": {
    "provider": "openai",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "theme_model": "gpt-4o-mini",
    "vision_model": "gpt-4o",
    "max_tokens": 800,
    "temperature": 0.7
  }
}
```

### ComfyUI Configuration

Set up ComfyUI connection and startup parameters:

```json
{
  "comfyui": {
    "host": "127.0.0.1",
    "port": 8188,
    "python_exe": "path/to/python.exe",
    "main_py": "path/to/main.py",
    "args": ["--windows-standalone-build"],
    "poll_interval_sec": 10,
    "poll_timeout_sec": 1200,
    "startup_wait_sec": 60
  }
}
```

### Audio Segmentation Settings

Customize how audio is split into segments:

```json
{
  "segment": {
    "min_sec": 5,
    "max_sec": 20,
    "silence_thresh_db": -45,
    "min_silence_ms": 700,
    "reduce_long_silences": true,
    "target_silence_sec": 1.0
  }
}
```

## 🔧 Advanced Usage

### Custom Workflows

Create your own ComfyUI workflow JSON files and reference them in scripts:

```python
from core.comfy_client import ComfyClient

client = ComfyClient()
with open('my_workflow.json') as f:
    workflow = json.load(f)

prompt_id = client.queue(workflow)
outputs = client.wait(prompt_id)
client.fetch_outputs(outputs, save_dir=Path('./outputs'))
```

### Custom Audio Filters

Use custom FFmpeg filters for audio processing:

```bash
python 3_SegmentAudio.py input.wav --af "highpass=f=100,lowpass=f=8000,compand"
```

### Batch Processing

Process multiple videos in batch:

```bash
for url in $(cat urls.txt); do
    python 1_yt_dl.py --url "$url"
    python 2_Audio_separator.py --input ./outputs/audio.wav
done
```

## 🐛 Troubleshooting

### Common Issues

**1. ComfyUI fails to start**
- Check if port 8188 is already in use
- Verify Python executable path in `configure.json`
- Check `comfy_logs/` for detailed error logs

**2. Audio separation produces no output**
- Ensure ffmpeg is installed and in PATH
- Check input audio file format (should be WAV or MP3)
- Verify audio-separator models are downloaded

**3. Out of memory errors**
- Reduce video resolution in ComfyUI workflow
- Enable `--lowvram` flag for ComfyUI
- Close other GPU-intensive applications
- Use `Free Memory` button in GUI between stages

**4. YouTube download fails**
- Update yt-dlp: `pip install -U yt-dlp`
- Check if video is available in your region
- Try alternative URL format

### Getting Help

- Check the `logs/pipeline.log` file for detailed error messages
- Open an issue on GitHub with:
  - Error logs
  - Your configuration (remove API keys)
  - Steps to reproduce

## 📝 API Reference

### ComfyClient

```python
from core.comfy_client import ComfyClient

client = ComfyClient(
    host="127.0.0.1",
    port=8188,
    poll_interval=10.0,
    timeout=1200.0
)

# Start server
client.start_server()

# Check status
is_online = client.is_online()

# Upload file
filename = client.upload_file("image.png", file_type="image")

# Queue workflow
prompt_id = client.queue(workflow_dict)

# Wait for completion
outputs = client.wait(prompt_id)

# Download results
files = client.fetch_outputs(outputs, save_dir=Path("./outputs"))

# Free memory
client.free_memory()

# Stop server
client.stop_server()
```

### Configuration

```python
from core.config import config

# Get nested values
api_key = config.get('llm', 'api_key')
comfy_port = config.get('comfyui', 'port')

# Get paths
img_dir = config.get_path('img_inputs')
output_dir = config.get_path('outputs')

# Access sections
llm_config = config.llm
comfy_config = config.comfyui
```

### Logging

```python
from core.logger import get_logger

logger = get_logger()

logger.stage_start("Vocal Separation")
logger.info("Processing audio...")
logger.error("Something went wrong")
logger.stage_complete("Vocal Separation", success=False)
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - Amazing Stable Diffusion GUI
- [Ultimate-RVC](https://github.com/daswer123/ultimate-rvc) - Voice conversion toolkit
- [audio-separator](https://github.com/karaokenerds/python-audio-separator) - Audio separation library
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [NiceGUI](https://github.com/zauberzeug/nicegui) - Web UI framework

## 📬 Contact

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community support

---

Made with ❤️ by the MusicVDO Comfy Team

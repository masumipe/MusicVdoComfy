# Music VDO Comfy - AI Music Video Generation GUI

A modern, flexible NiceGUI application for orchestrating an end-to-end AI music video generation pipeline with ComfyUI integration.

## 🎯 Features

- **Modern Dark Theme UI** - Sleek gradient header, card-based layout, real-time status indicators
- **Pipeline Stepper** - 9-stage visual workflow with status badges (idle/running/done/error)
- **ComfyUI Integration** - Unified HTTP client for server management, workflow queuing, and polling
- **Memory Management** - Automatic VRAM cleanup between stages to prevent OOM errors
- **Structured Logging** - Real-time console + file-based error dumps with JSON snapshots
- **Flexible Configuration** - Single `configure.json` for all settings (API keys, paths, models)

## 📋 Pipeline Stages

1. **Theme Expansion** - LLM-powered prompt enhancement with camera/style/technical details
2. **Input Images** - Vision-based image description and prompt blending
3. **YouTube Audio** - Download and extract audio from YouTube URLs
4. **Vocal Swap** - UVR separation + RVC voice conversion
5. **Audio Segmentation** - Silence-based splitting into manageable segments
6. **Pose Change** - Generate pose-modified character images (ComfyUI workflow)
7. **Multi-Angle** - Create 4-angle variations per image (ComfyUI workflow)
8. **Video Generation** - Generate videos for each audio segment (WanInfinite workflow)
9. **Logs & Errors** - View logs, open log folder, inspect error dumps

## 🏗️ Project Structure

```
music_vdo_comfy/
├── music_vdo_app.py          # Main NiceGUI application
├── configure.json            # Configuration (API keys, paths, models)
├── Theme.txt                 # Base theme description
├── core/
│   ├── __init__.py
│   ├── config.py             # Configuration loader
│   ├── comfy_client.py       # ComfyUI HTTP client
│   ├── memory.py             # Memory cleanup utilities
│   └── logger.py             # Structured logging
├── img_inputs/               # Source images
├── pose_inputs/              # Pose reference images
├── generated_imgs/           # Generated pose-modified images
├── generated_img_vdo/        # Multi-angle variations
├── AudioSegments/            # Segmented audio files
├── Generated_VDO/            # Final video outputs
└── logs/                     # Pipeline logs and error dumps
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- ComfyUI installed and configured
- Required packages: `nicegui`, `requests`

### Installation

```bash
# Install dependencies
pip install nicegui requests pydub ffmpeg-python yt-dlp

# Configure the application
# Edit configure.json with your:
# - OpenAI API key (for LLM features)
# - ComfyUI paths (python_exe, main_py)
# - Custom directories and model settings
```

### Running the Application

```bash
python music_vdo_app.py
```

The application will start on `http://localhost:8080`

## ⚙️ Configuration

Edit `configure.json` to customize:

- **LLM Settings**: Provider, API key, models for theme expansion and vision
- **ComfyUI**: Host, port, executable paths, polling intervals
- **Paths**: All input/output directories
- **RVC**: Voice model, conversion parameters
- **Segmentation**: Silence thresholds, min/max durations
- **Video**: Frame rate, block chaining for long audio

## 🎨 UI Highlights

- **Header**: Gradient purple-blue theme with global controls (Run All, Stop, Free Memory)
- **Sidebar**: 9-stage stepper with color-coded status badges
- **Main Area**: Expandable cards for each stage with inline controls
- **Progress Bar**: Visual indicator of pipeline progress (stage X of 8)
- **Live Console**: Real-time log streaming in footer panel
- **ComfyUI Status**: Online/offline indicator with auto-refresh

## 🔧 Extending the Application

### Adding New Stages

1. Create a new module in `core/stage_*.py`
2. Add the stage to the sidebar list in `main_page()`
3. Implement the stage logic function
4. Update the progress counter

### Integrating Custom Workflows

1. Place ComfyUI workflow JSON files in the root directory
2. Use `ComfyClient.queue()` to submit workflows
3. Handle outputs with `ComfyClient.fetch_outputs()`
4. Call `free_memory()` after each workflow execution

## 📝 Logging

Logs are stored in `logs/pipeline.log` with:
- Timestamped entries for all operations
- Stage start/completion markers
- Error dumps as JSON files with full context
- Configurable retention (last 1000 messages in memory)

## 🧠 Memory Management

Automatic cleanup occurs:
- After vocal swap (RVC subprocess)
- After each pose change iteration
- After each multi-angle batch
- After each video generation
- On pipeline stop
- On manual "Free Memory" button click

## 🛣️ Roadmap

- [ ] Full LLM integration for theme expansion
- [ ] Vision API for image description
- [ ] Complete YouTube download implementation
- [ ] RVC voice swap integration
- [ ] ComfyUI workflow execution for all stages
- [ ] Per-segment prompt variation
- [ ] Video concatenation and final output

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines before submitting PRs.

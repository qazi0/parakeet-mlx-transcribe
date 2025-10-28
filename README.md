# Live Speech-to-Text

Real-time speech-to-text transcription on macOS using parakeet-mlx. Press a hotkey to record, get instant transcription with automatic paste.

## Prerequisites

1. **ffmpeg** - `brew install ffmpeg`
2. **Accessibility Permissions** - Required for auto-paste
   - System Settings → Privacy & Security → Accessibility
   - Add your terminal app (Terminal.app, iTerm2, etc.)

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

**Basic:**
```bash
python live_stt.py
```

**Quiet mode (errors only):**
```bash
python live_stt.py --quiet
```

**Background service:**
```bash
./run_background.sh start    # Start
./run_background.sh logs     # View logs
./run_background.sh stop     # Stop
```

## How to Use

1. Run the script
2. Press **Cmd + Shift + ;** to start recording
3. Speak into your microphone
4. Press **Cmd + Shift + ;** again to stop
5. Transcription auto-pastes to your active text field

## Configuration

Edit `live_stt.py`:
- `MODEL_NAME` - Change model variant
- `CHUNK_DURATION` - Adjust chunk size (default: 1.0 seconds)

## License

Apache 2.0 (parakeet-mlx license)

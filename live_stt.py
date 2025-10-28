#!/usr/bin/env python3
"""
Live Speech-to-Text with Keyboard Hotkey Control with parakeet-mlx
Press Cmd + Shift + ; to start/stop recording
"""

import threading
import queue
import sys
import time
import subprocess
import argparse
import mlx.core as mx
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Key
from parakeet_mlx import from_pretrained

MODEL_NAME = "mlx-community/parakeet-tdt-0.6b-v3"
CHUNK_DURATION = 1.0

recording = False
audio_queue = queue.Queue()
hotkey_pressed = set()
quiet_mode = False


def on_press(key):
    global hotkey_pressed
    hotkey_pressed.add(key)

    cmd_pressed = (Key.cmd in hotkey_pressed or Key.cmd_l in hotkey_pressed or Key.cmd_r in hotkey_pressed)
    shift_pressed = (Key.shift in hotkey_pressed or Key.shift_l in hotkey_pressed or Key.shift_r in hotkey_pressed)

    if cmd_pressed and shift_pressed:
        if hasattr(key, 'char') and key.char in [';', ':']:
            toggle_recording()
            return


def on_release(key):
    global hotkey_pressed
    hotkey_pressed.discard(key)


def toggle_recording():
    global recording

    if not recording:
        recording = True
        if not quiet_mode:
            print("\nRecording started (Press Cmd + Shift + ; to stop)\n")
    else:
        recording = False
        if not quiet_mode:
            print("\nRecording stopped. Processing transcription...\n")


def copy_and_paste(text):
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

    if not quiet_mode:
        print("Copied to clipboard")

    verify = subprocess.run(['pbpaste'], capture_output=True, text=True)
    if verify.stdout != text:
        print("ERROR: Clipboard verification failed", file=sys.stderr)
        return

    time.sleep(0.3)

    applescript = 'tell application "System Events" to keystroke "v" using {command down}'
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=5)

    if result.returncode == 0:
        if not quiet_mode:
            print("Pasted successfully")
    else:
        error_msg = result.stderr.strip()
        if "not allowed assistive access" in error_msg.lower():
            print("ERROR: Accessibility permission denied", file=sys.stderr)
            print("Go to: System Settings > Privacy & Security > Accessibility", file=sys.stderr)
        else:
            print(f"ERROR: Paste failed: {error_msg}", file=sys.stderr)


def audio_callback(indata, frames, time, status):
    if status and not quiet_mode:
        print(f"Audio status: {status}", file=sys.stderr)

    if recording:
        audio_queue.put(indata.copy())


def transcription_loop(model, sample_rate):
    global recording
    chunk_size = int(sample_rate * CHUNK_DURATION)

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32',
                        blocksize=chunk_size, callback=audio_callback):
        while True:
            if not recording:
                time.sleep(0.1)
                continue

            with model.transcribe_stream(context_size=(256, 256)) as transcriber:
                while not audio_queue.empty():
                    audio_queue.get()

                last_text = ""

                while recording:
                    try:
                        audio_chunk = audio_queue.get(timeout=0.1)
                        audio_mlx = mx.array(audio_chunk.flatten())
                        transcriber.add_audio(audio_mlx)

                        result = transcriber.result
                        if result.text != last_text and not quiet_mode:
                            print(f"\rTranscription: {result.text}", end='', flush=True)
                            last_text = result.text
                    except queue.Empty:
                        continue

                result = transcriber.result

                if not quiet_mode:
                    print(f"\n\nFinal transcription:\n{result.text}\n")

                    if result.sentences:
                        print("Timestamps:")
                        for sentence in result.sentences:
                            print(f"  [{sentence.start:.2f}s - {sentence.end:.2f}s] {sentence.text}")
                        print()

                if result.text.strip():
                    copy_and_paste(result.text)


def main():
    global quiet_mode

    parser = argparse.ArgumentParser(description='Live Speech-to-Text with parakeet-mlx')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress all output except errors')
    args = parser.parse_args()

    quiet_mode = args.quiet

    if not quiet_mode:
        print("=" * 60)
        print("Live Speech-to-Text with parakeet-mlx")
        print("=" * 60)
        print("\nLoading model...")

    model = from_pretrained(MODEL_NAME)
    sample_rate = model.preprocessor_config.sample_rate

    if not quiet_mode:
        print(f"Model loaded: {MODEL_NAME}")
        print(f"Sample rate: {sample_rate} Hz")
        print("\n" + "=" * 60)
        print("Press Cmd + Shift + ; to start/stop recording")
        print("Transcription will auto-paste when stopped")
        print("Press Ctrl+C to exit")
        print("=" * 60 + "\n")

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    transcription_thread = threading.Thread(target=transcription_loop,
                                           args=(model, sample_rate), daemon=True)
    transcription_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if not quiet_mode:
            print("\nExiting...")
        listener.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()

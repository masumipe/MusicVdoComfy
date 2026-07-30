#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract lead vocal from video using ACE-Step 1.5 Python module."""

import os
import sys
import time
import subprocess

# === CONFIGURATION ===
ACE_STEP_DIR = r"D:\Myfiles\ace\ACE-Step-1.5"
INPUT_VIDEO = r"D:\Myfiles\MusicVDOComfy\outputs\yt_vdo.mp4"
OUTPUT_DIR = r"D:\Myfiles\MusicVDOComfy\outputs"
ACE_PYTHON = os.path.join(ACE_STEP_DIR, ".venv", "Scripts", "python.exe")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def extract_audio(video_path):
    """Extract audio from video as 44.1kHz 16-bit WAV."""
    audio_path = os.path.join(OUTPUT_DIR, "yt_audio.wav")
    if os.path.exists(audio_path):
        log(f"Audio already extracted: {audio_path}")
        return audio_path
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log(f"Extracting audio from {video_path}...")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "44100", "-ac", "2", "-y", audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    log(f"Audio saved: {audio_path}")
    return audio_path


def run_vocal_extract(audio_path, output_wav):
    """Spawn ACE-Step python subprocess to do the actual extraction."""
    script = r"""
import os, sys, time
sys.path.insert(0, r"{ace_dir}")

# Quiet down logging
os.environ["ACESTEP_DISABLE_TQDM"] = "true"
os.environ["ACESTEP_SUPPRESS_AUDIO_TOKENS"] = "1"

from loguru import logger
logger.remove()

from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

audio_path = r"{audio_path}"
output_wav = r"{output_wav}"

log = lambda msg: print(f"[{{time.strftime('%H:%M:%S')}}] {{msg}}")

# Step 1: Initialize DiT handler
log("Loading ACE-Step model (this may take a few minutes)...")
dit_handler = AceStepHandler()
msg, ok = dit_handler.initialize_service(
    project_root=r"{ace_dir}",
    config_path="acestep-v15-base",
    device="cuda",
    use_flash_attention=False,
    offload_to_cpu=False,
)
log(f"DiT init: {{msg}}")

# Step 2: Create uninitialized LLM handler (not needed for extract/thinking=False)
llm_handler = LLMHandler()

# Step 3: Configure generation params
params = GenerationParams(
    task_type="extract",
    src_audio=audio_path,
    instruction="Extract the vocals track from the audio:",
    thinking=False,
    inference_steps=50,
    duration=-1.0,
)

config = GenerationConfig(
    batch_size=1,
    use_random_seed=True,
    audio_format="wav",
    allow_lm_batch=False,
)

# Step 4: Run generation
log("Running vocal extraction...")
result = generate_music(
    dit_handler=dit_handler,
    llm_handler=llm_handler,
    params=params,
    config=config,
    save_dir=os.path.dirname(output_wav),
)

# Step 5: Save result
if result.success and result.audios:
    src = result.audios[0]["path"]
    import shutil
    shutil.copy2(src, output_wav)
    log(f"Saved: {{output_wav}}")
else:
    log(f"[ERR] Extraction failed: {{result.error or result.status_message}}")
    sys.exit(1)
""".format(ace_dir=ACE_STEP_DIR, audio_path=audio_path, output_wav=output_wav)

    log("Running extraction via ACE-Step (this will take several minutes)...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [ACE_PYTHON, "-c", script],
        capture_output=True, timeout=1800, env=env,
    )

    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    for line in stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line.strip()}")
    for line in stderr.strip().split("\n"):
        stripped = line.strip()
        if stripped and "INFO" not in stripped and "WARNING" not in stripped:
            log(f"  [stderr] {stripped}")

    if proc.returncode != 0:
        log(f"[ERR] Subprocess exited with code {proc.returncode}")
        return False
    return os.path.exists(output_wav)


def main():
    log("=" * 50)
    log("Lead Vocal Extraction using ACE-Step 1.5")
    log("=" * 50)

    if not os.path.exists(ACE_PYTHON):
        log(f"[ERR] ACE-Step Python not found at {ACE_PYTHON}")
        sys.exit(1)

    if not os.path.exists(INPUT_VIDEO):
        log(f"[ERR] Video not found: {INPUT_VIDEO}")
        sys.exit(1)

    audio_path = extract_audio(INPUT_VIDEO)
    output_wav = os.path.join(OUTPUT_DIR, "lead_vocal.wav")

    ok = run_vocal_extract(audio_path, output_wav)
    if ok:
        log(f"Lead vocal saved to: {output_wav}")
    else:
        log("[ERR] Extraction failed.")
        sys.exit(1)

    log("Done.")


if __name__ == "__main__":
    main()

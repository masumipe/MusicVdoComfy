import os
import subprocess
import tempfile
import re
import argparse
from pathlib import Path


# ============================================================
# MAIN PIPELINE
# ============================================================

def split_on_silence_segments(
    input_file,
    output_dir="./AudioSegments",
    min_segment_sec=5,
    max_segment_sec=20,
    silence_thresh_db=-45,
    min_silence_len_ms=700,
    reduce_long_silences=True,
    target_silence_sec=1.0,
    max_silence_to_reduce_sec=2.0,
    custom_af_filter=None,   # <-- command-line filter support
):
    """
    Pipeline:
    1. Gentle artifact removal (no distortion)
    2. High-accuracy silence detection
    3. Safe silence compression OR custom filter
    4. Segment extraction
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # 1) GENTLE ARTIFACT REMOVAL → PCM16LE
    # ------------------------------------------------------------
    cleaned_file = _clean_audio_artifacts_safe(input_file)
    if not cleaned_file:
        print("[ERROR] Failed to clean audio")
        return

    duration = _get_audio_duration(cleaned_file)
    print(f"[INFO] Duration after cleaning: {duration:.2f} sec")

    # ------------------------------------------------------------
    # 2) FIRST SILENCE DETECTION
    # ------------------------------------------------------------
    silent_ranges = _detect_silence_ffmpeg(
        cleaned_file,
        silence_thresh_db=silence_thresh_db,
        min_silence_len_ms=min_silence_len_ms,
    )
    print(f"[INFO] Silences found (cleaned): {len(silent_ranges)}")

    # ------------------------------------------------------------
    # 3) LONG-SILENCE COMPRESSION OR CUSTOM FILTER
    # ------------------------------------------------------------
    processed_file = cleaned_file

    if reduce_long_silences and silent_ranges:
        if custom_af_filter:
            print("[INFO] Using custom filter from command line")
            reduced = _apply_custom_filter(cleaned_file, custom_af_filter)
        else:
            reduced = _compress_long_silences(
                cleaned_file,
                silent_ranges,
                target_silence_sec=target_silence_sec,
                max_silence_to_reduce_sec=max_silence_to_reduce_sec,
                silence_thresh_db=silence_thresh_db,
            )

        if reduced:
            processed_file = reduced
            duration = _get_audio_duration(processed_file)
            print(f"[INFO] Duration after processing: {duration:.2f} sec")
        else:
            print("[WARN] Processing failed, using cleaned file")

    # ------------------------------------------------------------
    # 4) FINAL SILENCE DETECTION
    # ------------------------------------------------------------
    final_silences = _detect_silence_ffmpeg(
        processed_file,
        silence_thresh_db=silence_thresh_db,
        min_silence_len_ms=min_silence_len_ms,
    )
    print(f"[INFO] Silences found (processed): {len(final_silences)}")

    # ------------------------------------------------------------
    # 5) SEGMENTATION
    # ------------------------------------------------------------
    segment_index = 1
    segments_created = 0

    def make_segment(start, length):
        nonlocal segment_index, segments_created
        out_path = Path(output_dir) / f"segment_{segment_index:03d}.wav"
        _extract_segment(processed_file, out_path, start, length)
        seg_dur = _get_audio_duration(out_path)
        print(f"[SEG] {out_path} ({seg_dur:.2f} sec)")
        segment_index += 1
        segments_created += 1

    if not final_silences:
        print("[INFO] No silences detected → uniform splitting")
        _split_uniformly(processed_file, output_dir, min_segment_sec, max_segment_sec, duration)
        return

    gaps = []
    prev_end = 0.0
    for s_start, s_end in final_silences:
        if s_start > prev_end:
            gaps.append((prev_end, s_start))
        prev_end = s_end
    if prev_end < duration:
        gaps.append((prev_end, duration))

    for gap_start, gap_end in gaps:
        cursor = gap_start
        while cursor < gap_end:
            remaining = gap_end - cursor
            seg_len = min(max_segment_sec, remaining)
            if seg_len < min_segment_sec:
                break
            make_segment(cursor, seg_len)
            cursor += seg_len

    print(f"[INFO] Total segments created: {segments_created}")

    if cleaned_file != input_file and os.path.exists(cleaned_file):
        os.unlink(cleaned_file)
    if processed_file != cleaned_file and os.path.exists(processed_file):
        os.unlink(processed_file)


# ============================================================
# SAFE ARTIFACT REMOVAL (NO DISTORTION)
# ============================================================

def _clean_audio_artifacts_safe(input_file):
    """
    Gentle artifact removal:
    - highpass (rumble)
    - lowpass (hiss)
    - light compand (speech leveling)
    """

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out = tmp.name

    af = (
        "highpass=f=60,"
        "lowpass=f=14000,"
        "compand=attacks=0.002:decays=0.2:points=-80/-80|-40/-20|-20/-10|0/-5"
    )

    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", af,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-y", out
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out
    except Exception as e:
        print(f"[ERROR] Safe cleaning failed: {e}")
        return None


# ============================================================
# CUSTOM FILTER SUPPORT
# ============================================================

def _apply_custom_filter(input_file, af_filter):
    """
    Apply user-provided ffmpeg filter from command line.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out = tmp.name

    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", af_filter,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-y", out
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out
    except Exception as e:
        print(f"[ERROR] Custom filter failed: {e}")
        return None


# ============================================================
# SILENCE COMPRESSION (SAFE)
# ============================================================

def _compress_long_silences(
    input_file,
    silent_ranges,
    target_silence_sec,
    max_silence_to_reduce_sec,
    silence_thresh_db,
):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out = tmp.name

    af = (
        f"silencedetect=noise={silence_thresh_db}dB:d={max_silence_to_reduce_sec},"
        f"asetpts=N/SR/TB"
    )

    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", af,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-y", out
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out
    except Exception as e:
        print(f"[ERROR] Silence compression failed: {e}")
        return None


# ============================================================
# SILENCE DETECTION
# ============================================================

def _detect_silence_ffmpeg(input_file, silence_thresh_db, min_silence_len_ms):
    min_silence_sec = min_silence_len_ms / 1000.0

    af = f"silencedetect=noise={silence_thresh_db}dB:d={min_silence_sec}"

    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", af,
        "-vn", "-sn",
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr

        silences = []
        start = None

        for line in output.split("\n"):
            if "silence_start:" in line:
                m = re.search(r"silence_start:\s*([\d.]+)", line)
                if m:
                    start = float(m.group(1))
            elif "silence_end:" in line and start is not None:
                m = re.search(r"silence_end:\s*([\d.]+)", line)
                if m:
                    end = float(m.group(1))
                    if end - start >= min_silence_sec:
                        silences.append((start, end))
                    start = None

        return silences

    except Exception as e:
        print(f"[ERROR] Silence detection failed: {e}")
        return []


# ============================================================
# SEGMENT EXTRACTION
# ============================================================

def _extract_segment(input_file, output_file, start_sec, duration_sec):
    cmd = [
        "ffmpeg",
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-i", input_file,
        "-c:a", "copy",
        "-y", output_file
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        fallback = [
            "ffmpeg",
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-i", input_file,
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-y", output_file
        ]
        subprocess.run(fallback, check=True, capture_output=True)


def _split_uniformly(input_file, output_dir, min_segment_sec, max_segment_sec, duration):
    segment_index = 1
    cursor = 0.0
    while cursor < duration:
        seg_len = min(max_segment_sec, duration - cursor)
        if seg_len < min_segment_sec:
            break
        out_path = Path(output_dir) / f"segment_{segment_index:03d}.wav"
        _extract_segment(input_file, out_path, cursor, seg_len)
        print(f"[SEG] {out_path}")
        segment_index += 1
        cursor += seg_len


def _get_audio_duration(input_file):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return None


# ============================================================
# ENTRY POINT WITH COMMAND-LINE SUPPORT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to input audio file")
    parser.add_argument("--af", help="Custom ffmpeg audio filter", default=None)
    args = parser.parse_args()

    split_on_silence_segments(
        input_file=args.input_file,
        output_dir="./AudioSegments",
        custom_af_filter=args.af
    )
# python  .\SegmentAudio.py  .\outputs\21_Voice_Converted_b70e3fb06d.wav --af silenceremove=start_periods=1:start_threshold=-50dB:start_silence=2:stop_periods=1:stop_threshold=-50dB:top_silence=2"

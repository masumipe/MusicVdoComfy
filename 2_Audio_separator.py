from audio_separator.separator import Separator
import subprocess
import os

# Initialize separator
separator = Separator(
    output_dir="outputs",
    output_format="MP3",
    output_single_stem="Vocals",
    ensemble_algorithm="avg_wave",
    ensemble_preset="vocal_balanced"
)

# Load ensemble models
separator.load_model(
    model_filename=[
        "UVR-MDX-NET-Inst_HQ_3.onnx",
        "UVR_MDXNET_KARA_2.onnx",
    ]
)

# Separate audio
output_files = separator.separate("outputs/yt_audio.wav")

print("Generated files:", output_files)

# Find the vocal file
vocal_file = None

if isinstance(output_files, list):
    vocal_file = output_files[0]
else:
    vocal_file = output_files

print("Using vocal file:", vocal_file)

vocal_file = os.path.abspath(vocal_file)

# Run Ultimate-RVC via uv run
rvc_dir = r"D:\Myfiles\ultimate-rvc"
subprocess.run(
    [
        "uv", "run",
        "--directory", rvc_dir,
        "--frozen",
        "python", "-m", "ultimate_rvc.cli.main",
        "generate", "convert-voice",
        vocal_file,
        r"D:\Myfiles\MusicVDOComfy\outputs",
        r"D:\Myfiles\ultimate-rvc\models\rvc\voice_models\Rashed_V_Model",
        "--n-octaves", "0",
        "--n-semitones", "0",
        "--f0-method", "rmvpe",
        "--index-rate", "0.3",
        "--rms-mix-rate", "1.0",
        "--protect-rate", "0.33",
        "--no-split-voice",
        "--autotune-strength", "1.0",
        "--no-proposed-pitch",
        "--proposed-pitch-threshold", "155.0",
        "--no-clean-voice",
        "--clean-strength", "0.7",
        "--embedder-model", "contentvec",
        "--sid", "0",
    ],
    check=True,
    cwd=rvc_dir,
)
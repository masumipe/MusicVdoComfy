import os
import time
import json
import uuid
import socket
import subprocess
import urllib.request
import sys

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

COMFY_PY = r"D:\Myfiles\Comfyui\ComfyUI-Easy-Install\python_embeded\python.exe"
COMFY_SERVER = r"D:\Myfiles\Comfyui\ComfyUI-Easy-Install\ComfyUI\main.py"

COMFY_ARGS = [
    "--windows-standalone-build",
    "--use-sage-attention",
    "--enable-cors-header"
]


# ---------------------------------------------------------
# CHECK IF PORT IS IN USE
# ---------------------------------------------------------
def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


# ---------------------------------------------------------
# CHECK IF COMFYUI IS RUNNING
# ---------------------------------------------------------
def comfy_running():
    try:
        urllib.request.urlopen(f"http://{server_address}/system_stats", timeout=2)
        return True
    except:
        return False


# ---------------------------------------------------------
# START COMFYUI IN A HIDDEN WINDOW
# ---------------------------------------------------------
def start_comfy():
    PORT = 8188

    print(f"[FOUND] Checking if ComfyUI is already running on port {PORT}...")

    if port_in_use(PORT):
        print(f"[READY] ComfyUI is already running on port {PORT}.")
        return True

    print("[START] Starting ComfyUI in a hidden background window...")

    cmd = [
        COMFY_PY,
        "-I",
        "-W", "ignore::FutureWarning",
        COMFY_SERVER
    ] + COMFY_ARGS

    # Hide window on Windows
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE

    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        shell=False
    )

    print("[WAIT] Waiting for ComfyUI to start...")

    for _ in range(60):
        if comfy_running():
            print("[OK] ComfyUI server is online.")
            return True
        time.sleep(1)

    print("[ERROR] ComfyUI failed to start within 60 seconds.")
    return False


# ---------------------------------------------------------
# SEND PROMPT
# ---------------------------------------------------------
def queue_prompt(prompt):
    try:
        payload = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
        response = json.loads(urllib.request.urlopen(req).read())
        return response["prompt_id"]
    except Exception as e:
        print(f"[ERROR] queue_prompt error: {e}")
        return None


# ---------------------------------------------------------
# CHECK HISTORY FOR IMAGES
# ---------------------------------------------------------
def check_for_images(prompt_id):
    try:
        url = f"http://{server_address}/history/{prompt_id}"
        response = json.loads(urllib.request.urlopen(url).read())

        if prompt_id not in response:
            return None

        outputs = response[prompt_id]["outputs"]
        images = {}

        for node_id, node_output in outputs.items():
            if "images" in node_output:
                images[node_id] = []
                for img in node_output["images"]:
                    img_url = (
                        f"http://{server_address}/view?"
                        f"filename={img['filename']}&subfolder={img['subfolder']}&type={img['type']}"
                    )
                    img_data = urllib.request.urlopen(img_url).read()
                    images[node_id].append(img_data)

        return images if images else None

    except Exception as e:
        print(f"[ERROR] check_for_images error: {e}")
        return None


# ---------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------
def run_prompt(prompt):

    if not comfy_running():
        if not start_comfy():
            return None

    print("[SEND] Sending prompt to ComfyUI...")
    prompt_id = queue_prompt(prompt)

    if not prompt_id:
        print("[WAIT] Retrying prompt_id for 2 minutes...")
        for _ in range(12):
            time.sleep(10)
            prompt_id = queue_prompt(prompt)
            if prompt_id:
                break

        if not prompt_id:
            print("[ERROR] Failed to receive prompt_id.")
            return None

    print(f"[OK] Received prompt_id: {prompt_id}")
    print("[IMAGE] Waiting for images (max 20 minutes)...")

    for _ in range(120):
        images = check_for_images(prompt_id)
        if images:
            print("[DONE] Images found!")
            return images

        print("[WAIT] No images yet... checking again in 10 seconds.")
        time.sleep(10)

    print("[ERROR] No images received after 20 minutes.")
    return None


# ---------------------------------------------------------
# LOAD PROMPT FILE
# ---------------------------------------------------------
prompt_file = os.path.join(os.path.dirname(__file__), "infinit_API.json")

if os.path.exists(prompt_file):
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = json.load(f)
else:
    print("[ERROR] No prompt file found.")
    sys.exit()


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
images = run_prompt(prompt)

if images:
    print(f"\n[PACK] Received images from {len(images)} node(s). Saving...")

    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    for node_id, imgs in images.items():
        for i, img_data in enumerate(imgs):
            ext = "jpg" if img_data[:2] == b"\xff\xd8" else "png"
            fname = f"{node_id}_{i:04d}.{ext}"
            fpath = os.path.join(output_dir, fname)
            with open(fpath, "wb") as f:
                f.write(img_data)
            print(f"[SAVE] Saved: {fpath}")
else:
    print("[ERROR] No images to save.")

# ============================================================================
#   qwen_image_edit_auto.py - FIXED & COMPLETED SCRIPT
# ============================================================================

import os
import sys
import json
import uuid
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
import time

# === CONFIGURATION (MODIFY THESE PATHS) === #

COMFY_PY_PATH = r"D:\Myfiles\Comfyui\ComfyUI-Easy-Install\python_embeded\python.exe"
OUTPUT_DIR = r"D:\Myfiles\MusicVDOComfy\outputs"  # Where generated images will be saved
WORKFLOW_FILE = "qwen_image_edit_2imgs_1_rashed.json"
COMFY_PORT = 8188
HOST_ADDR = f"http://localhost:{COMFY_PORT}"
COMFY_ARGS = ["--windows-standalone-build"]  # Optional args: --use-sage-attention

# === GLOBAL VARIABLES === #

proc_obj = None
running = False
client_id_val = str(uuid.uuid4())
prompt_dict = None
_prompt_path = None


def main():
    global proc_obj, running, prompt_dict, _prompt_path

    print("=" * 60)
    print("[START] Qwen Image Edit Workflow Automation")
    print("=" * 60 + "\n")

    try:
        # Load workflow
        workflow_data = load_workflow_json()
        if not workflow_data:
            print(f"[ERR] ERROR: Cannot find/load {WORKFLOW_FILE}")
            sys.exit(1)

        # Check if server is running, start if not
        try:
            if not is_server_online():
                start_comfy()
        except Exception as err:
            print(f"[FAIL] Server startup - {err}")
            sys.exit(1)

        # Queue the prompt and process
        prompt_id = queue_prompt()
        if prompt_id:
            print(f"[OK] Prompt queued with ID: {prompt_id[:8]}...")
            
            # Wait for generation to complete
            if wait_for_generation(prompt_id):
                print("[OK] Generation completed successfully!")
            else:
                print("[ERR] Generation timed out or failed.")
        else:
            print("[ERR] Failed to queue prompt.")

        return True

    except Exception as e:
        print(f"[FAIL] Setup Error - {e}")
        return False

    finally:
        # Clean up process if it exists
        if proc_obj:
            try:
                proc_obj.terminate()
                print("[STOP] ComfyUI server terminated.")
            except:
                pass


def load_workflow_json():
    """Load the JSON workflow file into memory."""
    global prompt_dict, _prompt_path

    _prompt_path = os.path.abspath(WORKFLOW_FILE)

    if not os.path.exists(_prompt_path):
        print(f"[SEARCH] Searching for {WORKFLOW_FILE} in alternate locations...")

        # Search in ComfyUI directory as fallback
        comfy_base = os.path.dirname(COMFY_PY_PATH)
        fallback_1 = os.path.join(comfy_base, WORKFLOW_FILE)
        fallback_2 = os.path.join(os.getcwd(), WORKFLOW_FILE)

        if os.path.exists(fallback_1):
            _prompt_path = fallback_1
        elif os.path.exists(fallback_2):
            _prompt_path = fallback_2
        else:
            print(f"[ERR] Workflow file not found: {WORKFLOW_FILE}")
            return False

    try:
        with open(_prompt_path, "r", encoding="utf-8") as f:
            prompt_dict = json.load(f)
        print(f"[FILE] Workflow loaded successfully from: {_prompt_path}")
        return prompt_dict
    except Exception as e:
        print(f"[ERR] Error loading workflow: {e}")
        return False


def is_server_online():
    """Check if ComfyUI server process and port are available."""
    global running

    try:
        urllib.request.urlopen(f"{HOST_ADDR}/system_stats", timeout=5)
        print(f"[/] Server online at {HOST_ADDR}")
        running = True
        return True
    except Exception:
        running = False
        return False


def start_comfy():
    """Launch ComfyUI server and wait for startup."""
    global proc_obj, running

    if is_server_online():
        print("[/] Server already running.")
        return True

    print("[WAIT] Starting ComfyUI server (this may take a few minutes)...")

    # Build command
    cmd_list = [COMFY_PY_PATH, r"D:\Myfiles\Comfyui\ComfyUI-Easy-Install\ComfyUI\main.py"]
    
    if COMFY_ARGS:
        cmd_list.extend(COMFY_ARGS)

    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comfy_logs")
        os.makedirs(log_dir, exist_ok=True)
        out_path = os.path.join(log_dir, "comfy_stdout.txt")
        err_path = os.path.join(log_dir, "comfy_stderr.txt")
        out_file = open(out_path, "w", encoding="utf-8")
        err_file = open(err_path, "w", encoding="utf-8")

        proc_obj = subprocess.Popen(cmd_list, stdout=out_file, stderr=err_file)
        print(f"[PROC] Process started with PID: {proc_obj.pid}")

        # Wait for server to become available (up to 5 minutes)
        for wait_count in range(10):
            print(f"[WAIT] Waiting for server... ({wait_count + 1}/10)")
            time.sleep(30)
            if is_server_online():
                print("[/] Server is ready!")
                running = True
                return True

        print("[ERR] Server failed to start within timeout.")
        return False

    except Exception as e:
        print(f"[ERR] Failed to start ComfyUI: {e}")
        return False


def queue_prompt():
    """Queue the workflow prompt and get a session ID."""
    global prompt_dict, client_id_val

    if not prompt_dict:
        print("[ERR] No workflow loaded.")
        return None

    try:
        # Prepare payload
        payload = {
            "prompt": prompt_dict,
            "client_id": client_id_val
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{HOST_ADDR}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        print("[SEND] Queueing generation...")
        response = json.loads(urllib.request.urlopen(req).read())

        if "prompt_id" in response:
            prompt_id = response["prompt_id"]
            print(f"[OK] Prompt queued, ID: {prompt_id[:8]}...")
            return prompt_id
        else:
            print(f"[ERR] Queue error: {response}")
            return None

    except Exception as ex:
        print(f"[WARN] Queue error - {ex}")
        return None


def wait_for_generation(prompt_id, max_attempts=60, sleep_time=5):
    """Poll for completed generation with timeout."""
    if not prompt_id:
        return False

    print(f"[IMAGE] Monitoring generation (up to {max_attempts * sleep_time} seconds)...")

    for attempt in range(max_attempts):
        try:
            time.sleep(sleep_time)
            
            # Check history endpoint
            history_url = f"{HOST_ADDR}/history/{prompt_id}"
            response = json.loads(urllib.request.urlopen(history_url).read())

            if prompt_id in response:
                history_data = response[prompt_id]
                
                # Check if generation is complete
                if "outputs" in history_data:
                    outputs = history_data["outputs"]
                    print(f"[OK] Generation complete! Found {len(outputs)} outputs.")
                    
                    # Save images from outputs
                    save_images_from_outputs(outputs)
                    return True
                
                # Check for errors
                if "error" in history_data:
                    print(f"[ERR] Generation error: {history_data['error']}")
                    return False

            # Check queue status (still waiting)
            queue_url = f"{HOST_ADDR}/queue"
            queue_response = json.loads(urllib.request.urlopen(queue_url).read())
            
            # If prompt not in queue and not in history, it might have failed
            if not any(prompt_id in item for item in queue_response.get("queue_running", [])):
                # Check if it's in pending queue
                if not any(prompt_id in item for item in queue_response.get("queue_pending", [])):
                    print("[WARN]️ Prompt not found in queue or history - might have failed.")
                    return False

            print(f"[WAIT] Still processing... ({attempt + 1}/{max_attempts})")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # History not available yet, continue waiting
                continue
            else:
                print(f"[WARN] HTTP error: {e}")
        except Exception as e:
            print(f"[WARN] Status check error: {e}")
            continue

    print("[ERR] Generation timed out.")
    return False


def save_images_from_outputs(outputs_dict):
    """Save generated images from outputs."""
    print("[DONE] Saving generated images...")

    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    saved_count = 0

    try:
        # Loop through all outputs
        for node_id, node_output in outputs_dict.items():
            if "images" in node_output and node_output["images"]:
                images = node_output["images"]
                
                for idx, image_info in enumerate(images):
                    try:
                        filename = image_info.get("filename")
                        if not filename:
                            continue

                        subfolder = image_info.get("subfolder", "")
                        image_type = image_info.get("type", "output")
                        
                        # Build save URL
                        save_url = f"{HOST_ADDR}/view?filename={filename}&subfolder={subfolder}&type={image_type}"
                        
                        # Generate save path
                        timestamp = datetime.now().strftime("%H%M%S")
                        base_filename = f"image_{idx}_{timestamp}"
                        save_path = os.path.join(output_dir, f"{base_filename}.png")
                        
                        # Download and save image
                        urllib.request.urlretrieve(save_url, save_path)
                        saved_count += 1
                        print(f"[{saved_count}] Saved: {filename} -> {save_path}")

                    except Exception as save_err:
                        print(f"[ERROR] Failed to save image {idx}: {save_err}")

        if saved_count > 0:
            print(f"[OK] Successfully saved {saved_count} image(s) to {output_dir}")
            return True
        else:
            print("[WARN]️ No images found in outputs.")
            return False

    except Exception as e:
        print(f"[ERROR] Save failed - {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
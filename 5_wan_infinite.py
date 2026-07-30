#!/usr/bin/env python3
"""
ComfyUI helper – queue a prompt and wait for its completion.
"""

import json
import time
import urllib.request as request
import urllib.error as uerror
from datetime import datetime

SERVER_ADDRESS = "127.0.0.1"
PORT = 8188


def queue_prompt(prompt_workflow: dict) -> dict:
    """
    Send a prompt to the ComfyUI backend.

    Parameters
    ----------
    prompt_workflow : dict
        The workflow dictionary loaded from JSON.

    Returns
    -------
    dict
        JSON response from the server (contains 'prompt_id', 'hash', etc.).
    """
    payload = {"prompt": prompt_workflow}
    data = json.dumps(payload).encode("utf-8")
    url = f"http://{SERVER_ADDRESS}:{PORT}/prompt"

    req = request.Request(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data=data,
    )

    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except uerror.HTTPError as err:
        raise RuntimeError(f"HTTP error while queueing prompt: {err}") from err
    except uerror.URLError as err:
        raise RuntimeError(f"Connection error while queueing prompt: {err}") from err


def wait_for_completion(prompt_id: int, poll_interval: float = 2.0, timeout: int = 300) -> dict:
    """
    Poll /history/<id> until the prompt is completed or a timeout occurs.

    Parameters
    ----------
    prompt_id : int
        ID returned by the queue_prompt call.
    poll_interval : float
        Seconds to wait between polls.
    timeout : int
        Seconds to wait before giving up.

    Returns
    -------
    dict
        The final history entry (contains 'outputs' etc.).
    """
    url = f"http://{SERVER_ADDRESS}:{PORT}/history/{prompt_id}"
    start = time.time()

    while True:
        try:
            with request.urlopen(url, timeout=5) as resp:
                entry = json.loads(resp.read().decode("utf-8"))
        except uerror.URLError:
            # If the server is temporarily unreachable, just retry.
            entry = None

        if entry:
            # The API marks a finished prompt with a boolean `completed`.
            if entry.get("completed", False):
                print(f"\n✅ Prompt {prompt_id} finished at {datetime.now()}")
                return entry

        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout waiting for prompt {prompt_id}")

        time.sleep(poll_interval)


def main():
    # 1. Load the workflow JSON
    try:
        with open("infinite_API_34s", "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Workflow file 'infinite_API_34s' not found.")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in workflow file: {exc}") from exc

    print("\n🚀 Queuing prompt…")
    response = queue_prompt(workflow)

    prompt_id = response.get("prompt_id")
    if not isinstance(prompt_id, int):
        raise RuntimeError("Server did not return a valid prompt_id.")

    print(f"✅ Prompt queued successfully (ID: {prompt_id})")
    print("🔄 Waiting for completion…")

    # 2. Wait until the prompt is finished
    final_entry = wait_for_completion(prompt_id)

    # 3. Print or process the results
    outputs = final_entry.get("outputs", {})
    if outputs:
        print("\n🖼️  Prompt produced the following outputs:")
        for node_id, node_output in outputs.items():
            # The actual structure depends on the workflow; here we just print keys.
            print(f"  - Node {node_id}: {list(node_output.keys())}")
    else:
        print("\n⚠️  No outputs were returned.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user.")
    except Exception as exc:
        print(f"\n❌ Unexpected error: {exc}")

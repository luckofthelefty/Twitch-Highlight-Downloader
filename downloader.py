import os
import sys
import time
import requests
import yt_dlp
import json
import concurrent.futures
import signal
from tqdm import tqdm
from multiprocessing import Manager

# Configuration (Replace with your own values or load from environment variables)
TWITCH_CLIENT_ID = "YOUR_TWITCH_CLIENT_ID"
USER_ID = "YOUR_TWITCH_USER_ID"
SAVE_DIR = "YOUR_SAVE_DIRECTORY_PATH"  # Example: "/path/to/highlights"
MAX_CONCURRENT_DOWNLOADS = 10
CONFIG_FILE = "tokens.json"
os.makedirs(SAVE_DIR, exist_ok=True)
shutdown_flag = False

# ---------------------------------------------------------------------
# Signal Handling
# ---------------------------------------------------------------------
def signal_handler(sig, frame):
    global shutdown_flag
    print("\nShutdown requested. Cleaning up...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)

# ---------------------------------------------------------------------
# Token Management
# ---------------------------------------------------------------------
def load_tokens():
    """Load the saved Twitch tokens from a file."""
    global TWITCH_ACCESS_TOKEN, TWITCH_REFRESH_TOKEN
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            TWITCH_ACCESS_TOKEN = data.get("access_token", "")
            TWITCH_REFRESH_TOKEN = data.get("refresh_token", "")
    else:
        print("⚠️ No token file found. Make sure to generate tokens first.")
        TWITCH_ACCESS_TOKEN = ""
        TWITCH_REFRESH_TOKEN = ""

def save_tokens():
    """Save the updated Twitch tokens to a file."""
    global TWITCH_ACCESS_TOKEN, TWITCH_REFRESH_TOKEN
    data = {
        "access_token": TWITCH_ACCESS_TOKEN,
        "refresh_token": TWITCH_REFRESH_TOKEN
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print("✅ Tokens saved successfully.")

def refresh_access_token():
    """
    Refresh the Twitch access token using the stored refresh token.
    Saves the new token to the config file.
    """
    global TWITCH_ACCESS_TOKEN, TWITCH_REFRESH_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": TWITCH_REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        TWITCH_ACCESS_TOKEN = token_data["access_token"]
        TWITCH_REFRESH_TOKEN = token_data.get("refresh_token", TWITCH_REFRESH_TOKEN)
        save_tokens()
        print("✅ Successfully refreshed Twitch access token!")
        return True
    else:
        print(f"❌ Failed to refresh token: {response.json()}")
        return False

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------
def sanitize_filename(title: str) -> str:
    """Sanitize the Twitch video title for safe filesystem storage."""
    sanitized = title
    for ch in [' ', '/', '|', '#', ':', '"', '?', '\\', '*']:
        sanitized = sanitized.replace(ch, '_')
    return sanitized.lower()

def get_twitch_highlights(max_videos, downloaded_videos):
    """
    Fetch the latest Twitch highlights and return only the new ones.
    If the token is expired, refresh it and retry once.
    """
    url = "https://api.twitch.tv/helix/videos"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    params = {"user_id": USER_ID, "type": "highlight", "first": 100}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 401:
        print("⚠️ OAuth token expired. Attempting to refresh...")
        if refresh_access_token():
            headers["Authorization"] = f"Bearer {TWITCH_ACCESS_TOKEN}"
            response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Error fetching highlights: {response.json()}")
        return []

    all_videos = response.json().get("data", [])
    downloaded_filenames = {file.lower() for file in downloaded_videos}
    remaining_videos = []
    for video in all_videos:
        file_name = f"{sanitize_filename(video['title'])}.mp4"
        if file_name not in downloaded_filenames:
            remaining_videos.append(video)
        if len(remaining_videos) >= max_videos:
            break
    return remaining_videos

class MyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)

# ---------------------------------------------------------------------
# Progress Hook and Download Function (Working Version)
# ---------------------------------------------------------------------
def create_progress_hook(shared_dict, index):
    """
    Creates a progress hook that updates a shared dictionary with:
       - progress (0-100)
       - speed (e.g., "1.23 MB/s")
    Falls back to using fragment_index if total_bytes is missing.
    """
    def hook(status_dict):
        if shutdown_flag:
            return
        if status_dict["status"] == "downloading":
            total_bytes = status_dict.get("total_bytes")
            if total_bytes and total_bytes > 0:
                downloaded = status_dict.get("downloaded_bytes", 0)
                progress = int(downloaded / total_bytes * 100)
            else:
                frag_idx = status_dict.get("fragment_index")
                frag_count = status_dict.get("fragment_count")
                if frag_idx is not None and frag_count:
                    progress = int(frag_idx / frag_count * 100)
                else:
                    progress = 0

            speed_bytes = status_dict.get("speed")
            if speed_bytes is not None:
                speed_str = f"{(speed_bytes/(1024*1024)):.2f} MB/s"
            else:
                speed_str = "N/A"
            shared_dict[index] = {"progress": progress, "speed": speed_str}
        elif status_dict["status"] == "finished":
            shared_dict[index] = {"progress": 100, "speed": "0.00 MB/s"}
    return hook

def download_video(video, index, shared_dict):
    """
    Downloads a video using yt_dlp with a progress hook that updates shared_dict.
    """
    video_title = sanitize_filename(video["title"])
    save_path = os.path.join(SAVE_DIR, f"{video_title}.mp4")
    if os.path.exists(save_path):
        shared_dict[index] = {"progress": 100, "speed": "0.00 MB/s"}
        return f"Already downloaded: {save_path}"

    ydl_opts = {
        "outtmpl": save_path,
        "logger": MyLogger(),
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [create_progress_hook(shared_dict, index)]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([video["url"]])
        except Exception as e:
            return f"Download failed: {e}"

    shared_dict[index] = {"progress": 100, "speed": "0.00 MB/s"}
    return f"Downloaded: {save_path}"

def terminate_child_processes(executor):
    if not executor:
        return
    processes = getattr(executor, "_processes", None)
    if processes:
        for p in processes.values():
            if p.is_alive():
                p.terminate()

# ---------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------
def main():
    load_tokens()
    manager = Manager()
    progress_dict = manager.dict()
    downloaded_videos = set(os.listdir(SAVE_DIR))
    max_videos = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    videos = get_twitch_highlights(max_videos, downloaded_videos)
    total_videos = len(videos)
    if total_videos == 0:
        print("No new highlights found.")
        return

    overall_progress = tqdm(total=total_videos, desc="Overall Progress", position=0, leave=True)
    progress_bars = [
        tqdm(total=100, desc=f"[{i+1}/{total_videos}] {sanitize_filename(vid['title'])[:30]}...", position=i+1, leave=False,
             bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}% {postfix}")
        for i, vid in enumerate(videos)
    ]

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        futures = {executor.submit(download_video, video, i, progress_dict): i for i, video in enumerate(videos)}
        completed = set()
        while len(completed) < len(futures):
            for i, bar in enumerate(progress_bars):
                data = progress_dict.get(i, {"progress": 0, "speed": "N/A"})
                bar.n = data["progress"]
                bar.set_postfix_str(data["speed"])
                bar.refresh()
            for fut in list(futures):
                if fut.done() and fut not in completed:
                    overall_progress.update(1)
                    try:
                        result = fut.result()
                    except Exception as exc:
                        result = f"Download failed: {exc}"
                    overall_progress.write(result)
                    completed.add(fut)
                    futures.pop(fut, None)
            time.sleep(0.2)
    overall_progress.close()
    for bar in progress_bars:
        bar.close()
    print("Cleanup complete. Exiting...")

if __name__ == "__main__":
    main()

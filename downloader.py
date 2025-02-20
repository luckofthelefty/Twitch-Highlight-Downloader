import os
import sys
import time
import requests
import yt_dlp
import concurrent.futures
import signal
from tqdm import tqdm
from multiprocessing import Manager

# Configuration (Replace the placeholder strings with your actual values or load from environment variables)
TWITCH_CLIENT_ID = "YOUR_TWITCH_CLIENT_ID"
TWITCH_ACCESS_TOKEN = "YOUR_TWITCH_ACCESS_TOKEN"
USER_ID = "YOUR_TWITCH_USER_ID"
SAVE_DIR = "YOUR_SAVE_DIRECTORY_PATH"  # e.g. "/path/to/save/highlights"
MAX_CONCURRENT_DOWNLOADS = 10

os.makedirs(SAVE_DIR, exist_ok=True)
shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print("\nShutdown requested. Cleaning up...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)

def get_twitch_highlights(max_videos, downloaded_videos):
    url = "https://api.twitch.tv/helix/videos"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    params = {"user_id": USER_ID, "type": "highlight", "first": 100}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        all_videos = response.json().get("data", [])
    else:
        print(f"Error fetching highlights: {response.json()}")
        return []
    
    remaining_videos = []
    for video in all_videos:
        file_name = f"{video['title'].replace(' ', '_').replace('/', '-')}.mp4"
        if file_name not in downloaded_videos:
            remaining_videos.append(video)
        if len(remaining_videos) >= max_videos:
            break
    return remaining_videos

class MyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)

def create_progress_hook(shared_dict, index):
    """
    Creates a progress hook that updates a shared dictionary.
    The shared_dict key 'index' holds a dict with:
       - 'progress': the download progress (0-100)
       - 'speed': the current download speed as a string (e.g. "1.23 MB/s" or "N/A")
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
                if frag_idx and frag_count:
                    progress = int(frag_idx / frag_count * 100)
                else:
                    progress = 0

            speed_bytes = status_dict.get("speed")
            if speed_bytes is not None:
                speed_mb = speed_bytes / (1024 * 1024)
                speed_str = f"{speed_mb:.2f} MB/s"
            else:
                speed_str = "N/A"
            shared_dict[index] = {"progress": progress, "speed": speed_str}
        elif status_dict["status"] == "finished":
            shared_dict[index] = {"progress": 100, "speed": "0.00 MB/s"}
    return hook

def download_video(video, index, shared_dict):
    """
    Runs in a separate process.
    Downloads a video using yt_dlp and updates its progress in shared_dict.
    """
    video_title = video["title"].replace(" ", "_").replace("/", "-")
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

def main():
    manager = Manager()
    progress_dict = manager.dict()  # Shared dict for per‑download progress info

    downloaded_videos = set(os.listdir(SAVE_DIR))
    max_videos = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    videos = get_twitch_highlights(max_videos, downloaded_videos)
    total_videos = len(videos)
    
    if total_videos == 0:
        print("No new highlights found.")
        return

    overall_progress = tqdm(
        total=total_videos,
        desc="Overall Progress",
        position=0,
        leave=True
    )

    per_download_bars = [
        tqdm(
            total=100,
            desc=f"Downloading {video['id']}",
            position=i + 1,
            leave=False,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}% {postfix}"
        )
        for i, video in enumerate(videos)
    ]

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        futures = {
            executor.submit(download_video, video, i, progress_dict): i
            for i, video in enumerate(videos)
        }
        
        completed_futures = set()

        while len(completed_futures) < len(futures):
            for i, bar in enumerate(per_download_bars):
                data = progress_dict.get(i, {"progress": 0, "speed": "N/A"})
                progress = data.get("progress", 0)
                speed_str = data.get("speed", "N/A")
                bar.n = progress
                bar.set_postfix_str(speed_str)
                bar.refresh()

            for fut, idx in futures.items():
                if fut.done() and fut not in completed_futures:
                    completed_futures.add(fut)
                    overall_progress.update(1)
                    overall_progress.write(fut.result())

            time.sleep(0.2)

    overall_progress.close()
    for i, bar in enumerate(per_download_bars):
        data = progress_dict.get(i, {"progress": 100, "speed": "0.00 MB/s"})
        bar.n = data.get("progress", 100)
        bar.refresh()
        bar.close()

    print("Cleanup complete. Exiting...")

if __name__ == "__main__":
    main()

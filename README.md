# Twitch Highlights Downloader

Twitch Highlights Downloader is a Python script that leverages the Twitch API and yt-dlp to download your Twitch highlights concurrently. It features real-time, per-download progress bars (including current download speed in MB/s) as well as an overall progress indicator.

## Features

- **Concurrent Downloads:** Uses batching to run up to 10 downloads simultaneously.
- **Real-Time Progress:** Displays individual progress bars for each download, including current download speed, plus an overall progress bar.
- **Batching:** Specify how many highlights to download in one batch. The script queues and processes downloads in parallel.
- **GitHub Safe:** All sensitive credentials (tokens, IDs, directories) are set as placeholders so you can safely share the repository.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/twitch-highlights-downloader.git
   cd twitch-highlights-downloader
   ```

2. **Install Dependencies:**

   Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   Then install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   _Dependencies include:_
   - `requests`
   - `yt-dlp`
   - `tqdm`

## Configuration

Before running the script, open `downloader.py` and replace the placeholder values with your actual configuration:

- **TWITCH_CLIENT_ID:** `"YOUR_TWITCH_CLIENT_ID"`
- **TWITCH_ACCESS_TOKEN:** `"YOUR_TWITCH_ACCESS_TOKEN"`
- **USER_ID:** `"YOUR_TWITCH_USER_ID"`
- **SAVE_DIR:** `"YOUR_SAVE_DIRECTORY_PATH"` (e.g., `/path/to/highlights`)

Alternatively, you can load these values from environment variables or a configuration file to keep your credentials secure.

## Usage

Run the script from the command line and pass the number of highlights you want to download. For example, to download 2 highlights:

```bash
python downloader.py 2
```

### Batching and Concurrency

- **Batching:** When you pass a number (e.g., 20), the script queues that many highlights for download.
- **Concurrency:** The script uses a `ProcessPoolExecutor` to run up to 10 downloads concurrently. As each download completes, the next one in the queue starts automatically.
- **Progress Updates:** Each download updates its own progress bar using shared multiprocessing data. An overall progress bar shows how many downloads have finished out of the total queued.

This batching mechanism helps you efficiently utilize your bandwidth and system resources, ensuring a smoother and faster download experience—even for large batches.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open issues or submit pull requests to help improve this project.

## Disclaimer

This script is provided "as is" without any warranty. Use responsibly and ensure you comply with Twitch’s terms of service when downloading highlights.

---

Happy downloading!

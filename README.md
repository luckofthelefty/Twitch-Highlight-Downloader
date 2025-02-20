# Twitch Highlights Downloader

Twitch Highlights Downloader is a Python script that leverages the Twitch API and yt-dlp to download your Twitch highlights concurrently. It features real-time, per-download progress bars (including current download speed in MB/s) as well as an overall progress indicator.

## Features

- **Concurrent Downloads:** Uses batching to run up to 10 downloads simultaneously.
- **Real-Time Progress:** Displays individual progress bars for each download, including current download speed, plus an overall progress bar.
- **Batching:** Specify how many highlights to download in one batch. The script queues and processes downloads in parallel.
- **Token Management:** Utilizes `tokens.json` to securely store and refresh OAuth tokens automatically.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/twitch-highlights-downloader.git
cd twitch-highlights-downloader
```

### 2. Install Dependencies

Create a virtual environment (optional but recommended):

```bash
python -m venv venv
# On macOS/Linux
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

**Dependencies include:**

- `requests`
- `yt-dlp`
- `tqdm`

## Configuration

Before running the script, ensure you have the necessary Twitch API credentials and user ID.

### 1. Obtain Twitch API Credentials

#### Create a Twitch Developer Application

- Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
- Click **"Register Your Application"**.
- Fill in the following details:
  - **Name:** Choose a name for your application (e.g., "Twitch Highlights Downloader").
  - **OAuth Redirect URLs:** Set this to `https://twitchtokengenerator.com`.
  - **Category:** Select "Application Integration".
- Click **Create** and save your **Client ID**.
- Click **Manage** on your newly created app and generate a **Client Secret**.

#### Generate OAuth Tokens

- Visit [Twitch Token Generator](https://twitchtokengenerator.com/).
- Scroll down to **"Use Your Own Credentials"**.
- Enter your **Client ID** and **Client Secret** from the Twitch Developer Console.
- Select the required scopes:
  - `channel:manage:videos`
- Click **"Generate Token"** and **authorize** with your Twitch account.
- Copy the generated **access token** and **refresh token** and paste them into the `tokens.json` file included in the repository.

### 2. Obtain Your Twitch User ID

- Visit [StreamWeasels' Twitch User ID Converter](https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/).
- Enter your Twitch username to retrieve your numerical User ID.

### 3. Configure the Script

Open `downloader.py` and replace the placeholder values with your actual configuration:

```python
# Configuration
TWITCH_CLIENT_ID = "YOUR_TWITCH_CLIENT_ID"
TWITCH_CLIENT_SECRET = "YOUR_TWITCH_CLIENT_SECRET"
USER_ID = "YOUR_TWITCH_USER_ID"  # Replace with your Twitch user ID
SAVE_DIR = "YOUR_SAVE_DIRECTORY_PATH"  # Example: "/path/to/highlights"
MAX_CONCURRENT_DOWNLOADS = 10
CONFIG_FILE = "tokens.json"  # File to store OAuth tokens
```

Ensure that `tokens.json` contains the correct access and refresh tokens.

## Usage

Run the script from the command line and specify the number of highlights you want to download. For example, to download 2 highlights:

```bash
python downloader.py 2
```

### Batching and Concurrency

- **Batching:** When you specify a number (e.g., 20), the script queues that many highlights for download.
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

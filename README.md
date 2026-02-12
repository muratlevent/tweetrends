# X (Twitter) Global Trending Scraper

A robust web scraper built with Python and Playwright to extract trending keywords from X's (formerly Twitter) Global Trending page.

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output Format](#-output-format)
- [License](#-license)

## 🎯 Project Overview
The goal of this project is to systematically collect trending topics across all categories on X's global trends page. It navigates the horizontal scroll containers to discover both primary trends and category-specific trends (e.g., News, Sports, Entertainment).

## ✨ Features
- **Comprehensive Scraping:** Captures default home trends and iterates through every available category.
- **Dynamic Content Handling:** Automatically handles horizontal scrolling and lazy loading.
- **Robust Detection:** Uses smart waits and spinner detection to ensure content is fully loaded before extraction.
- **Flexible UI:** Supports both headless mode (background) and windowed mode (for debugging).
- **Clean Output:** Generates structured JSON data with timestamps.

## ⚙️ Prerequisites
The following software is required to run this project:
- **Python 3.8+**: If you don't have Python installed:
  - **macOS**: `brew install python` (Requires [Homebrew](https://brew.sh/)) or download from [python.org](https://www.python.org/downloads/macos/).
  - **Windows**: Download the installer from [python.org](https://www.python.org/downloads/windows/) and ensure you check **"Add Python to PATH"** during installation.
  - **Linux**: `sudo apt update && sudo apt install python3 python3-venv` (Ubuntu/Debian).

## 🚀 Installation & Rapid Start

### The Quickest Way (Linux/macOS)
We provide a helper script that handles environment setup, dependencies, and execution in one go:
```bash
chmod +x run.sh
./run.sh
```

### Manual Installation (All Platforms)
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tweetrends
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## 🛠 Usage

### Using the script (macOS/Linux):
```bash
./run.sh                # Standard run
./run.sh --no-headless  # Debug mode (visible browser)
```

### Using Python directly:
```bash
python scraper.py
```

### Options
- `--output` or `-o`: Specify a custom output file name (default: `trends.json`).
- `--no-headless`: Run the browser in windowed mode (see it working).

**Example:**
```bash
python scraper.py --output custom_file.json --no-headless
```

## 📄 Output Format
The results are saved in a JSON file with the following structure:

```json
{
  "scraped_at": "2026-02-12T16:24:10+03:00",
  "url": "https://x.com/i/jf/global-trending/home",
  "trends": {
    "home": ["Trend 1", "Trend 2", ...],
    "News": ["News Trend 1", ...],
    "Sports": ["Sports Trend 1", ...]
  }
}
```

## ⚖️ License
This project is for educational and research purposes. Please ensure compliance with X's Terms of Service and `robots.txt` policies.

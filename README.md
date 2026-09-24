# Google-Maps-Scrapper
This Python script utilizes the Playwright library to perform web scraping and data extraction from Google Maps. It is particularly designed for obtaining information about businesses, including their name, address, website, phone number, reviews, and more.

<br>
To do a custom web scraping project you can find me on Upwork or on Linkedin<br><br>

<a href="https://www.upwork.com/freelancers/~01dbb4d47d167c2d43" target="_blank">
<img src=https://img.shields.io/badge/Upwork-6FDA44?&style=for-the-badge&logo=medium&logoColor=white alt=medium style="margin-bottom: 5px;" />
</a>

<a href="https://www.linkedin.com/in/zohaibbashir" target="_blank">
<img src="https://img.shields.io/badge/LinkedIn-0077B5?&style=for-the-badge&logo=linkedin&logoColor=white" alt="linkedin" style="margin-bottom: 5px;" />
</a>


## Table of Contents
- [Prerequisites](#prerequisites)
- [Multiple Branches](#multiple-branches)
- [Key Features](#key-features)
- [Installation](#installation)
- [Usage](#usage)
- [Web UI](#web-ui)
- [Example](#example)
- [Notes](#notes)
- [Video Example](#video-example)

## Prerequisites
- Python 3.9 or newer

## Multiple Branches
The repo currently has 3 branches
- Main
- Latest Libraries (The one that works with latest libraries, can cause issues. Prefer Main)
- Linux ( Linux Support if main branch does not work correctly)


## Key Features
- Data Scraping: The script scrapes data from Google Maps listings, extracting valuable information about businesses, such as their name, address, website, and contact details.

- Review Analysis: It extracts review counts and average ratings, providing insights into businesses' online reputation.

- Business Type Detection: The script identifies whether a business offers in-store shopping, in-store pickup, or delivery services.

- Operating Hours: It extracts information about the business's operating hours.

- Introduction Extraction: The script also scrapes introductory information about the businesses when available.

- CSV Export: Results are exported to a CSV file with a fixed set of columns (including the Google Maps link of each place).

- Multiple Searches: Run several searches in one go; places found by more than one search are only saved once.

## Installation

**Windows quick start:** double-click `run.bat`. It finds Python 3.9+ (and offers to install it with winget if missing), creates a virtual environment in `.venv`, installs the requirements (plus Playwright's Chromium, only if neither Chrome nor Edge is installed), then starts the [Web UI](#web-ui) and opens it in your browser. Later runs start the UI directly and only reinstall when `requirements.txt` changes. To use an existing virtual environment instead, run `set VENV_DIR=C:\path\to\venv` before `run.bat`.

Manual installation:

1. Clone this repository:
   ```bash
   git clone https://github.com/zohaibbashir/Google-Maps-Scrapper.git
   cd google-maps-scraper
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Only if neither Google Chrome nor Microsoft Edge is installed, install Playwright's Chromium:
   ```bash
   playwright install chromium
   ```

## Usage

Run the script with your desired search term and number of results:

```bash
python main.py -s "Turkish Restaurants in Toronto Canada" -t 20
```

- `-s` or `--search`: Search query for Google Maps (default: "turkish stores in toronto Canada"). Repeat it to run several searches.
- `-t` or `--total`: Number of results to scrape per search (default: 1)
- `-o` or `--output`: Output CSV file path (default: result.csv)
- `--append`: Append results to the output file instead of overwriting (default: off)

## Example

Append new results to an existing CSV file:
```bash
python main.py -s "Turkish Restaurants in Toronto Canada" -t 20 -o toronto_turkish_restaurants.csv --append
```

The script will launch a browser, perform the search, and start scraping information. Progress will be displayed in the terminal, and results will be saved to the specified CSV file. If `--append` is used, new results will be added to the end of the file without removing previous data.

Google Maps shows at most ~120 results for a single search. To get more, split the search by area:
```bash
python main.py -s "cafes in Park Slope Brooklyn" -s "cafes in Williamsburg Brooklyn" -t 120
```

Press Ctrl+C to stop early; places collected so far are still saved.

## Web UI

A minimal local web page is included:
```bash
python app.py
```
Open http://127.0.0.1:5000, enter one search per line and the number of results per search. The browser window opens on your machine as usual, and the page shows the results with a CSV download link when the scrape finishes. CSV files are kept in the `results/` folder. It is meant for local, single-user use only.

## Notes
- The script opens a visible browser window (not headless) for scraping. It uses Google Chrome if installed, otherwise Microsoft Edge, otherwise Playwright's Chromium.
- Google Maps DOM may change, which can break the script. If you encounter issues, update the XPaths in `main.py`.
- If Google shows a cookie/consent page, click it in the opened browser window; the script waits for the search box.
- Avoid running too many scrapes in a short period to prevent being blocked by Google.

## Video Example

https://www.linkedin.com/posts/zohaibbashir_python-data-webscraping-activity-7093920891411062784-flEQ

## License
MIT

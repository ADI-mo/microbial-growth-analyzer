

# 🧬 Science Fetcher Pro - Ultimate Edition

**A smart multi-source scientific search engine that unifies 5 databases into one powerful tool.**

This tool is designed for researchers and students who want a complete overview of a research topic without having to manually search five different websites. The system fetches articles, removes duplicates, ranks them by relevance and impact, and allows for convenient data export to Excel/CSV.

-----

## 🌟 Why is this tool useful? (Key Features)

1.  **Massive Time Saver:** Instead of searching separately on PubMed, Semantic Scholar, and Europe PMC – you get everything in one place.
2.  **Smart Ranking Algorithm:** The system doesn't just "dump" results. It calculates which article best matches your search terms (is the word in the Title?) and combines that with the Citation Count (Impact).
3.  **Quality First:** The system prioritizes reliable medical sources (like PubMed) to prevent "noise" from less authoritative sources.
4.  **Direct File Access:** Automatically detects free **Open Access PDF** links and displays them in a separate button.
5.  **Data Export:** Save results as a **CSV** (for Excel analysis) or as a readable **Text file**.

-----

## 🚀 What's New in this Version? (Change Log)

We have performed a comprehensive upgrade to the engine and interface (Backend & GUI):

### 🧠 Algorithm & Logic Improvements

  * **New Relevance Score Model:**
      * An article gets **100 points** if the search term appears in the **Title**.
      * An article gets **10 points** if the search term appears in the **Abstract**.
      * **Special Bonus (5000 points):** Awarded to articles from **PubMed** and **Europe PMC** to ensure reliable medical sources appear at the top of the list.
  * **Combined Sorting Mechanism:** Results are sorted first by **Relevance Score**, and in case of a tie, by **Citation Count (Impact)**.
  * **Decimal Year Fix:** Fixed an issue where years were displayed as `2015.0`. They are now correctly displayed as `2015`.
  * **PLOS Bug Fix:** Fixed an issue that caused PLOS author names to be missing.

### 🖥️ Interface (GUI) Upgrades

  * **Link Separation:** Distinct buttons for the article page (`Open Article`) and the download link (`Open PDF`) to avoid confusion.
  * **Clean View:** Abstracts in the table are truncated to 50 characters ("...") to prevent visual clutter (but are saved fully in the export).
  * **Flexible Export:** A new `EXPORT DATA` button opens a selection window between **CSV** (for tables) and **Text** (for reading).
  * **Smart Filename:** The save filename is automatically generated based on your search term (e.g., `DNA_Repair_results.csv`).

### 🛠️ Stability

  * **Crash Protection:** The system handles missing years, missing abstracts, or momentary network timeouts without crashing.
  * **Code Cleanup:** Removed non-English comments and fixed indentation issues to prevent runtime errors.

-----

## ⚙️ Installation Requirements

The system is written in Python 3 and uses standard libraries as much as possible to keep it lightweight and fast.

### 1\. Install Python

Ensure you have [Python 3.10 or higher](https://www.python.org/downloads/) installed on your computer.

### 2\. Install Required Libraries

Open your Terminal (or CMD) and run the following command:

```bash
pip install requests
```

*(This is the only external library required. All others - `tkinter`, `csv`, `json`, `threading` - are built-in).*

### 3\. (Optional) Create an EXE file

If you want to turn the script into a standalone software file (to share with friends):

```bash
pip install pyinstaller
```

-----

## ▶️ How to Run?

### Option A: Running the Code (For Developers)

1.  Ensure all three files are in the same folder:
      * `main.py` (The main entry point)
      * `unified_client.py` (Search engine and logic)
      * `ncbi_client.py` (PubMed connection)
2.  Open the terminal in that folder and run:
    ```bash
    python main.py
    ```

### Option B: Creating an EXE (For Regular Use)

To create a file that runs with a double-click (no VS Code needed):

1.  Open the terminal in the project folder.
2.  Run the command:
    ```bash
    pyinstaller --onefile --noconsole --clean --name="ScienceFetcher" main.py
    ```
3.  The ready-to-use file will appear in the `dist` folder.

-----

## 📚 Data Sources Used

The system scans the following databases simultaneously:

1.  **PubMed:** (Top Priority) - The world's leading medical database.
2.  **Semantic Scholar:** AI-based engine providing excellent Citation data.
3.  **Europe PMC:** European repository often containing Open Access papers not found in PubMed.
4.  **OpenAlex:** Massive index of articles, used to fill in missing data (like citation counts).
5.  **PLOS:** Publisher of Open Access articles only.

-----

**Happy Researching\! 🎓**

# Ultimate Science Fetcher Pro 🔬

**A Multi-Source Scientific Search Engine with GUI**

This application allows researchers to search across multiple scientific databases simultaneously, aggregate results, remove duplicates, and export findings into a unified text file.

## 🚀 Features

* **Unified Search:** Queries 7 major databases at once:
    * PubMed (Priority Source)
    * Semantic Scholar
    * Europe PMC
    * OpenAlex
    * PLOS
    * arXiv
    * Crossref
* **Smart Priority System:** Merges duplicates based on source quality (e.g., keeps the PubMed version over the Crossref version).
* **Modern GUI:** Built with Tkinter & TTK for a clean, responsive user experience.
* **Non-Blocking:** Uses `threading` to keep the UI responsive during heavy API requests.
* **Direct Access:** Clickable links to full articles directly from the results pane.
* **Export Data:** Save your curated search results to a local text file for later review.

## 📂 Project Structure

To run this project, ensure you have the following 3 files in the same directory:

1.  **`main.py`** - The Graphical User Interface (GUI) entry point.
2.  **`unified_client.py`** - Manages the parallel searching logic and priority merging.
3.  **`ncbi_client.py`** - Specialized client for handling complex XML parsing from PubMed/NCBI.

## 🛠️ Installation & Requirements

The project relies on standard Python libraries and the `requests` library for API calls.

1.  **Install Python 3.x**
2.  **Install Dependencies:**
    ```bash
    pip install requests
    ```

## ▶️ How to Run

1.  Open your terminal or command prompt.
2.  Navigate to the project folder.
3.  Run the main application:
    ```bash
    python main.py
    ```

## ⚙️ Technical Details

### The Priority Algorithm
The `UnifiedSearchManager` sorts results based on a predefined hierarchy. If the same paper is found in multiple databases (matched by normalized title), the system keeps the version from the highest-priority source:
1.  PubMed (Highest quality metadata)
2.  Semantic Scholar
3.  Europe PMC
4.  ...
5.  Crossref (Lowest priority - used as fallback)

### XML Parsing
Unlike simple JSON APIs, this tool includes a dedicated `xml.etree.ElementTree` parser (`ncbi_client.py`) to correctly extract Authors, Abstracts, and PMIDs from the complex NCBI XML response format.

---
**Author:** [Your Name]
**Version:** 1.0.0

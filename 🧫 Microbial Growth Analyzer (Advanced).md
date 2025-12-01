🧫 Microbial Growth Analyzer (Advanced)

A robust, Python-based tool for analyzing microbial growth curves. Features multi-series support, automatic exponential phase detection, and dual-mode data entry (OD & CFU).

🌟 Key Features

Multi-Series Analysis: Compare multiple treatments (e.g., WT vs Mutant) on a single interactive plot.

Smart Detection: Uses a Sliding Window Algorithm to automatically identify the steepest exponential growth phase ($R^2 > 0.98$).

Dual Mode:

OD Mode: Input raw OD, auto-correct for Blank, and estimate CFU.

CFU Mode: Input colony counts and dilution factors for precise calculation.

Excel Integration: Load data directly from .xlsx files using openpyxl.

Export & View: Save plots as PNG/PDF and automatically open them (uses subprocess).

📦 Installation

Clone the repository:

git clone [https://github.com/YOUR_USERNAME/microbial-growth-analyzer.git](https://github.com/YOUR_USERNAME/microbial-growth-analyzer.git)
cd microbial-growth-analyzer


Install dependencies:

pip install numpy scipy matplotlib openpyxl pytest


Run the application:

python growth_rateGUI.py


🧬 Scientific Logic

Growth Rate ($k$)

The specific growth rate is calculated using linear regression on the log-transformed data during the exponential phase:
$$ k = \frac{\log_2(N_t) - \log_2(N_0)}{t} $$

Doubling Time ($T_d$)

$$ T_d = \frac{1}{k} $$

CFU Calculation

For plate counts:
$$ CFU/ml = \frac{\text{Colonies} \times \text{Dilution Factor}}{\text{Volume Plated (ml)}} $$

🧪 How to Use

Setup: Enter a series name (e.g., "E. coli 37C").

Mode: Choose OD or CFU.

OD: Enter Blank value (e.g., 0.1).

CFU: Enter Plated Volume (e.g., 0.1 ml).

Data: Enter points manually or load an Excel file.

Analyze: Click "Calculate & Plot". The app will:

Filter invalid data.

Find the best linear phase.

Plot the curve and the regression line.

Display $k$, $T_d$, and $R^2$ in the table.

🤖 AI & Development Process

This project was evolved using AI assistance (Gemini 2.5) through several iterations:

Core Logic: Building the math functions with numpy.

GUI: Creating the interface with tkinter.

Advanced Features: Adding the sliding window algorithm and CFU conversion logic.

Refinement: Adding subprocess for file handling and strict type checking.

📁 Repository Structure

calculator_logic.py: Core mathematical functions and algorithms.

growth_rateGUI.py: Main application entry point.

test_calculator_logic.py: Unit tests (pytest).

.github/: Copilot instructions and workflows.

✅ Day 6 Assignment Checklist

[x] Stand-alone Repo: Dedicated repository structure.

[x] File Handling: Uses openpyxl for Excel and standard I/O for CSV.

[x] Subprocess: Automatically opens exported reports using OS commands.

[x] Exception Handling: Robust try-except blocks throughout the GUI and Logic.

[x] Tests: Comprehensive pytest suite included.

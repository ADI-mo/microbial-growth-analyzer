# microbial-growth-analyzer
🧫 Microbial Growth Analyzer (Pro Version)

Advanced tool for calculating specific growth rate ($k$), doubling time ($T_d$), and CFU concentrations from OD or direct counts.

This project is a standalone Python application designed for microbiology researchers. It automates the analysis of bacterial growth curves by identifying the exponential phase, calculating key kinetic parameters, and generating export-ready reports.

🌟 Key Features

1. Multi-Series Analysis

Compare Treatments: Plot multiple datasets (e.g., "WT", "Mutant A", "Mutant B") on the same graph.

Dynamic Visualization: Each series gets a unique color and automatic legend entry.

Consistency Checks: Prevents mixing inconsistent data types (OD vs. CFU) within the same session.

2. Dual Measurement Modes

OD Mode (Optical Density):

Input raw OD measurements.

Auto-Correction: Subtracts "Blank" OD automatically.

Estimation: Converts OD to CFU/ml using a customizable conversion factor (default for E. coli: $8 \times 10^8$).

CFU Mode (Colony Forming Units):

Input Colony Counts, Dilution Factors, and Plated Volume.

Calculates precise CFU/ml.

3. Smart Phase Detection (Sliding Window Algorithm)

Instead of relying on user guesswork, the software uses a Sliding Window Algorithm.

It scans the dataset to find the steepest continuous segment (highest $k$) that maintains strict linearity ($R^2 > 0.98$).

Result: Accurate calculation of the exponential phase, ignoring Lag and Stationary phases.

4. Professional Reporting

Real-time Calculation: A calculated concentration column updates instantly in the data table.

Export: Save the plot as a high-resolution PNG image.

Embedded Data: The export includes a data table (Series, $k$, $T_d$, $R^2$) embedded directly below the graph.

Auto-Open: Uses OS-level commands (subprocess) to automatically open the report after saving.

5. Data Handling

Excel Support: Load data directly from .xlsx files using openpyxl.

Editability: Remove specific data points or clear all data easily via the GUI.

🧬 Scientific Principles

Specific Growth Rate ($k$)

Calculated using linear regression on log-transformed data during the detected exponential phase:


$$k = \frac{\log_2(N_t) - \log_2(N_0)}{t}$$


(Units: Generations per Hour/Minute/Day)

Doubling Time ($T_d$)

The time required for the population to double:


$$T_d = \frac{1}{k}$$

CFU Calculation

For direct plate counts:


$$CFU/ml = \frac{\text{Colonies} \times \text{Dilution Factor}}{\text{Volume Plated (ml)}}$$

🛠️ Installation & Usage

1. Prerequisites

Ensure you have Python installed. Install the required libraries:

pip install numpy scipy matplotlib openpyxl pytest


2. Running the App

python growth_rateGUI.py


3. Workflow

Settings: Enter a Series Name and choose your units (e.g., Hours).

Mode: Select OD or CFU.

OD: Set Blank OD (e.g., 0.1).

CFU: Set Plated Volume (e.g., 0.01 ml).

Data: Add points manually or click "Load from Excel".

Analyze: Click "Calculate & Plot". The app will auto-detect the growth phase and display results.

Export: Click "Export Graph & Report" to save your findings.

🤖 AI Development & Contribution

This project was developed through an iterative collaboration with Gemini (Google AI). The AI's contribution focused on bridging the gap between biological needs and software engineering standards.

Key Contributions by AI:

Architecture & Refactoring:

Separated the codebase into Logic (calculator_logic.py), GUI (growth_rateGUI.py), and Tests (test_calculator_logic.py) to ensure modularity.

Refactored basic math functions to use NumPy for vectorization and performance (Day 3 Assignment).

Algorithm Design:

Designed and implemented the Sliding Window Algorithm to solve the common biological problem of identifying the "true" log phase without manual selection.

Implemented the logic for linear regression using scipy.stats.linregress.

Advanced Features Implementation:

Subprocess Integration: Added the capability to interact with the Operating System (Windows/macOS/Linux) to open files automatically after export (Day 6 Assignment).

Excel Integration: Implemented openpyxl logic to read specific columns safely from spreadsheets.

Dynamic GUI: Created the Tkinter interface that dynamically switches input fields based on the selected mode (OD vs. CFU) and renders Matplotlib graphs inside the application window.

Quality Assurance:

Wrote comprehensive Unit Tests (pytest) to verify edge cases (e.g., negative growth, zero variance, invalid inputs).

Added robust Error Handling (try...except blocks) throughout the GUI to prevent crashes during user input.

📁 Project Structure

growth_rateGUI.py: Main application entry point (UI & Event Handling).

calculator_logic.py: Core mathematical engine (Calculations & Algorithms).

test_calculator_logic.py: Automated testing suite.

.gitignore: Configuration for version control.

Author: [Your Name]
Course: Python for Biologists

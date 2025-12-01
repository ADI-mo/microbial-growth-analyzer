import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import openpyxl
from collections import defaultdict
import subprocess
import os
import platform

# Import Logic
from calculator_logic import growth_rate_fit, calculate_doubling_time, find_best_growth_phase, od_to_cfu_estimate, calculate_cfu_from_plate

# --- Global Data Structure ---
# DATA_SERIES: Stores raw input data
# For OD: (time, od_value)
# For CFU: (time, colony_count, dilution_factor)
DATA_SERIES = defaultdict(list) 

class GrowthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Microbial Growth Analyzer - OD & Plate Counts")
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_panel = ttk.Frame(main_frame, width=380)
        right_panel = ttk.Frame(main_frame)
        main_frame.add(left_panel)
        main_frame.add(right_panel)

        # --- LEFT PANEL: Controls ---
        
        # 1. Experiment Settings
        settings_frame = ttk.LabelFrame(left_panel, text="1. Settings")
        settings_frame.pack(fill="x", pady=5)
        
        ttk.Label(settings_frame, text="Series Name:").pack(anchor="w", padx=5)
        self.entry_name = ttk.Entry(settings_frame)
        self.entry_name.insert(0, "WT Glucose")
        self.entry_name.pack(fill="x", padx=5, pady=2)

        # Measurement Type (Radio)
        self.measure_type = tk.StringVar(value="OD")
        self.measure_type.trace("w", self.update_input_fields) # Listener for change

        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill="x", padx=5, pady=2)
        ttk.Radiobutton(type_frame, text="OD (Optical Density)", variable=self.measure_type, value="OD").pack(side="left")
        ttk.Radiobutton(type_frame, text="Plate Count (CFU)", variable=self.measure_type, value="CFU").pack(side="left")

        # Dynamic Parameters Frame
        self.params_frame = ttk.Frame(settings_frame)
        self.params_frame.pack(fill="x", padx=10, pady=5)

        # 2. Data Entry
        entry_frame = ttk.LabelFrame(left_panel, text="2. Add Data")
        entry_frame.pack(fill="x", pady=5)
        
        # Time Input
        row1 = ttk.Frame(entry_frame)
        row1.pack(fill="x", padx=5, pady=2)
        ttk.Label(row1, text="Time:").pack(side="left")
        self.entry_t = ttk.Entry(row1, width=8)
        self.entry_t.pack(side="left", padx=5)

        # Dynamic Value Inputs (OD or Colony/Dilution)
        self.input_grid = ttk.Frame(entry_frame)
        self.input_grid.pack(fill="x", padx=5, pady=2)

        ttk.Button(entry_frame, text="Add Point", command=self.add_point).pack(fill="x", padx=5, pady=5)
        ttk.Button(entry_frame, text="Load from Excel", command=self.load_file).pack(fill="x", padx=5, pady=2)

        # 3. Actions
        action_frame = ttk.LabelFrame(left_panel, text="3. Analyze")
        action_frame.pack(fill="x", pady=5)
        ttk.Button(action_frame, text="Calculate & Plot", command=self.run_analysis).pack(fill="x", padx=5, pady=5)
        ttk.Button(action_frame, text="Clear All", command=self.clear_all).pack(fill="x", padx=5, pady=2)
        ttk.Button(action_frame, text="Export Report", command=self.export_report).pack(fill="x", padx=5, pady=2)

        
        # 4. Data List
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("series", "t", "raw"), show="headings")
        self.tree.heading("series", text="Series")
        self.tree.heading("t", text="Time")
        self.tree.heading("raw", text="Data (OD or Count/Dil)")
        self.tree.column("series", width=80)
        self.tree.column("t", width=50)
        self.tree.column("raw", width=120)
        self.tree.pack(side="left", fill="both", expand=True)
        
        # --- RIGHT PANEL: Visualization ---
        self.fig = plt.figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Results Table
        self.res_tree = ttk.Treeview(right_panel, columns=("name", "k", "td", "r2"), show="headings", height=5)
        self.res_tree.heading("name", text="Series")
        self.res_tree.heading("k", text="k (gen/time)")
        self.res_tree.heading("td", text="Doubling Time")
        self.res_tree.heading("r2", text="R²")
        self.res_tree.pack(fill="x", pady=5)

        # Initialize Inputs
        self.entry_blank = None
        self.entry_factor = None
        self.entry_vol = None
        self.entry_val = None
        self.entry_dil = None
        self.update_input_fields()

    def update_input_fields(self, *args):
        """Switches input fields based on OD vs CFU mode."""
        for widget in self.params_frame.winfo_children(): widget.destroy()
        for widget in self.input_grid.winfo_children(): widget.destroy()

        mode = self.measure_type.get()

        if mode == "OD":
            # Params
            ttk.Label(self.params_frame, text="Blank OD:").grid(row=0, column=0)
            self.entry_blank = ttk.Entry(self.params_frame, width=8)
            self.entry_blank.insert(0, "0.0")
            self.entry_blank.grid(row=0, column=1, padx=5)
            
            ttk.Label(self.params_frame, text="Est. Factor (x10^8):").grid(row=0, column=2)
            self.entry_factor = ttk.Entry(self.params_frame, width=8)
            self.entry_factor.insert(0, "8.0")
            self.entry_factor.grid(row=0, column=3, padx=5)

            # Data Entry
            ttk.Label(self.input_grid, text="OD Value:").pack(side="left")
            self.entry_val = ttk.Entry(self.input_grid, width=10)
            self.entry_val.pack(side="left", padx=5)
            self.entry_dil = None 

        else: # CFU Mode
            # Params
            ttk.Label(self.params_frame, text="Plated Vol (ml):").grid(row=0, column=0)
            self.entry_vol = ttk.Entry(self.params_frame, width=8)
            self.entry_vol.insert(0, "0.1") # Standard 100ul
            self.entry_vol.grid(row=0, column=1, padx=5)

            # Data Entry
            ttk.Label(self.input_grid, text="# Colonies:").pack(side="left")
            self.entry_val = ttk.Entry(self.input_grid, width=8)
            self.entry_val.pack(side="left", padx=2)
            
            ttk.Label(self.input_grid, text="Dilution (e.g. 1000):").pack(side="left")
            self.entry_dil = ttk.Entry(self.input_grid, width=8)
            self.entry_dil.insert(0, "1000")
            self.entry_dil.pack(side="left", padx=2)

    def add_point(self):
        try:
            name = self.entry_name.get().strip()
            t = float(self.entry_t.get())
            
            mode = self.measure_type.get()
            if mode == "OD":
                val = float(self.entry_val.get())
                if val <= 0: raise ValueError("OD must be > 0")
                DATA_SERIES[name].append({"t": t, "type": "OD", "od": val})
            else:
                count = float(self.entry_val.get())
                dil = float(self.entry_dil.get())
                if count < 0: raise ValueError("Count must be >= 0")
                if dil < 1: raise ValueError("Dilution factor must be >= 1")
                DATA_SERIES[name].append({"t": t, "type": "CFU", "count": count, "dil": dil})

            self.update_data_table()
            self.entry_val.delete(0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def update_data_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for name, points in DATA_SERIES.items():
            for p in points:
                if p["type"] == "OD":
                    raw = f"OD: {p['od']}"
                else:
                    raw = f"Cols: {int(p['count'])} (x{int(p['dil'])})"
                self.tree.insert('', 'end', values=(name, p['t'], raw))

    def clear_all(self):
        DATA_SERIES.clear()
        self.update_data_table()
        self.ax.clear()
        self.canvas.draw()
        for i in self.res_tree.get_children(): self.res_tree.delete(i)

    def load_file(self):
        messagebox.showinfo("Info", "Excel Format:\nOD Mode: Col A=Time, Col B=OD\nCFU Mode: Col A=Time, Col B=Count, Col C=Dilution")
        filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        
        name = self.entry_name.get()
        mode = self.measure_type.get()
        
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or row[0] is None: continue
                t = float(row[0])
                
                if mode == "OD" and len(row) >= 2:
                    val = float(row[1])
                    DATA_SERIES[name].append({"t": t, "type": "OD", "od": val})
                elif mode == "CFU" and len(row) >= 3:
                    count = float(row[1])
                    dil = float(row[2])
                    DATA_SERIES[name].append({"t": t, "type": "CFU", "count": count, "dil": dil})
            
            self.update_data_table()
            messagebox.showinfo("Success", f"Loaded data into '{name}'")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_report(self):
        """Exports graph and opens it using the OS default viewer via subprocess."""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("PDF", "*.pdf")]
            )
            if not filepath:
                return

            self.fig.savefig(filepath)
            
            if messagebox.askyesno("Export Success", "File saved. Open it now?"):
                try:
                    sys_plat = platform.system()
                    if sys_plat == 'Windows':
                        os.startfile(filepath)
                    elif sys_plat == 'Darwin':
                        subprocess.run(['open', filepath], check=True)
                    else:
                        subprocess.run(['xdg-open', filepath], check=True)
                except Exception as e:
                    messagebox.showwarning("Open Error", f"Could not open file: {e}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save report: {e}")

    def run_analysis(self):
        self.ax.clear()
        for i in self.res_tree.get_children(): self.res_tree.delete(i)
        
        try:
            if self.measure_type.get() == "OD":
                blank = float(self.entry_blank.get())
                factor = float(self.entry_factor.get()) * 1e8
            else:
                vol = float(self.entry_vol.get())
        except:
            messagebox.showerror("Error", "Check Settings (Blank/Factor/Volume).")
            return

        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        
        for i, (name, points) in enumerate(DATA_SERIES.items()):
            points.sort(key=lambda x: x["t"])
            
            times = []
            log_cfus = []
            real_cfus = []
            
            for p in points:
                t = p["t"]
                cfu = 0
                
                if p["type"] == "OD":
                    cfu = od_to_cfu_estimate(p["od"], blank, factor)
                elif p["type"] == "CFU":
                    cfu = calculate_cfu_from_plate(p["count"], p["dil"], vol)
                
                if cfu > 0:
                    times.append(t)
                    real_cfus.append(cfu)
                    log_cfus.append(np.log2(cfu))

            if len(times) < 2: continue

            k, r2, (start, end) = find_best_growth_phase(times, real_cfus)
            td = calculate_doubling_time(k)

            color = colors[i % len(colors)]
            self.ax.scatter(times, log_cfus, color=color, alpha=0.5, label=name)
            
            fit_t = times[start:end]
            fit_log = log_cfus[start:end]
            if len(fit_t) > 1:
                slope = k
                intercept = np.mean(fit_log) - slope * np.mean(fit_t)
                x_line = np.linspace(min(fit_t), max(fit_t), 10)
                y_line = slope * x_line + intercept
                self.ax.plot(x_line, y_line, color=color, linewidth=2)

            self.res_tree.insert('', 'end', values=(name, f"{k:.3f}", f"{td:.2f}", f"{r2:.3f}"))

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Log2(CFU/ml)")
        self.ax.set_title("Growth Curve Analysis")
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = GrowthApp(root)
    root.mainloop()

    

import numpy as np
from scipy.stats import linregress
from typing import List, Tuple, Dict, Optional

# --- Conversions ---

def calculate_cfu_from_plate(colony_count: float, dilution_factor: float, plated_volume_ml: float) -> float:
    """
    Calculates CFU/ml based on plate counts.
    Formula: CFU/ml = (Number of Colonies * Dilution Factor) / Volume Plated
    Example: 50 colonies, 10^4 dilution, 0.1ml plated -> 50 * 10000 / 0.1 = 5,000,000 CFU/ml
    """
    if plated_volume_ml <= 0:
        raise ValueError("Plated volume must be positive.")
    if colony_count < 0:
        raise ValueError("Colony count cannot be negative.")
    
    return (colony_count * dilution_factor) / plated_volume_ml

def od_to_cfu_estimate(od_value: float, blank: float, conversion_factor: float) -> float:
    """
    Estimates cells/ml from OD. 
    Note: This is an approximation.
    """
    corrected_od = od_value - blank
    if corrected_od <= 0:
        return 0.0
    return corrected_od * conversion_factor

# --- Core Calculations ---

def growth_rate(N_t: float, N_0: float, t: float) -> float:
    """Calculates specific growth rate k = (log2(Nt) - log2(N0)) / t"""
    if t <= 0 or N_t <= 0 or N_0 <= 0:
        raise ValueError("Error: All parameters must be positive.")
    num_generations = np.log2(N_t) - np.log2(N_0)
    return float(num_generations / t)

def calculate_doubling_time(k: float) -> float:
    """Calculates Doubling Time Td = 1 / k"""
    if k <= 0: return float('inf')
    return 1.0 / k

def growth_rate_fit(time_points: List[float], concentration_points: List[float]) -> Tuple[float, float]:
    """
    Linear regression on log2(concentration).
    Returns (k, r_squared).
    """
    if len(time_points) < 2:
        raise ValueError("Need at least 2 points.")
    if any(c <= 0 for c in concentration_points):
        raise ValueError("Concentrations must be > 0.")
        
    log2_conc = np.log2(concentration_points)
    
    # Handle stagnant growth (Zero Variance)
    if np.all(log2_conc == log2_conc[0]):
        return 0.0, 1.0

    slope, intercept, r_value, p_value, std_err = linregress(time_points, log2_conc)
    return float(slope), float(r_value**2)

def find_best_growth_phase(
    times: List[float], 
    concentrations: List[float], 
    min_points: int = 3, 
    r2_threshold: float = 0.98
) -> Tuple[float, float, Tuple[int, int]]:
    """
    Sliding Window Algorithm: Finds the steepest exponential phase.
    Returns: (best_k, best_r2, (start_idx, end_idx))
    """
    n = len(times)
    try:
        best_k, best_r2 = growth_rate_fit(times, concentrations)
        best_indices = (0, n)
    except:
        best_k, best_r2, best_indices = 0, 0, (0, n)

    found = False

    for start in range(n - min_points + 1):
        for end in range(start + min_points, n + 1):
            subset_t = times[start:end]
            subset_c = concentrations[start:end]
            
            if subset_c[-1] <= subset_c[0]: continue

            try:
                k, r2 = growth_rate_fit(subset_t, subset_c)
                if r2 >= r2_threshold:
                    if not found or k > best_k:
                        best_k = k
                        best_r2 = r2
                        best_indices = (start, end)
                        found = True
            except ValueError:
                continue
                
    return best_k, best_r2, best_indices
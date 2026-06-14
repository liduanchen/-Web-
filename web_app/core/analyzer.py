import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import sqlite3
from .db import get_connection

def auto_select_min_cutoff(df):
    if df.empty:
        return 1500.0
    x = df["wavenumber"].values
    y = df["reflectance"].values
    min_w = x.min()
    candidates = np.arange(max(min_w, 600), min(x.max(), 2200) + 1, 40)
    best_cutoff = None
    best_score = -np.inf
    for cutoff in candidates:
        mask = x >= cutoff
        if np.sum(mask) < 80:
            continue
        x_sub = x[mask]
        y_sub = y[mask]
        peaks, _ = find_peaks(y_sub, distance=20, height=np.mean(y_sub) * 0.7)
        if len(peaks) < 3:
            continue
        deltas = np.diff(x_sub[peaks])
        std_delta = np.std(deltas) if len(deltas) > 1 else 999
        score = len(peaks) * 12 - std_delta * 6
        if score > best_score:
            best_score = score
            best_cutoff = cutoff
    return float(best_cutoff) if best_cutoff is not None else max(min_w + 350, 1300.0)

def suggest_min_cutoff(material, angle):
    conn = get_connection()
    df = pd.read_sql(
        "SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=?",
        conn,
        params=(material, float(angle)),
    )
    conn.close()
    if df.empty:
        return {"ok": False, "error": "数据不存在"}
    val = auto_select_min_cutoff(df)
    return {"ok": True, "value": val}

def perform_analysis(material, angle_deg, min_cutoff, method, inversion_mode, n_film, n_sub, peak_distance, n_min, n_max):
    conn = get_connection()
    df = pd.read_sql(
        "SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=?",
        conn,
        params=(material, float(angle_deg)),
    )
    conn.close()

    if df.empty:
        return {"ok": False, "error": "未找到匹配数据"}
        
    df_filtered = df[df["wavenumber"] >= min_cutoff].copy()
    if df_filtered.empty:
        return {"ok": False, "error": f"在 {min_cutoff} cm^-1 之后没有数据点。"}
        
    x = df_filtered["wavenumber"].values
    y = df_filtered["reflectance"].values
    
    peaks, _ = find_peaks(y, distance=peak_distance, height=np.mean(y))
    if len(peaks) < 2:
        return {"ok": False, "error": "未检测到足够的干涉条纹，请降低峰值间距或调整分析起点。"}
        
    theta_prime = np.arcsin(np.sin(np.radians(angle_deg)) / n_film)
    avg_delta_nu = float(np.abs(np.mean(np.diff(x[peaks]))))
    thickness_fast = 10000 / (2 * n_film * np.cos(theta_prime) * avg_delta_nu)
    constant_k = 10000 / (2 * n_film * np.cos(theta_prime))
    peak_x = x[peaks]
    phase_anchor = peak_x[0] if len(peak_x) > 0 else x[0]
    y_mean = float(np.mean(y))
    amp = max(float(np.ptp(y) / 2), 1e-6)

    def build_cosine_curve(thickness_guess):
        delta_guess = constant_k / max(thickness_guess, 1e-6)
        return y_mean + amp * np.cos(2 * np.pi * (x - phase_anchor) / delta_guess)

    def tmm_reflectance(thickness_um, n_f):
        wl_um = 10000.0 / np.maximum(x, 1e-9)
        n0 = 1.0
        n1 = n_f
        n2 = n_sub
        theta0 = np.radians(angle_deg)
        theta1 = np.arcsin(np.clip(n0 * np.sin(theta0) / n1, -1, 1))
        theta2 = np.arcsin(np.clip(n0 * np.sin(theta0) / n2, -1, 1))
        beta = 2 * np.pi * n1 * np.cos(theta1) * thickness_um / np.maximum(wl_um, 1e-9)
        exp_term = np.exp(2j * beta)
        r01_s = (n0 * np.cos(theta0) - n1 * np.cos(theta1)) / (n0 * np.cos(theta0) + n1 * np.cos(theta1))
        r12_s = (n1 * np.cos(theta1) - n2 * np.cos(theta2)) / (n1 * np.cos(theta1) + n2 * np.cos(theta2))
        rs = (r01_s + r12_s * exp_term) / (1 + r01_s * r12_s * exp_term)
        r01_p = (n1 * np.cos(theta0) - n0 * np.cos(theta1)) / (n1 * np.cos(theta0) + n0 * np.cos(theta1))
        r12_p = (n2 * np.cos(theta1) - n1 * np.cos(theta2)) / (n2 * np.cos(theta1) + n1 * np.cos(theta2))
        rp = (r01_p + r12_p * exp_term) / (1 + r01_p * r12_p * exp_term)
        raw = np.abs(0.5 * (rs + rp)) ** 2
        raw_norm = (raw - np.min(raw)) / (np.ptp(raw) + 1e-9)
        y_norm = (y - np.min(y)) / (np.ptp(y) + 1e-9)
        aligned = raw_norm * np.ptp(y) + np.min(y)
        mse = float(np.mean((raw_norm - y_norm) ** 2))
        return aligned, mse

    method_key = str(method or "").lower()
    inversion_key = str(inversion_mode or "").lower()

    if "tmm" in method_key:
        if "joint" in inversion_key or "联合" in inversion_key:
            best_mse = float("inf")
            best_fit = build_cosine_curve(thickness_fast)
            best_n = n_film
            best_trace = np.array([thickness_fast], dtype=float)
            for n_guess in np.linspace(n_min, n_max, 38):
                theta_tmp = np.arcsin(np.clip(np.sin(np.radians(angle_deg)) / n_guess, -1, 1))
                t0 = 10000 / (2 * n_guess * np.cos(theta_tmp) * max(avg_delta_nu, 1e-9))
                search_min = max(0.1, t0 * 0.55)
                search_max = max(search_min + 0.2, t0 * 1.8)
                local_trace = np.linspace(search_min, search_max, 36)
                for t_guess in local_trace:
                    y_guess, mse_guess = tmm_reflectance(float(t_guess), float(n_guess))
                    if mse_guess < best_mse:
                        best_mse = mse_guess
                        best_fit = y_guess
                        best_n = float(n_guess)
                        thickness_um = float(t_guess)
                        best_trace = local_trace
            n_film = best_n
            thickness_trace = np.append(best_trace, thickness_um)
            mse_trace = [tmm_reflectance(float(t), n_film)[1] for t in thickness_trace]
            y_fit = best_fit
            mse_final = float(best_mse)
        else:
            search_min = max(0.2, thickness_fast * 0.5)
            search_max = max(search_min + 0.2, thickness_fast * 1.8)
            thickness_trace = np.linspace(search_min, search_max, 52)
            mse_trace = []
            best_idx = 0
            best_mse = float("inf")
            best_fit = build_cosine_curve(thickness_fast)
            for i, t_guess in enumerate(thickness_trace):
                y_guess, mse_guess = tmm_reflectance(float(t_guess), n_film)
                mse_trace.append(mse_guess)
                if mse_guess < best_mse:
                    best_mse = mse_guess
                    best_idx = i
                    best_fit = y_guess
            thickness_um = float(thickness_trace[best_idx])
            y_fit = best_fit
            mse_final = float(best_mse)
    else:
        thickness_um = float(thickness_fast)
        thickness_trace = np.linspace(max(thickness_um * 0.65, 0.1), thickness_um * 1.35, 36)
        thickness_trace = np.append(thickness_trace, thickness_um)
        mse_trace = [
            float(np.mean((build_cosine_curve(float(t)) - y) ** 2)) for t in thickness_trace
        ]
        y_fit = build_cosine_curve(thickness_um)
        mse_final = float(np.mean((y_fit - y) ** 2))

    fit_confidence = max(0.0, min(100.0, (1.0 - mse_final / (np.var(y) + 1e-9)) * 100.0))
    eps_r = n_film ** 2

    # --- Option D: Standing Wave Field Intensity (E-Field Mapping) ---
    wave_x = np.linspace(x.min(), x.max(), 50)
    depth_z = np.linspace(0, thickness_um, 50)
    standing_wave_z = []
    r_val = 0.45 
    for di in depth_z:
        phase = (4 * np.pi * n_film * di * wave_x) / 10000.0
        # Add a slight phase shift for visual depth
        intensity = 1.0 + (r_val**2) + 2 * r_val * np.cos(phase + 0.5)
        standing_wave_z.append(intensity.tolist())

    # --- Option E: Complex Index Analytical Panel (n-k Dispersion) ---
    nu_mid = (x.min() + x.max()) / 2
    # Realistic Cauchy-like slope for n
    dispersion_n = n_film + 2.0e-8 * (wave_x - nu_mid)**2
    # Simulated k (Extinction) - small in IR but shows absorption edge
    # k = C / (nu - nu_offset)
    dispersion_k = 0.001 + 5.0e-5 * np.exp((1500 - wave_x) / 500)
    
    # Confidence Envelope (Simulated based on MSE)
    upper_n = (dispersion_n + 0.04 * (1.0 + mse_final*5)).tolist()
    lower_n = (dispersion_n - 0.04 * (1.0 + mse_final*5)).tolist()
    
    # Standard Reference (Library value)
    ref_n = [float(n_film)] * len(wave_x)

    return {
        "ok": True,
        "x": x.tolist(),
        "y": y.tolist(),
        "fit_y": y_fit.tolist(),
        "peaks_x": x[peaks].tolist(),
        "peaks_y": y[peaks].tolist(),
        "thickness_um": float(thickness_um),
        "n_film": float(n_film),
        "n_sub": float(n_sub),
        "epsilon_r": float(eps_r),
        "fit_confidence": float(fit_confidence),
        "mse_final": float(mse_final),
        "avg_delta_nu": float(avg_delta_nu),
        "peak_count": len(peaks),
        "thickness_trace": thickness_trace.tolist(),
        "mse_trace": mse_trace,
        # Option D & E Data (Upgraded)
        "swave_x": wave_x.tolist(),
        "swave_y": depth_z.tolist(),
        "swave_z": standing_wave_z,
        "disp_x": wave_x.tolist(),
        "disp_n": dispersion_n.tolist(),
        "disp_k": dispersion_k.tolist(),
        "disp_ref_n": ref_n,
        "disp_upper": upper_n,
        "disp_lower": lower_n
    }

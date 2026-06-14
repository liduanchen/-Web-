"""
Matplotlib 光谱拟合图（与 epi_vision_qt.py 中 _perform_analysis 绘图风格一致）。
使用 Agg 后端生成 PNG，供 Web API 以 base64 返回。
"""

from __future__ import annotations

import base64
import io
from typing import Sequence, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


Number = Union[float, int]


def render_spectrum_fit_png_base64(
    x: Sequence[Number],
    y: Sequence[Number],
    fit_y: Sequence[Number],
    peaks_x: Sequence[Number],
    peaks_y: Sequence[Number],
    title: str,
    *,
    dpi: int = 100,
) -> str:
    """
    返回 PNG 的 base64 字符串（不含 data URL 前缀）。
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    fit_arr = np.asarray(fit_y, dtype=float)
    px = np.asarray(peaks_x, dtype=float)
    py = np.asarray(peaks_y, dtype=float)

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.Figure(figsize=(12, 6), dpi=dpi)
    fig.patch.set_facecolor("#131b30")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0f172a")

    ax.plot(x_arr, y_arr, color="#22d3ee", linewidth=2.0, alpha=0.95, label="实验光谱")
    y_min = float(np.min(y_arr)) if y_arr.size else 0.0
    ax.fill_between(x_arr, y_arr, y_min, color="#0ea5e9", alpha=0.12)
    ax.plot(
        x_arr,
        fit_arr,
        color="#f59e0b",
        linewidth=2.1,
        linestyle="--",
        alpha=0.92,
        label="理论拟合",
    )
    if px.size and py.size:
        ax.scatter(
            px,
            py,
            color="#ef4444",
            s=70,
            edgecolors="#f8fafc",
            linewidths=1.2,
            zorder=5,
            label="干涉峰",
        )

    ax.set_title(title, fontsize=14, color="#e2e8f0", pad=12)
    # 使用 mathtext，稳定渲染上标 -1（cm⁻¹）
    ax.set_xlabel(r"波数 (cm$^{-1}$)", color="#cbd5e1")
    ax.set_ylabel("反射率 (%)", color="#cbd5e1")
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.grid(True, linestyle="--", linewidth=0.8, alpha=0.35, color="#475569")
    leg = ax.legend(loc="upper right", fontsize=10, frameon=True)
    leg.get_frame().set_facecolor("#111827")
    leg.get_frame().set_edgecolor("#334155")
    for t in leg.get_texts():
        t.set_color("#f8fafc")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_wafer_heatmap_png_base64(
    thickness_um: float,
    material: str = "",
    *,
    dpi: int = 100,
) -> str:
    """Render a 2D radial wafer uniformity heatmap as base64 PNG."""
    import numpy as np

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    grid_size = 40
    xs = np.linspace(-1, 1, grid_size + 1)
    ys = np.linspace(-1, 1, grid_size + 1)
    z = np.zeros((grid_size + 1, grid_size + 1))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            r2 = x * x + y * y
            if r2 <= 1:
                bow = r2 * 0.03 * thickness_um
                noise = (np.random.RandomState(i * 100 + j).rand() - 0.5) * 0.002
                z[j, i] = thickness_um - bow + noise
            else:
                z[j, i] = np.nan

    fig = plt.Figure(figsize=(8, 7), dpi=dpi)
    fig.patch.set_facecolor("#131b30")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0f172a")

    im = ax.imshow(
        z, origin="lower", extent=[-1, 1, -1, 1],
        cmap="viridis", aspect="equal", interpolation="bilinear",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Thickness (μm)", color="#cbd5e1")
    cbar.ax.yaxis.set_tick_params(color="#94a3b8")
    for label in cbar.ax.get_yticklabels():
        label.set_color("#94a3b8")

    title = f"{material} Wafer Uniformity Map" if material else "Wafer Uniformity Map"
    ax.set_title(title, fontsize=14, color="#e2e8f0", pad=12)
    ax.set_xlabel("Normalized X", color="#cbd5e1")
    ax.set_ylabel("Normalized Y", color="#cbd5e1")
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_color("#334155")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_crystal_lattice_png_base64(
    material: str = "SiC",
    *,
    dpi: int = 100,
) -> str:
    """Render a stylized crystal lattice schematic as base64 PNG."""
    import numpy as np

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    color_map = {
        "SiC": ("#22d3ee", "#1e293b"),
        "Si": ("#38bdf8", "#38bdf8"),
        "GaN": ("#a78bfa", "#e2e8f0"),
        "GaAs": ("#f59e0b", "#94a3b8"),
    }
    color_a, color_b = color_map.get(material, ("#38bdf8", "#94a3b8"))

    fig = plt.Figure(figsize=(8, 7), dpi=dpi)
    fig.patch.set_facecolor("#131b30")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0f172a")

    size = 3
    spacing = 1.5
    offset = (size - 1) * spacing / 2

    xs_a, ys_a, zs_a = [], [], []
    xs_b, ys_b, zs_b = [], [], []

    for ix in range(size):
        for iy in range(size):
            for iz in range(size):
                x = ix * spacing - offset
                y = iy * spacing - offset
                z = iz * spacing - offset
                if (ix + iy + iz) % 2 == 0:
                    xs_a.append(x); ys_a.append(y); zs_a.append(z)
                else:
                    xs_b.append(x); ys_b.append(y); zs_b.append(z)

    ax.scatter(xs_a, ys_a, zs_a, c=color_a, s=300, edgecolors="white", linewidths=0.5, alpha=0.95, label="Type A")
    ax.scatter(xs_b, ys_b, zs_b, c=color_b, s=200, edgecolors="white", linewidths=0.5, alpha=0.85, label="Type B")

    # Draw bonds
    for ix in range(size - 1):
        for iy in range(size):
            for iz in range(size):
                x0, y0, z0 = ix * spacing - offset, iy * spacing - offset, iz * spacing - offset
                x1, y1, z1 = (ix + 1) * spacing - offset, iy * spacing - offset, iz * spacing - offset
                ax.plot([x0, x1], [y0, y1], [z0, z1], color="#475569", linewidth=1.2, alpha=0.6)
    for ix in range(size):
        for iy in range(size - 1):
            for iz in range(size):
                x0, y0, z0 = ix * spacing - offset, iy * spacing - offset, iz * spacing - offset
                x1, y1, z1 = ix * spacing - offset, (iy + 1) * spacing - offset, iz * spacing - offset
                ax.plot([x0, x1], [y0, y1], [z0, z1], color="#475569", linewidth=1.2, alpha=0.6)
    for ix in range(size):
        for iy in range(size):
            for iz in range(size - 1):
                x0, y0, z0 = ix * spacing - offset, iy * spacing - offset, iz * spacing - offset
                x1, y1, z1 = ix * spacing - offset, iy * spacing - offset, (iz + 1) * spacing - offset
                ax.plot([x0, x1], [y0, y1], [z0, z1], color="#475569", linewidth=1.2, alpha=0.6)

    ax.set_title(f"{material} Crystal Lattice", fontsize=14, color="#e2e8f0", pad=12)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    for label in ax.get_xticklabels() + ax.get_yticklabels() + ax.get_zticklabels():
        label.set_color("#94a3b8")
    ax.xaxis.label.set_color("#cbd5e1")
    ax.yaxis.label.set_color("#cbd5e1")
    ax.zaxis.label.set_color("#cbd5e1")
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.legend(loc="upper right", fontsize=10)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_standing_wave_png_base64(
    wave_x: Sequence[Number],
    depth_z: Sequence[Number],
    wave_z: Sequence[Sequence[Number]],
    title: str = "",
    *,
    dpi: int = 100,
) -> str:
    """Render standing wave field intensity heatmap as base64 PNG."""
    import numpy as np

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    z_arr = np.asarray(wave_z, dtype=float)
    x_arr = np.asarray(wave_x, dtype=float)
    y_arr = np.asarray(depth_z, dtype=float)

    fig = plt.Figure(figsize=(10, 6), dpi=dpi)
    fig.patch.set_facecolor("#131b30")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0f172a")

    im = ax.pcolormesh(x_arr, y_arr, z_arr, shading="auto", cmap="inferno")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Field Intensity (a.u.)", color="#cbd5e1")
    cbar.ax.yaxis.set_tick_params(color="#94a3b8")
    for label in cbar.ax.get_yticklabels():
        label.set_color("#94a3b8")

    t = title or "Standing Wave Field Intensity"
    ax.set_title(t, fontsize=14, color="#e2e8f0", pad=12)
    ax.set_xlabel(r"Wavenumber (cm$^{-1}$)", color="#cbd5e1")
    ax.set_ylabel("Film Depth (μm)", color="#cbd5e1")
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_color("#334155")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_dispersion_png_base64(
    disp_x: Sequence[Number],
    disp_n: Sequence[Number],
    disp_k: Sequence[Number],
    ref_n: Sequence[Number],
    upper_n: Sequence[Number],
    lower_n: Sequence[Number],
    title: str = "",
    *,
    dpi: int = 100,
) -> str:
    """Render n-k dispersion curves as base64 PNG."""
    import numpy as np

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    x_arr = np.asarray(disp_x, dtype=float)

    fig = plt.Figure(figsize=(10, 6), dpi=dpi)
    fig.patch.set_facecolor("#131b30")
    ax1 = fig.add_subplot(111)
    ax1.set_facecolor("#0f172a")
    ax2 = ax1.twinx()

    ax1.plot(x_arr, np.asarray(disp_n, dtype=float), color="#38bdf8", linewidth=2.5, label="n (refractive index)")
    ax1.plot(x_arr, np.asarray(ref_n, dtype=float), color="#94a3b8", linewidth=1.2, linestyle="dotted", label="Reference n")
    ax1.fill_between(
        x_arr,
        np.asarray(lower_n, dtype=float),
        np.asarray(upper_n, dtype=float),
        color="#38bdf8", alpha=0.12,
    )
    ax2.plot(x_arr, np.asarray(disp_k, dtype=float), color="#f43f5e", linewidth=2, linestyle="dashed", label="k (extinction)")

    t = title or "Complex Refractive Index Dispersion"
    ax1.set_title(t, fontsize=14, color="#e2e8f0", pad=12)
    ax1.set_xlabel(r"Wavenumber (cm$^{-1}$)", color="#cbd5e1")
    ax1.set_ylabel("Refractive Index n", color="#38bdf8")
    ax2.set_ylabel("Extinction Coefficient k", color="#f43f5e")
    ax1.tick_params(colors="#94a3b8")
    ax2.tick_params(colors="#94a3b8")
    for spine in ax1.spines.values():
        spine.set_color("#334155")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    leg = ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=10, frameon=True)
    leg.get_frame().set_facecolor("#111827")
    leg.get_frame().set_edgecolor("#334155")
    for t in leg.get_texts():
        t.set_color("#f8fafc")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

"""Population-weighted access-time CDF (pre vs post disaster)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


def _population_weighted_access_cdf(access, pop_f, valid_mask):
    """
    Population-weighted empirical CDF of ``access`` (hours).

    Uses only cells where ``valid_mask`` is True. Returns ``(x_step, y_step, pop_total)``
    suitable for ``ax.step(..., where='post')`` with leading (0, 0).
    """
    access = np.asarray(access, dtype=np.float64).ravel()
    pop_f = np.asarray(pop_f, dtype=np.float64).ravel()
    valid_mask = np.asarray(valid_mask, dtype=bool).ravel()
    access = access.copy()
    access[np.isneginf(access)] = np.nan

    m = valid_mask & np.isfinite(access) & (pop_f > 0)
    if not np.any(m):
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), 0.0

    a = access[m]
    w = pop_f[m]
    order = np.argsort(a, kind="mergesort")
    a_s = a[order]
    w_s = w[order]
    c = np.cumsum(w_s)
    total = float(c[-1])
    cdf = c / total if total > 0 else np.zeros_like(c, dtype=np.float64)

    x_step = np.concatenate([[0.0], a_s])
    y_step = np.concatenate([[0.0], cdf])
    return x_step, y_step, total


def _read_population_and_two_access_rasters(
    population_tiff_path, access_pre_tiff_path, access_post_tiff_path
):
    """
    Load population + pre/post access (band 1), validate alignment, return cleaned arrays.

    Returns
    -------
    a_pre, a_post, pop_f, crs, transform, h, w
    """
    with rasterio.open(access_pre_tiff_path) as pre_src:
        a_pre = np.asarray(pre_src.read(1), dtype=np.float64)
        transform = pre_src.transform
        crs = pre_src.crs
        h, w = a_pre.shape

    with rasterio.open(access_post_tiff_path) as post_src:
        a_post = np.asarray(post_src.read(1), dtype=np.float64)
        if a_post.shape != (h, w):
            raise ValueError(
                f"Post access shape {a_post.shape} must match pre access {(h, w)}."
            )
        if post_src.transform != transform:
            raise ValueError(
                "Post access transform must match the pre access TIFF for cell alignment."
            )
        if (crs is None) ^ (post_src.crs is None) or (
            crs is not None and post_src.crs is not None and crs != post_src.crs
        ):
            raise ValueError(
                "Post access CRS must match the pre access TIFF for cell alignment."
            )

    with rasterio.open(population_tiff_path) as p_src:
        pop = np.asarray(p_src.read(1), dtype=np.float64)
        if pop.shape != (h, w):
            raise ValueError(
                f"Population shape {pop.shape} must match access TIFF shape {(h, w)}."
            )
        if p_src.transform != transform:
            raise ValueError(
                "Population TIFF transform must match the access TIFF for cell alignment."
            )
        if (crs is None) ^ (p_src.crs is None) or (
            crs is not None and p_src.crs is not None and crs != p_src.crs
        ):
            raise ValueError(
                "Population TIFF CRS must match the access TIFF for cell alignment."
            )

    pop_f = np.nan_to_num(pop, nan=0.0, posinf=0.0, neginf=0.0)
    a_pre = a_pre.copy()
    a_post = a_post.copy()
    a_pre[np.isneginf(a_pre)] = np.nan
    a_post[np.isneginf(a_post)] = np.nan
    return a_pre, a_post, pop_f, crs, transform, h, w


def Func_Access_Time_Cdf_Pre_Post(
    population_tiff_path,
    access_pre_tiff_path,
    access_post_tiff_path,
    title=None,
    save_plot_path=None,
    max_access_plot_hours=None,
    xlim=None,
    ylim=None,
):
    """
    **Population-weighted cumulative distribution** of hospital access time (hours) for the same
    people grid under **pre-disaster** and **post-disaster** access rasters.

    All three GeoTIFFs must share **shape**, **transform**, and **CRS** (band 1). Population cells
    with non-positive weight are ignored. The CDF uses the **common** mask: finite access on
    **both** pre and post rasters and ``population > 0``, so the two curves refer to the same set
    of weighted individuals.

    Plot: **light green** = pre-disaster CDF, **dark green** = post-disaster CDF (same axes).

    Parameters
    ----------
    population_tiff_path : str or Path
        Population (people per cell), band 1.
    access_pre_tiff_path : str or Path
        Access time (hours) pre-disaster, band 1.
    access_post_tiff_path : str or Path
        Access time (hours) post-disaster, band 1.
    title : str, optional
        Figure title.
    save_plot_path : str or Path, optional
        If set, saves **JPEG** (``.jpg``), ``dpi=200``.
    max_access_plot_hours : float, optional
        If set and ``xlim`` is not, sets ``xlim`` to ``(0, max_access_plot_hours)`` (hours).
    xlim : tuple of float, optional
        ``(left, right)`` access-time axis limits in hours; crops the figure horizontally.
        If given, overrides ``max_access_plot_hours``.
    ylim : tuple of float, optional
        ``(bottom, top)`` cumulative-fraction limits; crops the figure vertically. Default is
        ``(0, 1.02)`` when omitted.

    Returns
    -------
    dict
        ``x_pre``, ``cdf_pre``, ``x_post``, ``cdf_post`` — step arrays; ``pop_total`` — denominator;
        ``n_cells`` — count of cells in the common mask.
    """
    a_pre, a_post, pop_f, crs, transform, h, w = _read_population_and_two_access_rasters(
        population_tiff_path, access_pre_tiff_path, access_post_tiff_path
    )

    common = np.isfinite(a_pre) & np.isfinite(a_post) & (pop_f > 0)
    n_cells = int(np.sum(common))
    pop_total = float(np.sum(pop_f[common]))

    x_pre, cdf_pre, tot_pre = _population_weighted_access_cdf(a_pre, pop_f, common)
    x_post, cdf_post, tot_post = _population_weighted_access_cdf(a_post, pop_f, common)

    if abs(tot_pre - tot_post) > 1e-6 * max(tot_pre, 1.0):
        raise RuntimeError("Internal CDF totals disagree; check population weighting.")

    print(
        f"CDF denominator: {pop_total:,.0f} people in {n_cells:,d} cells "
        "(finite pre & post access, pop > 0)."
    )

    fig, ax = plt.subplots(figsize=(9, 6), facecolor="white")
    ax.step(
        x_pre,
        cdf_pre,
        where="post",
        color="#90EE90",
        linewidth=2.0,
        label="Pre-disaster",
    )
    ax.step(
        x_post,
        cdf_post,
        where="post",
        color="#006400",
        linewidth=2.0,
        label="Post-disaster",
    )
    if xlim is not None:
        if len(xlim) != 2:
            raise ValueError("xlim must be (left, right) with two values (hours).")
        ax.set_xlim(float(xlim[0]), float(xlim[1]))
    elif max_access_plot_hours is not None:
        ax.set_xlim(0.0, float(max_access_plot_hours))
    else:
        ax.set_xlim(left=0.0)

    if ylim is not None:
        if len(ylim) != 2:
            raise ValueError("ylim must be (bottom, top) with two values (cumulative fraction).")
        ax.set_ylim(float(ylim[0]), float(ylim[1]))
    else:
        ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("Access time to hospital [hours]")
    ax.set_ylabel("Cumulative fraction of population")
    ax.grid(True, linestyle="--", linewidth=0.5, color="gray", alpha=0.6)
    ax.legend(loc="lower right", frameon=True)
    if title:
        ax.set_title(title)
    else:
        ax.set_title("Population-weighted CDF of access time (pre vs post)")
    plt.tight_layout()

    if save_plot_path is not None:
        out = Path(save_plot_path).with_suffix(".jpg")
        fig.savefig(out, format="jpeg", dpi=200, bbox_inches="tight", facecolor="white")
        print(f"CDF figure saved as {out}")

    plt.show()

    return {
        "x_pre": x_pre,
        "cdf_pre": cdf_pre,
        "x_post": x_post,
        "cdf_post": cdf_post,
        "pop_total": pop_total,
        "n_cells": n_cells,
    }

"""Population-weighted access-time CDF utilities for the modeling package."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


def _population_weighted_access_cdf(access, pop_f, valid_mask):
    """
    Population-weighted empirical CDF of access time in hours.

    Returns ``(x_step, y_step, pop_total)`` arrays suitable for
    ``ax.step(..., where="post")`` with a leading ``(0, 0)`` point.
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
    Load population + pre/post access rasters and validate grid alignment.

    Returns
    -------
    tuple
        ``(a_pre, a_post, pop_f)`` where all arrays are ``float64`` and
        ``-inf`` in access rasters is converted to ``NaN``.
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
                "Post access transform must match pre access TIFF for cell alignment."
            )
        if (crs is None) ^ (post_src.crs is None) or (
            crs is not None and post_src.crs is not None and crs != post_src.crs
        ):
            raise ValueError("Post access CRS must match pre access TIFF for cell alignment.")

    with rasterio.open(population_tiff_path) as pop_src:
        pop = np.asarray(pop_src.read(1), dtype=np.float64)
        if pop.shape != (h, w):
            raise ValueError(
                f"Population shape {pop.shape} must match access TIFF shape {(h, w)}."
            )
        if pop_src.transform != transform:
            raise ValueError(
                "Population transform must match access TIFF for cell alignment."
            )
        if (crs is None) ^ (pop_src.crs is None) or (
            crs is not None and pop_src.crs is not None and crs != pop_src.crs
        ):
            raise ValueError("Population CRS must match access TIFF for cell alignment.")

    pop_f = np.nan_to_num(pop, nan=0.0, posinf=0.0, neginf=0.0)
    a_pre = a_pre.copy()
    a_post = a_post.copy()
    a_pre[np.isneginf(a_pre)] = np.nan
    a_post[np.isneginf(a_post)] = np.nan
    return a_pre, a_post, pop_f


def Func_Access_Time_Cdf_Pre_Post(
    population_tiff_path,
    access_pre_tiff_path,
    access_post_tiff_path,
    title="CDF of Access time",
    save_plot_path=None,
    xlim=None,
    ylim=None,
):
    """
    Plot population-weighted CDFs of access time for pre and post scenarios.

    Parameters
    ----------
    population_tiff_path : str or Path
        Population raster path.
    access_pre_tiff_path : str or Path
        Normal/pre-disaster access-time raster path (hours).
    access_post_tiff_path : str or Path
        Landslide/post-disaster access-time raster path (hours).
    title : str, optional
        Figure title. Default is ``"CDF of Access time"``.
    save_plot_path : str or Path, optional
        If provided, save output as ``.jpg``.
    xlim : tuple(float, float), optional
        Explicit x-axis range in hours.
    ylim : tuple(float, float), optional
        Explicit y-axis range for cumulative fraction.

    Returns
    -------
    None
        Produces a CDF plot (and optionally saves it) without returning data.
    """
    a_pre, a_post, pop_f = _read_population_and_two_access_rasters(
        population_tiff_path, access_pre_tiff_path, access_post_tiff_path
    )

    common = np.isfinite(a_pre) & np.isfinite(a_post) & (pop_f > 0)

    x_pre, cdf_pre, tot_pre = _population_weighted_access_cdf(a_pre, pop_f, common)
    x_post, cdf_post, tot_post = _population_weighted_access_cdf(a_post, pop_f, common)

    if abs(tot_pre - tot_post) > 1e-6 * max(tot_pre, 1.0):
        raise RuntimeError("Internal CDF totals disagree; check input rasters.")

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
    else:
        ax.set_xlim(left=0.0)

    if ylim is not None:
        if len(ylim) != 2:
            raise ValueError("ylim must be (bottom, top) with two values.")
        ax.set_ylim(float(ylim[0]), float(ylim[1]))
    else:
        ax.set_ylim(0.0, 1.02)

    ax.set_xlabel("Access time to destination [h]")
    ax.set_ylabel("Cumulative share of population")
    ax.grid(True, linestyle="--", linewidth=0.5, color="gray", alpha=0.6)
    ax.legend(loc="lower right", frameon=True)
    ax.set_title(title if title else "Population-weighted CDF of access time")
    plt.tight_layout()

    if save_plot_path is not None:
        out = Path(save_plot_path).with_suffix(".jpg")
        fig.savefig(out, format="jpeg", dpi=200, bbox_inches="tight", facecolor="white")

    plt.show()

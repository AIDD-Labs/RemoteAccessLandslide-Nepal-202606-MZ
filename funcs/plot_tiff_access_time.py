"""Access-time and access-difference GeoTIFF maps with hazard overlay (modeling package)."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from rasterio.features import geometry_mask
from rasterio.transform import xy
from rasterio.warp import transform as warp_transform
from rasterio.warp import transform_bounds
from shapely.geometry import mapping
from shapely.ops import unary_union

# Discrete access-time bins (hours) and matching reversed-viridis palette.
_ACCESS_BIN_EDGES = np.array(
    [0.0, 0.1, 0.5, 1.0, 2.0, 3.0, 6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 72.0],
    dtype=np.float64,
)
_N_ACCESS_BINS = len(_ACCESS_BIN_EDGES) - 1
_ACCESS_PALETTE = plt.cm.viridis_r(np.linspace(0.0, 1.0, _N_ACCESS_BINS))

# Styling constants shared by raster cells and legend patches.
_WATER_RGBA = (0.82, 0.82, 0.84, 1.0)
_HAZARD_RGBA = (1.0, 127.0 / 255.0, 14.0 / 255.0, 1.0)
_INACCESSIBLE_LAND_RGBA = tuple(_ACCESS_PALETTE[-1])  # same as > 72 h bin

# Discrete access-increase bins (hours) for difference maps.
_DIFF_BIN_EDGES = np.array(
    [0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 12.0, 15.0, 18.0, 24.0],
    dtype=np.float64,
)
_N_DIFF_BINS = len(_DIFF_BIN_EDGES) - 1


def _get_mako_r_cmap():
    """Return mako_r colormap, preferring seaborn to match Func_Plot_Tiff_Access_Diff3."""
    try:
        import seaborn as sns

        return sns.color_palette("mako_r", _N_DIFF_BINS, as_cmap=True)
    except Exception:
        try:
            return plt.colormaps["mako_r"]
        except (AttributeError, KeyError, TypeError):
            return plt.cm.get_cmap("mako_r")


def _build_diff_palette():
    """
    Build diff palette like Func_Plot_Tiff_Access_Diff3: white, then light-to-dark blue.

    Uses discrete mako_r samples so increase colors stay in the blue range and do not
    overlap visually with the orange hazard overlay.
    """
    mako = _get_mako_r_cmap()
    mako_samples = mako(np.linspace(0.0, 1.0, _N_DIFF_BINS))
    palette = np.vstack(([1.0, 1.0, 1.0, 1.0], mako_samples[:-1]))
    palette[-1] = mako(1.0)
    return palette


_DIFF_PALETTE = _build_diff_palette()


def _read_aligned_band(path, ref_shape, ref_transform, ref_crs, label):
    """Read raster band 1 and verify it matches the access-time grid."""
    with rasterio.open(path) as src:
        data = np.asarray(src.read(1), dtype=np.float64)
        if data.shape != ref_shape:
            raise ValueError(
                f"{label} TIFF shape {data.shape} must match access TIFF {ref_shape}."
            )
        if src.transform != ref_transform:
            raise ValueError(
                f"{label} TIFF transform must match the access TIFF for cell alignment."
            )
        if (ref_crs is None) ^ (src.crs is None) or (
            ref_crs is not None and src.crs is not None and ref_crs != src.crs
        ):
            raise ValueError(
                f"{label} TIFF CRS must match the access TIFF for cell alignment."
            )
    return data


def _study_outside_mask(study_boundary, crs, transform, shape):
    """Boolean mask of raster cells outside the study boundary (False = inside)."""
    if study_boundary is None or crs is None:
        return np.zeros(shape, dtype=bool)

    boundary = gpd.read_file(str(study_boundary))
    if boundary.crs != crs:
        boundary = boundary.to_crs(crs)

    geom = unary_union(boundary.geometry)
    return geometry_mask(
        [mapping(geom)],
        out_shape=shape,
        transform=transform,
        all_touched=True,
        invert=False,
    )


def _plot_study_boundary_outline(ax, study_boundary, crs):
    """Draw study boundary as a light-grey outline (in WGS84 plot coordinates)."""
    if study_boundary is None:
        return

    boundary = gpd.read_file(str(study_boundary))
    if crs is not None and boundary.crs != crs:
        boundary = boundary.to_crs(crs)
    if boundary.crs is not None and boundary.crs.to_string() != "EPSG:4326":
        boundary = boundary.to_crs("EPSG:4326")

    boundary.boundary.plot(
        ax=ax,
        color="#bfbfbf",
        linewidth=1.0,
        zorder=30,
    )


def _plot_extent_wgs84(crs, bounds):
    """Return (left, right, bottom, top) in WGS84 degrees for imshow extent."""
    if crs is not None and crs.to_string() != "EPSG:4326":
        left, bottom, right, top = transform_bounds(crs, "EPSG:4326", *bounds)
    else:
        left, bottom, right, top = (
            bounds.left,
            bounds.bottom,
            bounds.right,
            bounds.top,
        )
    return left, right, bottom, top


def _apply_crop_lonlat(ax, crop_lonlat):
    """
    Zoom axes to ``[x_min, x_max, y_min, y_max]`` in lon/lat.

    Invalid or missing crop values are ignored so the map falls back to the
    full raster extent already set by ``imshow``.
    """
    if crop_lonlat is None:
        return

    try:
        xmin, xmax, ymin, ymax = (float(v) for v in crop_lonlat)
    except (TypeError, ValueError):
        return

    if xmin >= xmax or ymin >= ymax:
        return

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def _destination_lon_lat(destination_tiff_path, ref_shape, transform, crs):
    """
    Return destination marker coordinates (lon, lat lists) from a destination raster.

    Cells with finite value == 1 are treated as destination locations.
    """
    if destination_tiff_path is None:
        return [], []

    dest_data = _read_aligned_band(
        destination_tiff_path, ref_shape, transform, crs, "Destination"
    )
    dest_mask = np.isfinite(dest_data) & (dest_data == 1.0)
    if not np.any(dest_mask):
        return [], []

    rows, cols = np.nonzero(dest_mask)
    xs, ys = xy(transform, rows, cols, offset="center")
    if crs is not None and crs.to_string() != "EPSG:4326":
        lons, lats = warp_transform(crs, "EPSG:4326", xs, ys)
    else:
        lons, lats = xs, ys
    return list(lons), list(lats)


def _assign_diff_bins(diff, mask):
    """Map masked diff values to discrete palette indices."""
    bin_id = np.zeros(diff.shape, dtype=np.int32)
    for i in range(_N_DIFF_BINS):
        lo, hi = _DIFF_BIN_EDGES[i], _DIFF_BIN_EDGES[i + 1]
        bin_id[mask & (diff > lo) & (diff <= hi)] = i
    bin_id[mask & (diff > _DIFF_BIN_EDGES[-1])] = _N_DIFF_BINS - 1
    return bin_id


def Func_Plot_Access_Time_wHazard_Crop(
    tiff_path,
    hazard_tiff_path,
    colorbar_label="Access time [h]",
    title=None,
    save_path=None,
    study_boundary=None,
    water_tiff_path=None,
    destination_tiff_path=None,
    crop_lonlat=None,
):
    """
    Plot access time with hazard overlay, optional crop, and a compact legend.

    Parameters
    ----------
    tiff_path : str or Path
        Access-time GeoTIFF (band 1, hours).
    hazard_tiff_path : str or Path
        Hazard-impact mask aligned to the access raster (band 1 == 1 marks hazard cells).
    colorbar_label : str, optional
        Label for the discrete access-time colorbar.
    title : str or None, optional
        Optional map title.
    save_path : str or Path or None, optional
        If set, save a transparent PNG at 300 dpi.
    study_boundary : str or Path or None, optional
        GeoJSON polygon used to mask cells outside the study area (transparent).
    water_tiff_path : str or Path or None, optional
        Water mask aligned to the access raster (band 1 == 1 marks water).
    destination_tiff_path : str or Path or None, optional
        Destination raster aligned to the access raster (band 1 == 1 marks destinations).
    crop_lonlat : sequence or None, optional
        ``[x_min, x_max, y_min, y_max]`` in longitude/latitude (WGS84).
        If missing or invalid, the full raster extent is shown.

    Map styling
    -----------
    - Outside ``study_boundary``: transparent.
    - Access time **0** at a destination cell: white.
    - Finite access **0 < t <= 999 h**: discrete reversed viridis bins (through 72 h;
      values above 72 h use the top bin; colorbar extends for > 72 h).
    - Inaccessible land (NaN, +inf, or > 999 h, not water): **darkest palette color**
      (same as > 72 h), not black.
    - Water (mask == 1): light grey.
    - Hazard cells (mask == 1): orange overlay on top of other cell colors.
    - Destinations: white circle markers with black outline.
    - Study boundary: light grey outline (``#bfbfbf``).

    Legend (up to three items only)
    -------------------------------
    - White circle: destination
    - Grey patch: water surface
    - Orange patch: hazard affected area
    """
    with rasterio.open(tiff_path) as src:
        access = np.asarray(src.read(1), dtype=np.float64)
        crs = src.crs
        bounds = src.bounds
        transform = src.transform

    access[np.isneginf(access)] = np.nan
    height, width = access.shape

    # Optional aligned auxiliary layers.
    water_mask = None
    if water_tiff_path is not None:
        water_data = _read_aligned_band(
            water_tiff_path, (height, width), transform, crs, "Water"
        )
        water_mask = np.isfinite(water_data) & (water_data == 1.0)

    hazard_data = _read_aligned_band(
        hazard_tiff_path, (height, width), transform, crs, "Hazard"
    )
    hazard_mask = np.isfinite(hazard_data) & (hazard_data == 1.0)

    dest_lons, dest_lats = _destination_lon_lat(
        destination_tiff_path, (height, width), transform, crs
    )

    outside = _study_outside_mask(study_boundary, crs, transform, (height, width))
    inside = ~outside

    rgba = np.zeros((height, width, 4), dtype=np.float32)
    rgba[outside, :] = (0.0, 0.0, 0.0, 0.0)

    # Destination cells with zero access time render as white.
    zero_inside = inside & (access == 0)
    rgba[zero_inside, :] = (1.0, 1.0, 1.0, 1.0)

    # Inaccessible cells: grey on water, darkest bin on land (no isolated-black overlay).
    bad_cells = inside & (
        np.isnan(access) | np.isposinf(access) | (np.isfinite(access) & (access > 999.0))
    )
    if water_mask is None:
        grey_inside = np.zeros(bad_cells.shape, dtype=bool)
        rgba[bad_cells, :] = _INACCESSIBLE_LAND_RGBA
    else:
        grey_inside = bad_cells & water_mask
        land_bad = bad_cells & ~water_mask
        rgba[grey_inside, :] = _WATER_RGBA
        rgba[land_bad, :] = _INACCESSIBLE_LAND_RGBA

    # Finite positive access times use discrete reversed viridis bins.
    positive = inside & np.isfinite(access) & (access > 0) & (access <= 999.0)
    if np.any(positive):
        bin_id = np.zeros(access.shape, dtype=np.int32)
        for i in range(_N_ACCESS_BINS):
            lo, hi = _ACCESS_BIN_EDGES[i], _ACCESS_BIN_EDGES[i + 1]
            bin_id[positive & (access > lo) & (access <= hi)] = i
        bin_id[positive & (access > _ACCESS_BIN_EDGES[-1])] = _N_ACCESS_BINS - 1
        rgba[positive, :] = _ACCESS_PALETTE[bin_id[positive]]

    # Hazard footprint overwrites underlying cell styling.
    rgba[hazard_mask, :] = _HAZARD_RGBA

    left, right, bottom, top = _plot_extent_wgs84(crs, bounds)
    extent = (left, right, bottom, top)
    width_deg = right - left
    height_deg = top - bottom
    figsize = (10, 10 * height_deg / width_deg) if width_deg > 0 else (10, 8)

    fig = plt.figure(figsize=figsize, facecolor="none")
    ax = fig.add_subplot(111, facecolor="none")
    ax.imshow(rgba, extent=extent, origin="upper", interpolation="nearest")

    if dest_lons:
        ax.plot(
            dest_lons,
            dest_lats,
            linestyle="none",
            marker="o",
            markersize=5,
            markerfacecolor="white",
            markeredgecolor="black",
            markeredgewidth=1.2,
            zorder=10,
        )

    ax.grid(visible=True, linestyle="--", linewidth=0.5, color="gray", alpha=0.7)
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(False)

    if title:
        ax.set_title(title)

    if np.any(positive):
        cmap_cbar = ListedColormap(_ACCESS_PALETTE)
        norm_cbar = BoundaryNorm(_ACCESS_BIN_EDGES, cmap_cbar.N)
        sm = ScalarMappable(norm=norm_cbar, cmap=cmap_cbar)
        sm.set_array([])
        cbar = plt.colorbar(
            sm,
            ax=ax,
            orientation="vertical",
            fraction=0.03,
            pad=0.04,
            extend="max",
        )
        cbar.set_label(colorbar_label)
        cbar.set_ticks(_ACCESS_BIN_EDGES)
        cbar.set_ticklabels(
            ["0", "0.1", "0.5", "1", "2", "3", "6", "9", "12", "18", "24", "36", "48", "72"]
        )
        cbar.ax.tick_params(labelsize=8)

    # Compact legend: destination, water, hazard only.
    legend_handles = []
    if dest_lons:
        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                linestyle="none",
                marker="o",
                markersize=5,
                markerfacecolor="white",
                markeredgecolor="black",
                markeredgewidth=1.2,
                label="Destination",
            )
        )
    if water_tiff_path is not None and np.any(grey_inside):
        legend_handles.append(
            Patch(
                facecolor=_WATER_RGBA[:3],
                edgecolor="#555555",
                linewidth=0.8,
                label="Water surface",
            )
        )
    if np.any(hazard_mask):
        legend_handles.append(
            Patch(
                facecolor=_HAZARD_RGBA[:3],
                edgecolor="#555555",
                linewidth=0.8,
                label="Hazard affected area",
            )
        )

    if legend_handles:
        legend = ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=8)
        legend.get_frame().set_alpha(0.9)

    _apply_crop_lonlat(ax, crop_lonlat)
    plt.tight_layout()

    if save_path:
        out_path = Path(save_path).with_suffix(".png")
        plt.savefig(out_path, format="png", dpi=300, bbox_inches="tight", transparent=True)
        print(f"Plot saved as {out_path}")

    plt.show()


def Func_Plot_Access_Diff_wHazard_Crop(
    access_diff_tiff_path,
    hazard_tiff_path,
    study_boundary,
    destination_tiff_path=None,
    colorbar_label="Access Time Increase [h]",
    title=None,
    save_path=None,
    crop_lonlat=None,
):
    """
    Plot access-time increase with hazard overlay, study mask, and optional crop.

    Parameters
    ----------
    access_diff_tiff_path : str or Path
        GeoTIFF of access-time difference (landslide minus normal, hours).
    hazard_tiff_path : str or Path
        Hazard-impact mask aligned to the diff raster (band 1 == 1 marks hazard cells).
    study_boundary : str or Path
        GeoJSON polygon used to mask cells outside the study area (transparent).
    destination_tiff_path : str or Path or None, optional
        Destination raster aligned to the diff raster (band 1 == 1 marks destinations).
    colorbar_label : str, optional
        Label for the discrete increase colorbar.
    title : str or None, optional
        Optional map title.
    save_path : str or Path or None, optional
        If set, save a transparent PNG at 300 dpi.
    crop_lonlat : sequence or None, optional
        ``[x_min, x_max, y_min, y_max]`` in longitude/latitude (WGS84).
        If missing or invalid, the full raster extent is shown.

    Map styling
    -----------
    - Outside ``study_boundary``: transparent.
    - **0** increase: white.
    - **Finite increase > 0**: discrete ``mako_r`` blue palette (through 24 h; larger values use darkest blue).
    - **+inf** increase (e.g. newly unreachable vs. zero baseline): top bin color.
    - Hazard cells (mask == 1): orange overlay.
    - Destinations: white circle markers with black outline.
    - Study boundary: light grey outline (``#bfbfbf``).

    Legend
    ------
    - White circle: destination
    - Orange patch: hazard affected area
    """
    with rasterio.open(access_diff_tiff_path) as src:
        diff = np.asarray(src.read(1), dtype=np.float64)
        crs = src.crs
        bounds = src.bounds
        transform = src.transform

    diff[np.isneginf(diff)] = np.nan
    height, width = diff.shape

    hazard_data = _read_aligned_band(
        hazard_tiff_path, (height, width), transform, crs, "Hazard"
    )
    hazard_mask = np.isfinite(hazard_data) & (hazard_data == 1.0)

    dest_lons, dest_lats = _destination_lon_lat(
        destination_tiff_path, (height, width), transform, crs
    )

    outside = _study_outside_mask(study_boundary, crs, transform, (height, width))
    inside = ~outside

    rgba = np.zeros((height, width, 4), dtype=np.float32)
    rgba[outside, :] = (0.0, 0.0, 0.0, 0.0)

    white_inside = inside & (
        (diff == 0)
        | np.isnan(diff)
        | np.isneginf(diff)
        | (np.isfinite(diff) & (diff < 0))
    )
    rgba[white_inside, :] = (1.0, 1.0, 1.0, 1.0)

    positive = inside & np.isfinite(diff) & (diff > 0)
    if np.any(positive):
        bin_id = _assign_diff_bins(diff, positive)
        rgba[positive, :] = _DIFF_PALETTE[bin_id[positive]]

    unreachable = inside & np.isposinf(diff)
    rgba[unreachable, :] = _DIFF_PALETTE[-1]

    rgba[hazard_mask, :] = _HAZARD_RGBA

    left, right, bottom, top = _plot_extent_wgs84(crs, bounds)
    extent = (left, right, bottom, top)
    width_deg = right - left
    height_deg = top - bottom
    figsize = (10, 10 * height_deg / width_deg) if width_deg > 0 else (10, 8)

    fig = plt.figure(figsize=figsize, facecolor="none")
    ax = fig.add_subplot(111, facecolor="none")
    ax.imshow(rgba, extent=extent, origin="upper", interpolation="nearest")

    if dest_lons:
        ax.plot(
            dest_lons,
            dest_lats,
            linestyle="none",
            marker="o",
            markersize=5,
            markerfacecolor="white",
            markeredgecolor="black",
            markeredgewidth=1.2,
            zorder=10,
        )

    ax.grid(visible=True, linestyle="--", linewidth=0.5, color="gray", alpha=0.7)
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(False)

    if title:
        ax.set_title(title)

    plottable = inside & ((np.isfinite(diff) & (diff > 0)) | np.isposinf(diff))
    if np.any(plottable):
        cmap_cbar = ListedColormap(_DIFF_PALETTE)
        norm_cbar = BoundaryNorm(_DIFF_BIN_EDGES, cmap_cbar.N)
        sm = ScalarMappable(norm=norm_cbar, cmap=cmap_cbar)
        sm.set_array([])
        cbar = plt.colorbar(
            sm,
            ax=ax,
            orientation="vertical",
            fraction=0.03,
            pad=0.04,
            extend="max",
        )
        cbar.set_label(colorbar_label)
        cbar.set_ticks(_DIFF_BIN_EDGES)
        cbar.set_ticklabels(
            [
                "0",
                "0.1",
                "0.2",
                "0.3",
                "0.5",
                "0.75",
                "1",
                "2",
                "3",
                "5",
                "7.5",
                "10",
                "12",
                "15",
                "18",
                "24",
            ]
        )
        cbar.ax.tick_params(labelsize=8)

    legend_handles = []
    if dest_lons:
        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                linestyle="none",
                marker="o",
                markersize=5,
                markerfacecolor="white",
                markeredgecolor="black",
                markeredgewidth=1.2,
                label="Destination",
            )
        )
    if np.any(hazard_mask):
        legend_handles.append(
            Patch(
                facecolor=_HAZARD_RGBA[:3],
                edgecolor="#555555",
                linewidth=0.8,
                label="Hazard affected area",
            )
        )

    if legend_handles:
        legend = ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=8)
        legend.get_frame().set_alpha(0.9)

    _plot_study_boundary_outline(ax, study_boundary, crs)
    _apply_crop_lonlat(ax, crop_lonlat)
    plt.tight_layout()

    if save_path:
        out_path = Path(save_path).with_suffix(".png")
        plt.savefig(out_path, format="png", dpi=300, bbox_inches="tight", transparent=True)
        print(f"Plot saved as {out_path}")

    plt.show()

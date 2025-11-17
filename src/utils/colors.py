"""Colorblind-friendly color palettes and utilities for visualizations."""

from typing import Dict, List, Tuple

# Colorblind-friendly palette based on Wong (2011)
# These colors are distinguishable by people with common forms of color vision deficiency
COLORBLIND_PALETTE = {
    'blue': '#0072B2',       # Blue
    'orange': '#E69F00',     # Orange
    'green': '#009E73',      # Bluish green
    'yellow': '#F0E442',     # Yellow
    'sky_blue': '#56B4E9',   # Sky blue
    'vermillion': '#D55E00', # Vermillion (red-orange)
    'purple': '#CC79A7',     # Reddish purple
    'black': '#000000',      # Black
}

# Quality category colors
QUALITY_COLORS = {
    'good': COLORBLIND_PALETTE['green'],
    'review': COLORBLIND_PALETTE['orange'],
    'poor': COLORBLIND_PALETTE['vermillion'],
}

# Sequential color scale for heatmaps (colorblind-friendly)
SEQUENTIAL_COLORS = [
    '#f7fbff',  # Light
    '#deebf7',
    '#c6dbef',
    '#9ecae1',
    '#6baed6',
    '#4292c6',
    '#2171b5',
    '#08519c',
    '#08306b',  # Dark
]

# Diverging color scale (for correlation matrices)
DIVERGING_COLORS = [
    '#053061',  # Dark blue
    '#2166ac',
    '#4393c3',
    '#92c5de',
    '#d1e5f0',
    '#f7f7f7',  # White center
    '#fddbc7',
    '#f4a582',
    '#d6604d',
    '#b2182b',
    '#67001f',  # Dark red
]


def get_quality_color(quality: str) -> str:
    """Get the color for a quality category.

    Args:
        quality: One of 'good', 'review', 'poor'

    Returns:
        Hex color string
    """
    return QUALITY_COLORS.get(quality.lower(), COLORBLIND_PALETTE['black'])


def get_quality_colors_list() -> List[str]:
    """Get ordered list of quality colors for pie/bar charts.

    Returns:
        List of hex color strings in order: good, review, poor
    """
    return [
        QUALITY_COLORS['good'],
        QUALITY_COLORS['review'],
        QUALITY_COLORS['poor'],
    ]


def get_recommendation_color(current: float, recommended: float) -> str:
    """Get color based on weight recommendation difference.

    Args:
        current: Current weight value
        recommended: Recommended weight value

    Returns:
        Hex color string
    """
    diff = recommended - current
    if abs(diff) < 0.1:
        return COLORBLIND_PALETTE['green']  # Good - no change needed
    elif diff > 0:
        return COLORBLIND_PALETTE['blue']  # Increase recommended
    else:
        return COLORBLIND_PALETTE['vermillion']  # Decrease recommended


def get_discrimination_quality_color(discrimination: float) -> str:
    """Get color based on discrimination index quality.

    Args:
        discrimination: Discrimination index value

    Returns:
        Hex color string
    """
    if discrimination >= 0.3:
        return COLORBLIND_PALETTE['green']  # Excellent
    elif discrimination >= 0.2:
        return COLORBLIND_PALETTE['sky_blue']  # Good
    elif discrimination >= 0.1:
        return COLORBLIND_PALETTE['orange']  # Acceptable
    else:
        return COLORBLIND_PALETTE['vermillion']  # Poor


def create_quadrant_colors() -> Dict[str, str]:
    """Create colors for the 4-quadrant discrimination-difficulty plot.

    Returns:
        Dictionary mapping quadrant names to colors
    """
    return {
        'high_disc_high_diff': COLORBLIND_PALETTE['green'],    # Good - challenging but discriminating
        'high_disc_low_diff': COLORBLIND_PALETTE['sky_blue'],  # OK - easy but discriminating
        'low_disc_high_diff': COLORBLIND_PALETTE['orange'],    # Problem - hard and not discriminating
        'low_disc_low_diff': COLORBLIND_PALETTE['vermillion'], # Problem - easy and not discriminating
    }


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., '#0072B2')

    Returns:
        Tuple of (R, G, B) values (0-255)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color string.

    Args:
        rgb: Tuple of (R, G, B) values (0-255)

    Returns:
        Hex color string
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpolate between two colors.

    Args:
        color1: First hex color
        color2: Second hex color
        factor: Interpolation factor (0.0 = color1, 1.0 = color2)

    Returns:
        Interpolated hex color
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    interpolated = tuple(
        int(rgb1[i] + (rgb2[i] - rgb1[i]) * factor)
        for i in range(3)
    )

    return rgb_to_hex(interpolated)

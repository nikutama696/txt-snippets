"""Dynamic icon generation for txt-snippets."""

from PIL import Image, ImageDraw


def create_icon(size: int = 22) -> Image.Image:
    """
    Create a monochrome icon for the macOS menu bar.

    Args:
        size: Icon size in pixels (22 is standard for macOS menu bar)

    Returns:
        PIL Image object
    """
    # Create a transparent image
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Monochrome color for menu bar (black for light mode compatibility)
    # macOS will automatically adjust for dark mode
    color = (0, 0, 0, 255)

    # Draw a simple "T" shape for "Text"
    margin = size // 5
    bar_height = size // 6

    # Top horizontal bar of T
    draw.rectangle(
        [margin, margin, size - margin, margin + bar_height],
        fill=color,
    )

    # Vertical bar of T
    center_x = size // 2
    bar_width = size // 5
    draw.rectangle(
        [center_x - bar_width // 2, margin + bar_height,
         center_x + bar_width // 2, size - margin],
        fill=color,
    )

    return image


def create_icon_template(size: int = 22) -> Image.Image:
    """
    Create a template icon for macOS menu bar.
    Template icons should be black with alpha for proper dark/light mode support.

    Args:
        size: Icon size in pixels

    Returns:
        PIL Image object with alpha channel
    """
    return create_icon(size)

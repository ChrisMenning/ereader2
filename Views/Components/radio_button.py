from PIL import ImageDraw

def draw_radio_button(draw, center, radius, selected, outline=0, width=2, fill=0):
    """
    Draws a radio button at the given center (x, y).
    """
    x, y = center
    # Outer circle
    draw.ellipse(
        [(x - radius, y - radius), (x + radius, y + radius)],
        outline=outline, width=width
    )
    # Inner filled circle if selected
    if selected:
        fill_radius = radius // 2
        draw.ellipse(
            [(x - fill_radius, y - fill_radius), (x + fill_radius, y + fill_radius)],
            fill=fill
        )
from PIL import Image, ImageDraw, ImageFont
from Configs import epd7in5_V2

class EPaperDisplay:
    def partial_refresh_radio_buttons(self, y_offset, num_items, selected_index):
        """
        Perform a partial refresh of the radio button area in the library view.
        y_offset: index of the first visible item
        num_items: number of visible items (lines)
        selected_index: which item is selected (relative to y_offset)
        Also update the main framebuffer so it stays in sync with the display.
        """
        from Views.Components.radio_button import draw_radio_button
        THUMB_SIZE = 64
        LINE_HEIGHT = THUMB_SIZE + 10
        radio_radius = 12
        left_padding = 16
        radio_x = left_padding + radio_radius
        width = 2 * (radio_radius + 4)  # radio button + padding
        height = num_items * LINE_HEIGHT
        x0 = radio_x - radio_radius - 4
        y0 = 50
        x1 = radio_x + radio_radius + 4
        y1 = y0 + height
        x0_aligned = (x0 // 8) * 8
        x1_aligned = ((x1 + 7) // 8) * 8
        region_width = x1_aligned - x0_aligned
        region_height = y1 - y0

        # Create and draw the region for partial refresh
        img = Image.new("1", (region_width, region_height), 255)
        draw = ImageDraw.Draw(img)
        for i in range(num_items):
            y = (i * LINE_HEIGHT) + LINE_HEIGHT // 2
            selected = (i == selected_index)
            draw_radio_button(draw, (radio_x - x0_aligned, y), radio_radius, selected)
        # Rotate the region to match display orientation
        rotated_img = img.rotate(270, expand=True)
        # After rotation, region's top-left is at (y0, x0_aligned)
        buf = self.epd.getbuffer_region(rotated_img)
        self.epd.init_part()
        self.epd.display_Partial(buf, y0, x0_aligned, y1, x1_aligned)

        # --- ALSO update the main framebuffer (self.fb) ---
        # Draw the same radio buttons into the framebuffer
        fb_draw = self.draw
        for i in range(num_items):
            y = y0 + (i * LINE_HEIGHT) + LINE_HEIGHT // 2
            selected = (i == selected_index)
            fb_draw.rectangle(
                [(radio_x - radio_radius - 4, y - radio_radius - 4),
                 (radio_x + radio_radius + 4, y + radio_radius + 4)],
                fill=255
            )
            draw_radio_button(fb_draw, (radio_x, y), radio_radius, selected)

    def __init__(self):
        self.epd = epd7in5_V2.EPD()
        self.width = self.epd.height
        self.height = self.epd.width
        self.font_title = ImageFont.load_default()
        self.fb = Image.new("1", (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.fb)
        self.init_display()

    def init_display(self):
        self.epd.init()
        self.clear()

    def clear(self):
        self.fb.paste(255, (0, 0, self.width, self.height))
        self.epd.Clear()

    def clear_framebuffer(self):
        self.fb.paste(255, (0, 0, self.width, self.height))
        self.draw = ImageDraw.Draw(self.fb)

    def update_display(self, mode="1"):
        rotated_fb = self.fb.rotate(270, expand=True)
        if mode == "1":
            self.epd.display(self.epd.getbuffer(rotated_fb))
        elif mode == "4gray":
            self.epd.display_4Gray(self.epd.getbuffer_4Gray(rotated_fb))

    def sleep(self):
        self.epd.sleep()

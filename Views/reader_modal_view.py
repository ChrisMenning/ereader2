from PIL import Image, ImageDraw
from Views.Components.radio_button import draw_radio_button

MODAL_OPTIONS = [
    "Place Bookmark",
    "Go to Bookmark",
    "Back to Library",
    "Cancel"
]

THUMB_SIZE = 64
LINE_HEIGHT = THUMB_SIZE + 10
VISIBLE_OPTIONS = 4  # Adjust as needed for your modal

class ReaderModalView:
    def __init__(self, display):
        self.display = display

    def show_modal(self, selected_index):
        # Copy current framebuffer
        modal_fb = self.display.fb.copy()
        draw = ImageDraw.Draw(modal_fb)
        modal_width = self.display.width // 2
        modal_height = 32 * len(MODAL_OPTIONS) + 40
        modal_x = (self.display.width - modal_width) // 2
        modal_y = (self.display.height - modal_height) // 2

        # Modal background (white rectangle)
        draw.rectangle([modal_x, modal_y, modal_x + modal_width, modal_y + modal_height], fill=255, outline=0, width=2)
        draw.text((modal_x + 20, modal_y + 10), "Options", fill=0, font=self.display.font_title)

        # Options
        for i, option in enumerate(MODAL_OPTIONS):
            y = modal_y + 40 + i * 32
            selected = (i == selected_index)
            radio_x = modal_x + 20
            radio_y = y + 12
            radio_radius = 10
            draw_radio_button(draw, (radio_x, radio_y), radio_radius, selected)
            draw.text((radio_x + 2 * radio_radius + 8, y), option, fill=0, font=self.display.font_title)

        # Rotate modal_fb before displaying, just like update_display()
        rotated_fb = modal_fb.rotate(270, expand=True)
        self.display.epd.display(self.display.epd.getbuffer(rotated_fb))

    def get_options(self):
        return MODAL_OPTIONS

    def partial_refresh_radio_buttons(self, num_options, selected_index):
        # Modal geometry (must match show_modal)
        modal_width = self.display.width // 2
        modal_height = LINE_HEIGHT * num_options + 40
        modal_x = (self.display.width - modal_width) // 2
        modal_y = (self.display.height - modal_height) // 2

        radio_radius = 10
        radio_x = modal_x + 20
        y0 = modal_y + 40  # where the first radio button row starts
        x0 = radio_x - radio_radius - 4
        x1 = radio_x + radio_radius + 4
        y1 = y0 + num_options * LINE_HEIGHT

        x0_aligned = (x0 // 8) * 8
        x1_aligned = ((x1 + 7) // 8) * 8
        region_width = x1_aligned - x0_aligned
        region_height = y1 - y0

        img = Image.new("1", (region_width, region_height), 255)
        draw = ImageDraw.Draw(img)
        for i in range(num_options):
            y = (i * LINE_HEIGHT) + LINE_HEIGHT // 2
            selected = (i == selected_index)
            draw_radio_button(draw, (radio_x - x0_aligned, y), radio_radius, selected)
        rotated_img = img.rotate(270, expand=True)
        buf = self.display.epd.getbuffer_region(rotated_img)
        self.display.epd.init_part()
        self.display.epd.display_Partial(buf, y0, x0_aligned, y1, x1_aligned)
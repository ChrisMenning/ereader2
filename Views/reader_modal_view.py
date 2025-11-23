from PIL import ImageDraw

MODAL_OPTIONS = [
    "Place Bookmark",
    "Go to Bookmark",
    "Back to Library",
    "Cancel"
]

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
            draw.ellipse(
                [(radio_x - radio_radius, radio_y - radio_radius),
                 (radio_x + radio_radius, radio_y + radio_radius)],
                outline=0, width=2
            )
            if selected:
                draw.ellipse(
                    [(radio_x - radio_radius//2, radio_y - radio_radius//2),
                     (radio_x + radio_radius//2, radio_y + radio_radius//2)],
                    fill=0
                )
            draw.text((radio_x + 2 * radio_radius + 8, y), option, fill=0, font=self.display.font_title)

        # Rotate modal_fb before displaying, just like update_display()
        rotated_fb = modal_fb.rotate(270, expand=True)
        self.display.epd.display(self.display.epd.getbuffer(rotated_fb))

    def get_options(self):
        return MODAL_OPTIONS
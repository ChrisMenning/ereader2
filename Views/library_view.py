from PIL import Image
from Views.Components.radio_button import draw_radio_button

# Library View
THUMB_SIZE = 64
LINE_HEIGHT = THUMB_SIZE + 10

class LibraryView:
    def __init__(self, display):
        self.display = display

    def draw_library_item(self, book, index, selected):
        y = 10 + index * LINE_HEIGHT
        radio_radius = 12
        left_padding = 16
        radio_x = left_padding + radio_radius
        radio_y = y + LINE_HEIGHT // 2

        # Radio button background
        self.display.draw.rectangle(
            [(radio_x - radio_radius - 4, radio_y - radio_radius - 4),
             (radio_x + radio_radius + 4, radio_y + radio_radius + 4)],
            fill=255
        )
        draw_radio_button(self.display.draw, (radio_x, radio_y), radio_radius, selected)  # Use component

        # Thumbnail (convert to 1-bit for fast display)
        thumb = book.get("thumbnail", Image.new("1", (THUMB_SIZE, THUMB_SIZE), 255))
        if thumb.mode != "1":
            thumb = thumb.convert("1")
        self.display.fb.paste(thumb, (left_padding + 2 * radio_radius + 8, y))

        # Title
        title = book.get("title", "Unknown")
        self.display.draw.text(
            (left_padding + 2 * radio_radius + THUMB_SIZE + 24, y + 20),
            title, font=self.display.font_title, fill=0
        )

    def display_library(self, books, selected_index):
        self.display.clear_framebuffer()
        for i, book in enumerate(books):
            self.draw_library_item(book, i, i == selected_index)
        self.display.update_display(mode="1")  # This should use the 1-bit display method
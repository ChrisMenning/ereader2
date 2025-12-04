from PIL import Image
from Views.Components.radio_button import draw_radio_button

THUMB_SIZE = 64
LINE_HEIGHT = THUMB_SIZE + 10
VISIBLE_ITEMS = 10  # Number of items visible at once

class LibraryView:
    def __init__(self, display):
        self.display = display

    def draw_library_item(self, book, index, selected, y_offset):
        y = 10 + (index - y_offset) * LINE_HEIGHT
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
        draw_radio_button(self.display.draw, (radio_x, radio_y), radio_radius, selected)

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
        total_books = len(books)
        # Calculate the window of visible items
        if total_books <= VISIBLE_ITEMS:
            start = 0
            end = total_books
        else:
            # Center selected item in the window if possible
            half = VISIBLE_ITEMS // 2
            start = max(0, selected_index - half)
            end = start + VISIBLE_ITEMS
            if end > total_books:
                end = total_books
                start = end - VISIBLE_ITEMS
        for i in range(start, end):
            self.draw_library_item(books[i], i, i == selected_index, start)
        self.display.update_display(mode="1")
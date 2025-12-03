from PIL import Image

class CBZReaderView:
    def __init__(self, display):
        self.display = display

    def display_page(self, page_image, page_num=None, total_pages=None, cbz_filename=None):
        self.display.clear_framebuffer()
        self.display.fb.paste(page_image, (0, 0))

        # Draw footer
        footer_height = 36
        footer_y = self.display.height - footer_height
        self.display.draw.rectangle(
            [(0, footer_y), (self.display.width, self.display.height)],
            fill=255
        )

        footer_text = ""
        if cbz_filename:
            footer_text += cbz_filename
        if page_num is not None and total_pages is not None:
            footer_text += f" | Page {page_num + 1}/{total_pages}"

        self.display.draw.text(
            (20, footer_y + 8),
            footer_text,
            font=self.display.font_title,
            fill=0
        )

        self.display.update_display(mode="4gray")
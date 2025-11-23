from PIL import Image

class EpubReaderView:
    def __init__(self, display):
        self.display = display

    def display_page(self, page_image, book_title=None, chapter_title=None, page_num=None, total_pages=None, book_total_pages=None):
        self.display.clear_framebuffer()
        self.display.fb.paste(page_image, (0, 0))

        # Draw footer
        footer_height = 36
        footer_y = self.display.height - footer_height
        self.display.draw.rectangle(
            [(0, footer_y), (self.display.width, self.display.height)],
            fill=255
        )

        # Compose footer text
        footer_text = ""
        if book_title:
            footer_text += book_title
        if chapter_title:
            footer_text += " | " + chapter_title
        if page_num is not None and total_pages is not None:
            footer_text += f" | Page {page_num + 1}/{total_pages}"
        if book_total_pages is not None:
            footer_text += f" | Book: {book_total_pages} pages"

        self.display.draw.text(
            (20, footer_y + 8),
            footer_text,
            font=self.display.font_title,
            fill=0
        )

        self.display.update_display()

    def show_page(self, book_title, chapter_title):
        self.view.display_page(
            self.pages[self.current_page],
            book_title=book_title,
            chapter_title=chapter_title,
            page_num=self.current_page,
            total_pages=len(self.pages),
            book_total_pages=self.book_total_pages
        )
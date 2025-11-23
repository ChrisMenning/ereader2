from PIL import Image

class EpubReaderView:
    def __init__(self, display):
        self.display = display

    def display_page(self, page_image):
        self.display.clear_framebuffer()
        self.display.fb.paste(page_image, (0, 0))
        self.display.update_display()
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2

class EPaperDisplay:
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

    def update_display(self):
        rotated_fb = self.fb.rotate(270, expand=True)
        # Use 4-gray display method
        self.epd.display_4Gray(self.epd.getbuffer_4Gray(rotated_fb))

    def sleep(self):
        self.epd.sleep()

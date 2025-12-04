from PIL import Image, ImageDraw, ImageFont

class SplashScreenView:
    def __init__(self, display):
        self.display = display
        # Try to use a monospaced font; fallback to default if not found
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)
        except OSError:
            self.font = self.display.font_title

    def show(self):
        self.display.clear_framebuffer()
        splash_text_tome = (
            "     ███      ▄██████▄    ▄▄▄▄███▄▄▄▄      ▄████████        \n"                  
            " ▀█████████▄ ███    ███ ▄██▀▀▀███▀▀▀██▄   ███    ███        \n"                  
            "    ▀███▀▀██ ███    ███ ███   ███   ███   ███    █▀         \n"                  
            "     ███   ▀ ███    ███ ███   ███   ███  ▄███▄▄▄            \n"                  
            "     ███     ███    ███ ███   ███   ███ ▀▀███▀▀▀            \n"                  
            "     ███     ███    ███ ███   ███   ███   ███    █▄         \n"                 
            "     ███     ███    ███ ███   ███   ███   ███    ███        \n"                 
            "    ▄████▀    ▀██████▀   ▀█   ███   █▀    ██████████        \n"                 
        )
        splash_text_reader = (
            "   ▄████████    ▄████████    ▄████████ ████████▄     ▄████████    ▄████████  \n"
            "  ███    ███   ███    ███   ███    ███ ███   ▀███   ███    ███   ███    ███  \n"
            "  ███    ███   ███    █▀    ███    ███ ███    ███   ███    █▀    ███    ███  \n"
            " ▄███▄▄▄▄██▀  ▄███▄▄▄       ███    ███ ███    ███  ▄███▄▄▄      ▄███▄▄▄▄██▀  \n"
            "▀▀███▀▀▀▀▀   ▀▀███▀▀▀     ▀███████████ ███    ███ ▀▀███▀▀▀     ▀▀███▀▀▀▀▀    \n"
            "▀███████████   ███    █▄    ███    ███ ███    ███   ███    █▄  ▀███████████  \n"
            "  ███    ███   ███    ███   ███    ███ ███   ▄███   ███    ███   ███    ███  \n"
            "  ███    ███   ██████████   ███    █▀  ████████▀    ██████████   ███    ███  \n"
            "  ███    ███                                                     ███    ███  \n"
        )
        splash_subtitle = (
            "                                                                                                 \n"
            "  /\\  ._    o ._ _  ._  ._ _     o  _  _   _|    _ __ ._ _   _.  _|  _  ._    _|  _     o  _  _  \n"
            " /--\\ | |   | | | | |_) | (_) \\/ | _> (/_ (_|   (/_   | (/_ (_| (_| (/_ |    (_| (/_ \\/ | (_ (/_ \n"
            "                    |                                                                            \n"
        )

        # Draw TOME at the top, READER below, subtitle at the bottom
        y_tome = 30
        y_reader = y_tome + 8 * 12 + 10  # 8 lines * 12px + gap
        y_subtitle = y_reader + 9 * 12 + 20  # 9 lines reader * 12px + gap

        self.display.draw.multiline_text(
            (20, y_tome),
            splash_text_tome,
            font=self.font,
            fill=0,
            spacing=4
        )
        self.display.draw.multiline_text(
            (20, y_reader),
            splash_text_reader,
            font=self.font,
            fill=0,
            spacing=4
        )
        self.display.draw.multiline_text(
            (20, y_subtitle),
            splash_subtitle,
            font=self.font,
            fill=0,
            spacing=2
        )

        self.display.update_display()
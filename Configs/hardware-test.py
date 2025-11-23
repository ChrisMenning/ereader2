#!/usr/bin/env python3

import time
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO

from waveshare_epd import epd7in5_V2

# Rotary encoder GPIO pins
CLK = 29
DT = 31
SW = 33

def setup_encoder():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main():
    setup_encoder()
    epd = epd7in5_V2.EPD()
    print("Init...")
    epd.init()
    epd.Clear()

    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)

    text = "Hello, World!"
    font = ImageFont.load_default()

    # Use textbbox instead of textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    x = (epd.width - w) // 2
    y = (epd.height - h) // 2

    draw.text((x, y), text, font=font, fill=0)

    print("Display...")
    epd.display(epd.getbuffer(image))

    last_clk = GPIO.input(CLK)
    try:
        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)
            sw_state = GPIO.input(SW)
            if clk_state != last_clk:
                if dt_state != clk_state:
                    print("Rotated right")
                else:
                    print("Rotated left")
                last_clk = clk_state
            if sw_state == 0:
                print("Button pressed")
                time.sleep(0.2)  # Debounce
            time.sleep(0.01)
    except KeyboardInterrupt:
        GPIO.cleanup()
        epd.sleep()
        print("Done.")

if __name__ == "__main__":
    main()
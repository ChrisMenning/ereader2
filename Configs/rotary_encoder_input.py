import RPi.GPIO as GPIO

# Rotary encoder GPIO pins
CLK = 29
DT = 31
SW = 33

def setup_encoder():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
from flask import Flask, render_template, request
import Adafruit_BBIO.GPIO as GPIO
import threading
import time
import os

# Setup GPIO pins for the LED
led_pins = ["USR0", "USR1", "USR2", "USR3"]

# Initialize the GPIO pins
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)

# Flask App Setup
app = Flask(__name__)

# Global state for the LED pattern
led_pattern = ""

# Lock to handle thread safety
led_lock = threading.Lock()

# LED control functions
def led_on():
    for pin in led_pins:
        GPIO.output(pin, GPIO.HIGH)

def led_off():
    for pin in led_pins:
        GPIO.output(pin, GPIO.LOW)

def led_single(index, state):
    if state:
        GPIO.output(led_pins[index], GPIO.HIGH)
    else:
        GPIO.output(led_pins[index], GPIO.LOW)

def set_led_pattern(pattern):
    """Function to safely update the global LED pattern."""
    with led_lock:
        global led_pattern
        led_pattern = pattern

# Flask Route to set LED pattern
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        led = request.form.get("led")
        set_led_pattern(led)
    return render_template("index.html")

# Function to handle the LED pattern in a separate thread
def led_control_loop():
    current_time = time.time()
    led_state = 0
    circle_dir = 0
    circle_state = 0b0000

    while True:
        with led_lock:
            pattern = led_pattern

        if pattern == "on":
            led_on()
        elif pattern == "off":
            led_off()
        elif pattern == "blink":
            if time.time() - current_time > 0.5:  # Blink rate
                led_state = 1 - led_state  # Toggle state
                if led_state:
                    led_on()
                else:
                    led_off()
                current_time = time.time()
        elif pattern == "circle":
            if time.time() - current_time > 0.1:
                if circle_state == 0b1111:
                    circle_dir = 1
                elif circle_state == 0b0000:
                    circle_dir = 0
                
                if circle_dir == 1:
                    circle_state -= 0b1
                else:
                    circle_state += 0b1

                for i in range(4):
                    led_single(i, (circle_state >> i) & 0b1)

                current_time = time.time()

# Start the LED control loop in a separate thread
def start_led_thread():
    t = threading.Thread(target=led_control_loop, daemon=True)
    t.start()

if __name__ == '__main__':
    # Start the background thread for LED control
    start_led_thread()
    
    # Run the Flask app
    print(f"Flask app is running at: {os.getcwd()}")
    app.run(host="0.0.0.0", port=88, debug=True)

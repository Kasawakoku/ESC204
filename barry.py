import time
import board
import busio
import digitalio
import adafruit_am2320

# ---------------- CONFIGURATION ---------------- #
TEMP_THRESHOLD = 25.0  # Celsius threshold to trigger behavior change
STEP_DELAY = 0.002     # Speed of the motor (lower is faster). Each step will take 2 x 0.002 seconds.

# ---------------- PIN SETUP ---------------- #
# 1. AM2320 Sensor Setup (I2C)
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_am2320.AM2320(i2c)

# 2. PIR Sensor Setup (PRETENDING THIS IS A DIGITAL LIGHT SENSOR)
pir = digitalio.DigitalInOut(board.D4)
pir.direction = digitalio.Direction.INPUT

# 3. TMC2209 Stepper Driver Setup
step_pin = digitalio.DigitalInOut(board.D5)
step_pin.direction = digitalio.Direction.OUTPUT

dir_pin = digitalio.DigitalInOut(board.D6)
dir_pin.direction = digitalio.Direction.OUTPUT

enable_pin = digitalio.DigitalInOut(board.D13)
enable_pin.direction = digitalio.Direction.OUTPUT
enable_pin.value = False  # Set to False to ENABLE the TMC2209 driver

# ---------------- FUNCTIONS ---------------- #
def move_motor(steps, direction_forward=True):
    """Moves the stepper motor a specific number of steps."""
    dir_pin.value = direction_forward
    for _ in range(steps):
        step_pin.value = True
        time.sleep(STEP_DELAY)
        step_pin.value = False
        time.sleep(STEP_DELAY)

# ---------------- MAIN LOOP ---------------- #
print("Starting Conveyor System...")

while True:
    try:
        # 1. Read Sensor Data
        current_temp = sensor.temperature
        light_detected = pir.value # Pretending PIR returns True for Day, False for Night
        
        # Determine Mode based on our pretend light sensor
        is_day_mode = light_detected 
        
        # 2. Execute Logic Based on Modes
        if is_day_mode:
            # Day Mode Behavior
            if current_temp > TEMP_THRESHOLD: # Swapped the trigger to be temperature-based
                print(f"Day Mode: Light detected! Temp: {current_temp}C. Moving conveyor forward.")
                move_motor(steps=200, direction_forward=True) # 200 steps = 1 revolution for Nema 17
            else:
                pass # Waiting for temperature trigger
                
        else:
            # Night Mode Behavior
            if current_temp > TEMP_THRESHOLD:
                print(f"Night Mode: It is dark. Temp: {current_temp}C. Moving conveyor slowly.")
                # Maybe change speed or distance for night mode
                STEP_DELAY = 0.005 # slower
                move_motor(steps=100, direction_forward=False) # Reverse direction?
                STEP_DELAY = 0.002 # reset speed
                
        time.sleep(0.5) # Brief pause to prevent overloading the CPU

    except Exception as e:
        # The AM2320 sometimes throws read errors, so we catch them to prevent crashes
        print(f"Sensor read error: {e}")
        time.sleep(2)
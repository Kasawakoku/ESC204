import time
import board
import busio
import digitalio
import adafruit_am2320

# ---------------- CONFIGURATION ---------------- #
HOT_TEMP_THRESHOLD = 25.5  # Celsius threshold to trigger hot mode 
COLD_TEMP_THRESHOLD = 23  # Celsius threshold to trigger cold mode
# need to look back on Joburg temperature. Ideally switch should be daily
PIR_THRESHOLD = 0.5   # Placeholder threshold for PIR sensor (if we were using it as a light sensor)
STEP_DELAY = 0.002     # Speed of the motor (lower is faster). Each step will take 2 x 0.002 seconds.


# HEATING_COEFFICIENT = 1.2 # Calibration constant. Degrees (C) to subtract per 1.0V of light reading.
# Finding the actual value may require experimentation. Hard

# ---------------- PIN SETUP ---------------- #
# 1. AM2320 Sensor Setup (I2C)
i2c = busio.I2C(board.GP17, board.GP16)
sensor = adafruit_am2320.AM2320(i2c)

'''
# 2. PIR Sensor Setup (PRETENDING THIS IS A DIGITAL LIGHT SENSOR)
pir = digitalio.DigitalInOut(board.D4) # should change
pir.direction = digitalio.Direction.INPUT

# 3. Photoresistor Setup (Using your native analogio code)
photoresistor_pin = board.GP26_A0 # can change
photoresistor = analogio.AnalogIn(photoresistor_pin)
ADC_REF = photoresistor.reference_voltage

# 4. TMC2209 Stepper Driver Setup
step_pin = digitalio.DigitalInOut(board.D5) # should change
step_pin.direction = digitalio.Direction.OUTPUT

dir_pin = digitalio.DigitalInOut(board.D6) # should change
dir_pin.direction = digitalio.Direction.OUTPUT

enable_pin = digitalio.DigitalInOut(board.D13) # should change
enable_pin.direction = digitalio.Direction.OUTPUT
enable_pin.value = False  # Set to False to ENABLE the TMC2209 driver
'''

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

# Start in hot mode
is_hot_mode = True
# Rely on temperature
# If temperature value is sus (eg. extreme value, error, hasnt change a long time, prevent reflections?)
# try to do light sensor as backup.
# reflectivity of material? add to temperature for "effective temperature"?
# but light sensor might be easier?
# after switching modes, should only run once

while True:
    try:
        # 1. Read Sensor Data
        current_temp = sensor.temperature
        
        # pir_value = pir.value
        pir_value = None # for without pir sensor
        
        # --- CALCULATE ADJUSTED TEMPERATURE ---
        # ldr_voltage = adc_to_voltage(photoresistor.value)
        # Calculate the compensation. We use max(0, ...) so we don't accidentally add heat in the dark.
        # temp_compensation = max(0, ldr_voltage * HEATING_COEFFICIENT)
        # adjusted_temp = current_temp - temp_compensation
        #
        # For the logic below, you would replace 'current_temp' with 'adjusted_temp'
        # e.g., if adjusted_temp > HOT_TEMP_THRESHOLD and not is_hot_mode:
        
        # Determine Mode based on our pretend light sensor

        
        
        # 2. Execute Logic Based on Modes
        if current_temp > HOT_TEMP_THRESHOLD and not is_hot_mode: 
                print(f"Hot Mode Triggered: Temp: {current_temp}C. PIR Value: {pir_value}. Moving conveyor forward.")
                #move_motor(steps=200, direction_forward=True) # 200 steps = 1 revolution for Nema 17
                is_hot_mode = True

        elif current_temp < COLD_TEMP_THRESHOLD and is_hot_mode:
                print(f"Cold Mode Triggered: Temp: {current_temp}C. PIR Value: {pir_value}. Moving conveyor backward.")
                #move_motor(steps=200, direction_forward=False) # Move in reverse
                is_hot_mode = False

        else:
            if is_hot_mode:
                print(f"Hot Mode: No mode change. Current Temp: {current_temp}C. PIR Value: {pir_value}.")
            else:
                print(f"Cold Mode: No mode change. Current Temp: {current_temp}C. PIR Value: {pir_value}.")

        time.sleep(5) # Pause to prevent overloading the CPU
        '''
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
        '''

        

    except Exception as e:
        # The AM2320 sometimes throws read errors, so we catch them to prevent crashes
        print(f"Sensor read error: {e}")
        time.sleep(2)
import time
import board
import busio
import digitalio
import adafruit_am2320
import analogio

# ---------------- CONFIGURATION ---------------- #
HOT_TEMP_THRESHOLD = 24  # Internal Celsius threshold 
COLD_TEMP_THRESHOLD = 21  # Internal Celsius threshold
# Internal temperature should be kept between 18C and 27C.

PIR_THRESHOLD = 0.5   # Threshold for PIR sensor 
STEP_DELAY = 0.002     # Speed of the motor (lower is faster). Each step will take 2 x 0.002 seconds.
MOTOR_STEPS = 7500 # Steps to turn from bottom to top empirically determined

DAY_LIGHT_THRESHOLD = 10000  # Determined experimentally.
NIGHT_LIGHT_THRESHOLD = 15000  # Determined experimentally. 
# Note: Night threshold is higher as darkness causes a greater resistance.

CONTINUOUS_MODE = False # if true, spin continuously.


# ---------------- PIN SETUP ---------------- #
# 1. AM2320 Sensor Setup (I2C)
i2c_1 = busio.I2C(board.GP17, board.GP16) # i2c0
top_sensor = adafruit_am2320.AM2320(i2c_1)

i2c_2 = busio.I2C(board.GP19, board.GP18) # i2c1
bottom_sensor = adafruit_am2320.AM2320(i2c_2)

# 2. TMC2209 Stepper Driver Setup
step_pin = digitalio.DigitalInOut(board.GP5) 
step_pin.direction = digitalio.Direction.OUTPUT

dir_pin = digitalio.DigitalInOut(board.GP6) 
dir_pin.direction = digitalio.Direction.OUTPUT

enable_pin = digitalio.DigitalInOut(board.GP13) 
enable_pin.direction = digitalio.Direction.OUTPUT
enable_pin.value = False  # Set to False to ENABLE the TMC2209 driver

# 3. PIR Sensor Setup 
pir = digitalio.DigitalInOut(board.GP4) 
pir.direction = digitalio.Direction.INPUT

# 4. Photoresistor Setup 
photoresistor_pin = board.GP26_A0
photoresistor = analogio.AnalogIn(photoresistor_pin)
#ADC_REF = photoresistor.reference_voltage

# ---------------- FUNCTIONS ---------------- #
def move_motor(steps, direction_forward=True):
    # Moves the stepper motor a specific number of steps.
    dir_pin.value = direction_forward
    for _ in range(steps):
        step_pin.value = True
        time.sleep(STEP_DELAY)
        step_pin.value = False
        time.sleep(STEP_DELAY)

# ---------------- MAIN LOOP ---------------- #
print("Starting Conveyor System...")

# Start in hot mode. Change if initial conditions different during testing.
is_hot_mode = True
# Hot mode means we are exposing the paraffin wax, or have the insulation layer at the bottom
should_be_hot_mode = True
is_day = True

while True:
    if CONTINUOUS_MODE: # for verification testing
        print("Continuous Mode: Spinning conveyor indefinitely.")
        move_motor(steps=MOTOR_STEPS, direction_forward=False) # Spin backwards continuously
        time.sleep(5) # Short pause to prevent CPU overload

    else:
        try:
            # ---------------- READ SENSOR DATA  ---------------- #


            pir_value = pir.value
            # pir_value = None # for without pir testing
            photoresistor_value = photoresistor.value

            outside_temp = top_sensor.temperature
            measured_outside_temp = outside_temp
            
            outside_temp += (photoresistor_value/(-2500)+8) 
            # Temperature adjustment to account for the effect of sunlight exposure on the temperature of the material
            # Under the current conversion, when it is ambient indoor birhgtness (simulating average day conditions) the temperature will rise by ~5 degrees.
            # When the resister is covered (simulating night) the temperature will rise by 0C
            inside_temp = bottom_sensor.temperature
            
            # ---------------- DETERMINE DAY/NIGHT VIA PHOTORESISTOR  ---------------- #

            print(f"Photoresistor Value: {photoresistor.value}.")

            if photoresistor_value > NIGHT_LIGHT_THRESHOLD and is_day:
                is_day = False
                print("No daylight detected. Changing to Night state.")
            elif photoresistor_value < DAY_LIGHT_THRESHOLD and not is_day:
                is_day = True
                print("Daylight detected. Changing to Day state.")

            else:
                if is_day:
                    print("Daylight detected. No change in state.")
                else:
                    print("No daylight detected. No change in state.")

            # ---------- DETERMINE DESIRED MODE VIA INTERNAL/EXTERNAL TEMPERATURE AND LIGHT  ---------- #


            print(f"Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Inside Temp : {inside_temp}C.")

            if inside_temp < COLD_TEMP_THRESHOLD : 
                # need heating
                if outside_temp > inside_temp or is_day:
                    # can get heat from either hot outside air or the sun. Charge for the night.
                    print("DEMAND (HEAT): Harvesting environmental heat.")
                    should_be_hot_mode = True
                else:
                    # heat the house using the stored heat.
                    print("DEMAND (HEAT): Cold & dark outside. Heating house with trapped heat.")
                    should_be_hot_mode = False

            elif inside_temp > HOT_TEMP_THRESHOLD:
                # need cooling
                if outside_temp < inside_temp and not is_day:
                    # need both cool outside air and darkness to effectively cool, so only cool if both are present. 
                    print("DEMAND (COOL): Dumping heat to cool night sky.")
                    should_be_hot_mode = False
                else:
                    print("DEMAND (COOL): Hot or sunny outside. Harvest heat.")
                    should_be_hot_mode = True

            else:
                # DEMAND: Satisfied (21C to 24C)
                # Play it very safe since we don't know the season. "Opportunity Zone"
                if is_day or outside_temp > HOT_TEMP_THRESHOLD:
                    # It is day or hot. Charge the battery.
                    print("OPPORTUNITY: Harvesting sun for the future.")
                    should_be_hot_mode = True
                else: 
                    # It is dark and cold. Provide heat to maintain the comfortable temperature.
                    print("OPPORTUNITY: Cold & dark outside. Locking down.")
                    should_be_hot_mode = False

            # ---------------- DETERMINE WHETHER TO MOVE MOTOR  ---------------- #


            if should_be_hot_mode and not is_hot_mode:
                    print(f"Hot Mode Triggered. Moving conveyor.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=False) # 200 steps = 1 revolution for Nema 17. Always move in reverse
                    print("Rotation complete.")
                    is_hot_mode = True

            elif not should_be_hot_mode and is_hot_mode:
                    print(f"Cold Mode Triggered. Moving conveyor.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=False) # Move in reverse
                    print("Rotation complete.")
                    is_hot_mode = False

            else:
                if is_hot_mode:
                    print(f"Hot Mode: No mode change.")
                else:
                    print(f"Cold Mode: No mode change.")

            time.sleep(5) # Pause to prevent overloading the CPU

        except Exception as e:
            # The AM2320 sometimes throws read errors, so we catch them to prevent crashes
            print(f"Sensor read error: {e}")
            time.sleep(2)

import time
import board
import busio
import digitalio
import adafruit_am2320
import analogio

# ---------------- CONFIGURATION ---------------- #
HOT_TEMP_THRESHOLD = 24  # Internal Celsius threshold to trigger hot mode 
COLD_TEMP_THRESHOLD = 21  # Internal Celsius threshold to trigger cold mode
PIR_THRESHOLD = 0.5   # Placeholder threshold for PIR sensor (if we were using it as a light sensor)
STEP_DELAY = 0.002     # Speed of the motor (lower is faster). Each step will take 2 x 0.002 seconds.
MOTOR_STEPS = 7500 # Steps to turn from bottom to top empirically determined

DAY_LIGHT_THRESHOLD = 10000
NIGHT_LIGHT_THRESHOLD = 15000


CONTINUOUS_MODE = False # if true, spin continuously.

# HEATING_COEFFICIENT = 1.2 # Calibration constant. Degrees (C) to subtract per 1.0V of light reading.
# Finding the actual value may require experimentation. Hard

# ---------------- PIN SETUP ---------------- #
# 1. AM2320 Sensor Setup (I2C)
i2c_1 = busio.I2C(board.GP17, board.GP16) # i2c0
top_sensor = adafruit_am2320.AM2320(i2c_1)

i2c_2 = busio.I2C(board.GP19, board.GP18) #i2c1
bottom_sensor = adafruit_am2320.AM2320(i2c_2)



# 2. TMC2209 Stepper Driver Setup
step_pin = digitalio.DigitalInOut(board.GP5) # should change
step_pin.direction = digitalio.Direction.OUTPUT

dir_pin = digitalio.DigitalInOut(board.GP6) # should change
dir_pin.direction = digitalio.Direction.OUTPUT

enable_pin = digitalio.DigitalInOut(board.GP13) # should change
enable_pin.direction = digitalio.Direction.OUTPUT
enable_pin.value = False  # Set to False to ENABLE the TMC2209 driver

# 3. PIR Sensor Setup (PRETENDING THIS IS A DIGITAL LIGHT SENSOR)
pir = digitalio.DigitalInOut(board.GP4) # should change
pir.direction = digitalio.Direction.INPUT

# 4. Photoresistor Setup (Using your native analogio code)
photoresistor_pin = board.GP26_A0
photoresistor = analogio.AnalogIn(photoresistor_pin)
#ADC_REF = photoresistor.reference_voltage


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
# means we are exposing the paraffin wax
should_be_hot_mode = True

is_day = True

# Rely on temperature
# If temperature value is sus (eg. extreme value, error, hasnt change a long time, prevent reflections?)
# try to do light sensor as backup.
# reflectivity of material? add to temperature for "effective temperature"?
# but light sensor might be easier?
# after switching modes, should only run once

while True:
    if CONTINUOUS_MODE: # for verification testing
        print("Continuous Mode: Spinning conveyor indefinitely.")
        
        move_motor(steps=MOTOR_STEPS, direction_forward=False) # Spin backwards continuously
        time.sleep(5) # Short pause to prevent CPU overload

    else:
        try:
            # 1. Read Sensor Data
            outside_temp = top_sensor.temperature
            measured_outside_temp = outside_temp
            photoresistor_value = photoresistor.value
            outside_temp += (photoresistor_value/(-2500)+8) #temperature adjustment to account for the effect of sunlight exposure on the temperature of the material
            #under the current conversion, when it is ambiant indoor birhgtness (simulating average day temp) the temperaturewill rise by ~5 degrees. When the resister is covered (simulating night) the temperature will rise by 0C
            pir_value = pir.value
            #pir_value = None #for without pir testing
            inside_temp = bottom_sensor.temperature

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



            print(f"Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Inside Temp : {inside_temp}C.")

            if inside_temp < COLD_TEMP_THRESHOLD : 
                # need heating
                if outside_temp > inside_temp or is_day:
                    # can get heat from either hot outside air or the sun
                    print("DEMAND (HEAT): Harvesting environmental heat.")
                    should_be_hot_mode = True
                else:
                    print("DEMAND (HEAT): Cold & dark outside. Trapping heat.")
                    should_be_hot_mode = False

            elif inside_temp > HOT_TEMP_THRESHOLD:
                # need cooling
                if outside_temp < inside_temp and not is_day:
                    # need both cool outside air and darkness to effectively cool, so only cool if both are present. 
                    print("DEMAND (COOL): Dumping heat to cool night sky.")
                    should_be_hot_mode = False
                else:
                    print("DEMAND (COOL): Hot or sunny outside. Shielding house.")
                    should_be_hot_mode = True

            else:
                # DEMAND: Satisfied (21C to 24C)
                # Play it very safe since we don't know the season. "Opportunity Zone"
                if is_day and outside_temp < HOT_TEMP_THRESHOLD:
                    # It is sunny and the air won't overheat us. Charge the battery!
                    print("OPPORTUNITY: Harvesting sun for the future.")
                    should_be_hot_mode = True
                else:
                    # It is dark, raining, or hot. Lock down the comfortable house.
                    print("OPPORTUNITY: No clear advantage. Locking down.")
                    should_be_hot_mode = False

            if should_be_hot_mode and not is_hot_mode:
                    print(f"Hot Mode Triggered. Moving conveyor forward.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=False) # 200 steps = 1 revolution for Nema 17. always move in reverse
                    print("Rotation complete.")
                    is_hot_mode = True
            elif not should_be_hot_mode and is_hot_mode:
                    print(f"Cold Mode Triggered. Moving conveyor backward.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=False) # Move in reverse
                    print("Rotation complete.")
                    is_hot_mode = False
            else:
                if is_hot_mode:
                    print(f"Hot Mode: No mode change.")
                else:
                    print(f"Cold Mode: No mode change.")
                    

            '''
            

            if outside_temp > HOT_TEMP_THRESHOLD and not is_hot_mode: 
                    print(f"Hot Mode Triggered. Moving conveyor forward. \n Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Photoresistor Value: {photoresistor.value}. \n Inside Temp : {inside_temp}C.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=True) # 200 steps = 1 revolution for Nema 17
                    print("Rotation complete.")
                    is_hot_mode = True

            elif outside_temp < COLD_TEMP_THRESHOLD and is_hot_mode:
                    print(f"Cold Mode Triggered. Moving conveyor backward. \n Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Photoresistor Value: {photoresistor.value}. \n Inside Temp : {inside_temp}C.")
                    move_motor(steps=MOTOR_STEPS, direction_forward=False) # Move in reverse
                    print("Rotation complete.")
                    is_hot_mode = False

            else:
                if is_hot_mode:
                    print(f"Hot Mode: No mode change. \n Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Photoresistor Value: {photoresistor.value}. \n Inside Temp : {inside_temp}C.")
                else:
                    print(f"Cold Mode: No mode change. \n Measured Outside Temp: {measured_outside_temp}C. Adjusted Outside Temp: {outside_temp}C. Photoresistor Value: {photoresistor.value}. \n Inside Temp : {inside_temp}C.")

            
            '''
            '''
            we are not using this....
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

            time.sleep(5) # Pause to prevent overloading the CPU

            

        except Exception as e:
            # The AM2320 sometimes throws read errors, so we catch them to prevent crashes
            print(f"Sensor read error: {e}")
            time.sleep(2)

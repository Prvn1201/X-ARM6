"""
Project Name: 3D PRINTING APPLICATION USING XARM6
COURSE CODE: BFM4503 ROBOTICS FOR ENGINEER 
Team Members : 1. RONALD LEE DENG
               2. PRAVIN THIRUCHELVAM 
               3. LOO HUI KIE
               4. TANG GUI HONG
               5. RHESYAN NAIDU SOMU NAIDU 

"""
#!/usr/bin/env python3
import sys
import time
from xarm import version         
from xarm.wrapper import XArmAPI
from concurrent.futures import ThreadPoolExecutor

# Connect to the robot arm
arm = XArmAPI('192.168.1.233')
arm.clean_warn()
arm.clean_error()
arm.motion_enable(True)
arm.set_mode(0)
arm.set_state(0)
time.sleep(0)

params = {'speed': 100, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': {}, 'quit': False}

# Offsets
xo = 270
yo = 0
zo = 208.5

# Register error/warn changed callback
def error_warn_change_callback(data):
    if data and data['error_code'] != 0:
        arm.set_state(4)
        params['quit'] = True
        print('err={}, quit'.format(data['error_code']))
        arm.release_error_warn_changed_callback(error_warn_change_callback)
arm.register_error_warn_changed_callback(error_warn_change_callback)

# Register state changed callback
def state_changed_callback(data):
    if data and data['state'] == 4:
        params['quit'] = True
        print('state=4, quit')
        arm.release_state_changed_callback(state_changed_callback)
arm.register_state_changed_callback(state_changed_callback)

# Register counter value changed callback
if hasattr(arm, 'register_count_changed_callback'):
    def count_changed_callback(data):
        print('counter val: {}'.format(data['count']))
    arm.register_count_changed_callback(count_changed_callback)

params['speed'] = 20
params['acc'] = 2000

# Robot arm initial position
if arm.error_code == 0 and not params['quit']:
    if arm.set_position(*[228.0, 0.0, 285.0, 0.0, -90.0, 180.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
        params['quit'] = True

# Move robot arm up a bit
if arm.error_code == 0 and not params['quit']:
    if arm.set_position(*[228.0, 0.0, 385.0, 0.0, -90.0, 180.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
        params['quit'] = True

# File path for tgtrip.txt
tgtrip_file_path = "/home/uf/.UFACTORY/projects/test/xarm6/python/nope/tgtrip.txt"

# Define a function for moving the robot
def move_robot(x, y, z, first_move=False, second_move=False):
    x_new = x + xo
    y_new = y + yo
    z_new = z + zo

    print(f"Moving to position: x={x_new}, y={y_new}, z={z_new}")
    if first_move:
        # Move to the first position and hold for 5 seconds
        if arm.set_position(x_new, y_new, z_new, 0.0, -90.0, 180.0, speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
            params['quit'] = True
        print("Holding at the first coordinate for 5 seconds.")
        time.sleep(5)
    elif second_move:
        # Set pin 5 to high when reaching the second position
        if arm.set_cgpio_digital(5, 1) != 0:
            params['quit'] = True
        print("Pin 5 set to HIGH.")
        if arm.set_position(x_new, y_new, z_new, 0.0, -90.0, 180.0, speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
            params['quit'] = True
    else:
        # Move to subsequent positions
        if arm.set_position(x_new, y_new, z_new, 0.0, -90.0, 180.0, speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
            params['quit'] = True

# Optimized file reading and processing with threading
try:
    with open(tgtrip_file_path, 'r') as file:
        lines_batch = []
        line_count = 0
        with ThreadPoolExecutor(max_workers=3) as executor:  
            for line in file:
                lines_batch.append(line.strip())
                if len(lines_batch) >= 3:  # Process 3 lines at once
                    # Submit tasks for concurrent execution
                    for batch_line in lines_batch:
                        if params['quit']:
                            break
                        try:
                            # Parse x, y, z values from the line
                            values = batch_line.split()
                            if len(values) != 3:
                                print(f"Invalid line format: {batch_line}")
                                continue

                            x, y, z = map(float, values)
                            line_count += 1

                            # Add offsets and submit the move task to the executor
                            if line_count == 1:
                                move_robot(x, y, z, first_move=True)
                            elif line_count == 2:
                                move_robot(x, y, z, second_move=True)
                            else:
                                executor.submit(move_robot, x, y, z)
                        except ValueError as e:
                            print(f"Error parsing line: {batch_line} - {e}")

                    # Clear batch after submitting
                    lines_batch = []
except FileNotFoundError:
    print(f"File not found: {tgtrip_file_path}")

# Set pin 5 to low when program finishes
if not params['quit']:
    if arm.set_cgpio_digital(5, 0) != 0:
        params['quit'] = True
    print("Pin 5 set to LOW.")

    # Move the robot back to the initial position
    print("Moving back to the initial position.")

if arm.error_code == 0 and not params['quit']:
    if arm.set_position(*[228.0, 0.0, 385.0, 0.0, -90.0, 180.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
        params['quit'] = True
if arm.error_code == 0 and not params['quit']:
    if arm.set_position(*[228.0, 0.0, 285.0, 0.0, -90.0, 180.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
        params['quit'] = True

# Release callbacks
arm.release_error_warn_changed_callback(error_warn_change_callback)
arm.release_state_changed_callback(state_changed_callback)
if hasattr(arm, 'release_count_changed_callback'):
    arm.release_count_changed_callback(count_changed_callback)

print("Program finished.")
# stepper_motor.py - A python module to control a stepper motor.
# Created by ClayXrex, April 10, 2023.
# Released into the public domain.
# Do with this as you please.

import RPi.GPIO as GPIO
import time

class StepperMotor():

    def __init__(self, enable_pin, direction_pin, pulse_pin, steps_per_revolution, max_rpm=None, hold_position=True):

        # Set pin numbering mode.
        GPIO.setmode(GPIO.BCM)

        self.enable_pin = enable_pin
        self.direction_pin = direction_pin
        self.pulse_pin = pulse_pin

        # Setup control pins.
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.pulse_pin, GPIO.OUT)

        # Is used to calculate the delay between steps based on desired rpm.
        self.steps_per_revolution = steps_per_revolution

        # If defined during initialization this later prevents the user from trying to spin the motor too fast.
        self.max_rpm = max_rpm

        self.hold_position = hold_position # Default value is True.
        if self.hold_position:
            GPIO.output(self.enable_pin, GPIO.LOW)
        else:
            GPIO.output(self.enable_pin, GPIO.HIGH)

        self.steps_from_home = None
        # Steps are always counted clockwise.
        # Example:
        # If the stepper motor moves 10 steps away from home clockwise self.steps_from_home will read 10.
        # If the stepper motor moves 10 steps away from home counterclockwise self.steps_from_home will read (self.steps_per_revolution - 10).
        # Once self.steps_from_home reaches self.steps_per_revolution it is set back to 0.

    def step(self, steps, turn_clockwise, rpm):

        if self.max_rpm != None:
            if rpm > self.max_rpm:
                raise ValueError('Desired rpm is higher than max_rpm')

        if turn_clockwise:
            GPIO.output(self.direction_pin, GPIO.HIGH)
        else:
            GPIO.output(self.direction_pin, GPIO.LOW)

        # Enable stepper motor.
        GPIO.output(self.enable_pin, GPIO.LOW)
        
        delay_in_seconds = self.calculate_delay_from_rpm(rpm)

        for i in range(steps):
            
            GPIO.output(self.pulse_pin, GPIO.HIGH)
            time.sleep(delay_in_seconds)
            GPIO.output(self.pulse_pin, GPIO.LOW)
            time.sleep(delay_in_seconds)

            self.update_position(turn_clockwise=turn_clockwise)

        if not self.hold_position:
            # Disable stepper motor.
            GPIO.output(self.enable_pin, GPIO.HIGH)

    def do_one_rotation(self, turn_clockwise, rpm):
        self.step(steps=self.steps_per_revolution, turn_clockwise=turn_clockwise, rpm=rpm)

    def rotate(self, rotations, turn_clockwise, rpm): 
        self.step(steps=(rotations * self.steps_per_revolution), turn_clockwise=turn_clockwise, rpm=rpm)

    def calculate_delay_from_rpm(self, rpm):

        # time_per_revolution is in seconds.
        time_per_revolution = 60 / rpm 

        delay_in_seconds = time_per_revolution / (self.steps_per_revolution * 2)
        
        return delay_in_seconds

    def set_current_position_as_home(self):
        self.steps_from_home = 0

    def update_position(self, turn_clockwise):
        # This method should be called after every single step.

        if self.steps_from_home == None: # Home position has not been set.
            return
        
        if turn_clockwise:
            self.steps_from_home += 1
            if self.steps_from_home == self.steps_per_revolution: # The stepper motor has reached its home position again.
                self.steps_from_home = 0                
        else:
            if self.steps_from_home == 0: # The stepper motor is at its home position.
                self.steps_from_home = self.steps_per_revolution
            self.steps_from_home -= 1

    def go_to_position(self, turn_clockwise, rpm, steps_relative_to_home=None, degree=None):
        '''
        The position of the stepper motor can be described either by the number of steps from its home position or its angle of rotation from its home position.
        DO NOT pass values for both arguments at the same time!
        The value of steps_relative_to_home has to be between 0 and self.steps_per_revolution.
        The value of degree has to be between 0 and 360.
        '''

        if self.steps_from_home == None:
            raise AttributeError('Cannot go to position if home position has not been set -> self.steps_from home is set to None.')

        # Check for correct user input.
        if steps_relative_to_home == None and degree == None:
            raise ValueError('No argument for steps_relative_to_home or degree was given.')
        if steps_relative_to_home != None and degree!= None:
            raise ValueError('Only specify steps_relative_to_home or degree. Not both at the same time.')

        # User input seems to be correct. Now follow instructions.
        if degree != None:
            if degree < 0 or degree > 360:
                raise IndexError('Value for degree has to be between 0 and 360.')
            # Calculate if value given for degree is a multiple of the motors step angle.
            step_angle = 360 / self.steps_per_revolution
            if (degree / step_angle) != int(degree / step_angle):
                raise ValueError('Value given for degree is not a multiple of the motors step angle.')

            # Calculate step position from given angle.
            steps_relative_to_home = int(degree / step_angle)
            # Since step_angle can be a float the division might return a float.
            # Due to the check above the float will always have a 0 behind the decimal point -> No data is lost by converting to an int.
            
        if steps_relative_to_home == self.steps_from_home: # Motor is already at desired position.
            return

        if steps_relative_to_home < 0 or steps_relative_to_home > (self.steps_per_revolution - 1): # self.steps_per_revolution is the same as 0 steps
            raise IndexError('Value given for steps_relative_to_home exceeds self.steps_per_revolution.')

        # Compare self.steps_from_home (current position) to steps_relative_to_home (position to move to).
        # Calculate number of steps needed to reach steps_relative_to_home respecting the desired direction of rotation.
        if turn_clockwise:
            if steps_relative_to_home > self.steps_from_home:
                self.step(steps=(steps_relative_to_home - self.steps_from_home), turn_clockwise=True, rpm=rpm)
            else:
                self.step(steps=(self.steps_per_revolution - self.steps_from_home + steps_relative_to_home), turn_clockwise=True, rpm=rpm)
        else:
            if steps_relative_to_home > self.steps_from_home:
                self.step(steps=(self.steps_from_home + (self.steps_per_revolution - steps_relative_to_home)), turn_clockwise=False, rpm=rpm)
            else:
                self.step(steps=(self.steps_from_home - steps_relative_to_home), turn_clockwise=False, rpm=rpm)

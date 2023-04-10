from stepper_motor import StepperMotor

def main():

    stepper_motor = StepperMotor(enable_pin=17, direction_pin=27, pulse_pin=22, steps_per_revolution=200, max_rpm=630, hold_position=True)

    stepper_motor.step(steps=1000, turn_clockwise=True, rpm=60)

if __name__ == "__main__":
    main()
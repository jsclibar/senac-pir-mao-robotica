from pyfirmata2 import Arduino, SERVO
import time

# Define the servo pins and their movement angles
servos = {
    9: 120,   # Finger 1
    10: 120,  # Finger 2
    11: 160,  # Finger 3
    12: 160,  # Finger 4
    13: 120   # Finger 5
}

# Ask how many tests to perform
number_tests = int(
    input("Input how many times you want to test the fingers: "))

# Connect to the Arduino
board = Arduino('/dev/cu.usbserial-A5069RR4')


# Move a servo to a specific angle
def servo_activate(pin, angle):
    board.digital[pin].write(angle)

try:
    # Configure the pins as servos
    for pin in servos:
        board.digital[pin].mode = SERVO

    # Move all fingers to the initial position
    for pin in servos:
        servo_activate(pin, 0)

    time.sleep(1)

    # Repeat the tests
    for test in range(number_tests):

        print(f"Starting test {test + 1} of {number_tests}")

        # Test each finger individually
        for pin, angle in servos.items():
            servo_activate(pin, angle)
            time.sleep(1)

            servo_activate(pin, 0)
            time.sleep(1)

finally:
    # Close the connection to the Arduino
    board.exit()

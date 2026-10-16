from pyfirmata2 import Arduino, SERVO
import time

# Connect to the Arduino
board = Arduino('/dev/cu.usbserial-A5069RR4')

# Define the servo pins and their movement angles
servos = {
    9: 120,   # Finger 1
    10: 120,  # Finger 2
    11: 160,  # Finger 3
    12: 160,  # Finger 4
    13: 120   # Finger 5
}

# Configure the pins as servos
for pin in servos:
    board.digital[pin].mode = SERVO


# Move a servo to a specific angle
def servo_activate(pin, angle):
    board.digital[pin].write(angle)


# Open or close a finger
def abrir_fechar(pin, on_off):
    if on_off == 1:
        servo_activate(pin, 0)
    elif on_off == 0:
        servo_activate(pin, servos[pin])


# Test all fingers individually
def testeTodos():
    # Move all fingers to the initial position
    for pin in servos:
        servo_activate(pin, 0)

    time.sleep(1)

    # Test each finger individually
    for pin, angle in servos.items():
        servo_activate(pin, angle)
        time.sleep(1)

        servo_activate(pin, 0)
        time.sleep(1)

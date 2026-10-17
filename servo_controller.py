# Importa as ferramentas para comunicação e controle dos servomotores no Arduino.
from pyfirmata2 import Arduino, SERVO

# Importa a biblioteca para controlar pausas na execução do programa.
import time

# Porta de comunicação com o Arduino (macOS)
# Para Windows, utilize algo como 'COM3', 'COM4', etc.
comunication_port = '/dev/cu.usbserial-A5069RR4'

# Estabelece a comunicação serial com o Arduino utilizando o protocolo Firmata.
# A variável board representa a conexão com a placa.
board = Arduino(comunication_port)

# Dicionário que associa cada pino do Arduino ao ângulo de fechamento do dedo.
# As chaves representam os pinos e os valores representam os ângulos em graus.
servos = {
    9: 120,   # Dedo 1
    10: 120,  # Dedo 2
    11: 160,  # Dedo 3
    12: 160,  # Dedo 4
    13: 120   # Dedo 5
}

# Percorre os pinos definidos no dicionário servos (9, 10, 11, 12 e 13).
# Configura cada pino no modo SERVO para controlar um servomotor.
for pin in servos:
    board.digital[pin].mode = SERVO


# Função que movimenta um servomotor até o ângulo desejado.
# pin: pino digital do Arduino.
# angle: ângulo de movimentação, em graus.
# O método write() envia o comando ao Arduino.
def servo_activate(pin, angle):
    board.digital[pin].write(angle)


# Controla a abertura e o fechamento de um dedo.
# on_off = 1: abre o dedo, posicionando o servomotor em 0°.
# on_off = 0: fecha o dedo, utilizando o ângulo definido no dicionário servos.
def open_close(pin, on_off):
    if on_off == 1:
        servo_activate(pin, 0)
    elif on_off == 0:
        servo_activate(pin, servos[pin])

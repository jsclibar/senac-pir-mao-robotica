from pyfirmata2 import Arduino, SERVO
import time

# Estabelece a comunicação serial com o Arduino utilizando o protocolo Firmata.
# A porta informada corresponde ao Arduino conectado ao macOS.
board = Arduino('/dev/cu.usbserial-A5069RR4')

# Define os pinos digitais utilizados e os ângulos de fechamento dos dedos.
# Cada chave representa um pino do Arduino e seu valor representa o
# ângulo que o servomotor deverá atingir ao fechar o dedo.
servos = {
    9: 120,   # Dedo 1
    10: 120,  # Dedo 2
    11: 160,  # Dedo 3
    12: 160,  # Dedo 4
    13: 120   # Dedo 5
}

# Configura os pinos digitais para controlar servomotores.
# O modo SERVO permite enviar comandos de posicionamento angular.
for pin in servos:
    board.digital[pin].mode = SERVO


# Envia ao Arduino um comando para posicionar o servomotor
# conectado ao pino informado no ângulo desejado.
def servo_activate(pin, angle):
    board.digital[pin].write(angle)


# Controla a abertura e o fechamento de um dedo.
# on_off = 1: abre o dedo, posicionando o servomotor em 0°.
# on_off = 0: fecha o dedo, utilizando o ângulo definido no dicionário servos.
def abrir_fechar(pin, on_off):
    if on_off == 1:
        servo_activate(pin, 0)
    elif on_off == 0:
        servo_activate(pin, servos[pin])


# Executa uma sequência de testes para verificar o funcionamento
# individual dos cinco servomotores da mão robótica.
def testeTodos():

    # Posiciona todos os dedos em 0° antes de iniciar os testes.
    # Aguarda 1 segundo para permitir que os motores alcancem
    # suas posições iniciais.
    for pin in servos:
        servo_activate(pin, 0)

    time.sleep(1)

    # Movimenta cada servomotor individualmente até seu ângulo
    # de fechamento, aguarda 1 segundo e retorna à posição inicial.
    # A pausa seguinte permite que o dedo termine de abrir
    # antes do teste do próximo servomotor.
    for pin, angle in servos.items():
        servo_activate(pin, angle)
        time.sleep(1)

        servo_activate(pin, 0)
        time.sleep(1)

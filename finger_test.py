# Importa as ferramentas para comunicação e controle dos servomotores no Arduino.
from pyfirmata2 import Arduino, SERVO

# Importa a biblioteca para controlar pausas na execução do programa.
import time

# Porta de comunicação com o Arduino (macOS)
# Para Windows, utilize algo como 'COM3', 'COM4', etc.
comunication_port = '/dev/cu.usbserial-A5069RR4'

# Dicionário que associa os pinos digitais do Arduino aos ângulos dos servomotores.
# As chaves representam os pinos e os valores representam os ângulos em graus.
# Exemplo: 9: 120 movimenta o servo conectado ao pino 9 até 120 graus.
servos = {
    9: 120,   # Dedo 1
    10: 120,  # Dedo 2
    11: 160,  # Dedo 3
    12: 160,  # Dedo 4
    13: 120   # Dedo 5
}

# Solicita ao usuário a quantidade de testes que deseja realizar.
number_tests = int(input("Input how many times you want to test the fingers: "))

# Estabelece a comunicação serial com o Arduino utilizando o protocolo Firmata.
# A variável board representa a conexão com a placa.
board = Arduino(comunication_port)


# Função que movimenta um servomotor até o ângulo desejado.
# pin: pino digital do Arduino.
# angle: ângulo de movimentação, em graus.
# O método write() envia o comando ao Arduino.
def servo_activate(pin, angle):
    board.digital[pin].write(angle)


# O bloco try executa a configuração e movimentação dos servomotores.
# O finally garante o encerramento da comunicação com o Arduino, mesmo em caso de erro.
try:

    # Percorre os pinos definidos no dicionário servos (9, 10, 11, 12 e 13).
    # Configura cada pino no modo SERVO para controlar um servomotor.
    for pin in servos:
        board.digital[pin].mode = SERVO

    # Posiciona todos os servomotores em 0 grau, individualmente.
    # Na mão robótica, essa é a posição inicial dos dedos.
    for pin in servos:
        servo_activate(pin, 0)

    # Pausa a execução por 1 segundo para que os servomotores
    # alcancem suas posições iniciais antes dos testes.
    time.sleep(1)

    # Repete os testes conforme a quantidade informada pelo usuário.
    # range(number_tests) controla o número de repetições.
    # test + 1 exibe a numeração dos testes começando em 1.
    for test in range(number_tests):
        print(f"Starting test {test + 1} of {number_tests}")

        # Percorre o dicionário servos com items(), obtendo o pino e o ângulo.
        # Exemplo: pin = 9 e angle = 120.
        for pin, angle in servos.items():

            # Envia o comando para movimentar o servomotor
            servo_activate(pin, angle)

            # Aguarda 1 segundo antes de enviar o próximo comando.
            time.sleep(1)

            # Envia o comando para retornar o servomotor
            # à posição inicial de 0 graus.
            servo_activate(pin, 0)

            # Aguarda mais 1 segundo antes de iniciar
            # o teste do próximo servomotor.
            time.sleep(1)

finally:
    board.exit()
from pyfirmata2 import Arduino, SERVO
import time

# Dicionário que define os pinos digitais do Arduino e os ângulos
# de movimentação de cada servomotor.
#
# As chaves representam os números dos pinos digitais do Arduino.
# Os valores representam os ângulos, em graus, utilizados para fechar os dedos.
#
# Exemplo: 9: 120 significa que o servomotor conectado ao pino 9
# será movimentado até a posição de 120 graus.
servos = {
    9: 120,   # Dedo 1
    10: 120,  # Dedo 2
    11: 160,  # Dedo 3
    12: 160,  # Dedo 4
    13: 120   # Dedo 5
}

# Solicita ao usuário a quantidade de testes que deseja realizar.
number_tests = int(
    input("Input how many times you want to test the fingers: "))

# Estabelece a comunicação serial entre o Python e o Arduino.
# O PyFirmata2 utiliza o protocolo Firmata para enviar comandos à placa.
#
# O endereço informado corresponde à porta serial do Arduino no macOS.
# No Windows, normalmente seria necessário utilizar COM3, COM4 etc.
#
# A variável board representa a conexão estabelecida com o Arduino.
board = Arduino('/dev/cu.usbserial-A5069RR4')


# Define uma função para movimentar um servomotor.
#
# Parâmetros:
# pin: número do pino digital ao qual o servomotor está conectado.
# angle: posição, em graus, para a qual o servomotor deve se movimentar.
#
# O método write() envia ao Arduino o comando de posicionamento.
# O servomotor começa a se movimentar em direção ao ângulo solicitado.
# A função não aguarda o motor terminar fisicamente o movimento.
def servo_activate(pin, angle):
    board.digital[pin].write(angle)


# O bloco try executa a configuração e os movimentos dos servomotores.
# Mesmo que ocorra um erro durante essas operações, o bloco finally
# será executado para encerrar a comunicação com o Arduino.
try:

    # Percorre as chaves do dicionário servos, ou seja, os pinos:
    # 9, 10, 11, 12 e 13.
    #
    # Para cada pino, configura seu modo de funcionamento como SERVO.
    # Isso informa ao Arduino que o pino será utilizado para
    # controlar um servomotor.
    for pin in servos:
        board.digital[pin].mode = SERVO

    # Coloca todos os servomotores na posição inicial de 0 graus.
    #
    # O comando é enviado individualmente para cada pino.
    # Os motores não precisam terminar seus movimentos antes
    # de o próximo comando ser enviado.
    #
    # No projeto da mão robótica, 0 grau corresponde à posição
    # inicial dos dedos.
    for pin in servos:
        servo_activate(pin, 0)

    # Pausa a execução do Python por 1 segundo.
    # Essa pausa permite que os servomotores tenham tempo
    # para alcançar suas posições iniciais antes dos testes.
    time.sleep(1)

    # Repete a sequência completa de testes conforme a
    # quantidade informada pelo usuário.
    #
    # A função range(number_tests) determina quantas vezes
    # o bloco de comandos será executado.
    #
    # A variável test começa em 0, por isso utilizamos test + 1
    # para mostrar a numeração começando em 1 no terminal.
    for test in range(number_tests):

        print(f"Starting test {test + 1} of {number_tests}")

        # Percorre o dicionário servos utilizando o método items().
        #
        # Em cada repetição:
        # pin recebe o número do pino digital.
        # angle recebe o ângulo configurado para aquele servomotor.
        #
        # Exemplo da primeira repetição:
        # pin = 9
        # angle = 120
        #
        # Cada servomotor é testado individualmente.
        for pin, angle in servos.items():

            # Envia o comando para movimentar o servomotor
            # até o ângulo definido no dicionário.
            servo_activate(pin, angle)

            # Aguarda 1 segundo antes de enviar o próximo comando.
            # Esse intervalo permite que o motor execute o movimento.
            time.sleep(1)

            # Envia o comando para retornar o servomotor
            # à posição inicial de 0 graus.
            servo_activate(pin, 0)

            # Aguarda mais 1 segundo antes de iniciar
            # o teste do próximo servomotor.
            time.sleep(1)

# O bloco finally é executado ao terminar os testes ou
# quando ocorre uma exceção dentro do bloco try.
#
# O método board.exit() encerra a comunicação serial
# entre o Python e o Arduino, liberando a porta utilizada.
finally:
    board.exit()
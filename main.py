# Importa funções matemáticas, como cálculos de ângulos e distâncias.
import math

# Permite controlar pausas e intervalos de tempo.
import time

# Biblioteca OpenCV, utilizada para capturar e processar imagens da câmera.
import cv2

# Biblioteca MediaPipe, utilizada para detectar e rastrear as mãos.
import mediapipe as mp

# Importa o módulo responsável pelo controle dos servomotores do Arduino.
import servo_controller as servos


# Abre a câmera principal do computador.
cap = cv2.VideoCapture(0)

# Configura a resolução da captura para 640 x 480 pixels.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# Define o arquivo do modelo de reconhecimento das mãos.
modelo = 'hand_landmarker.task'

# Configura o detector de mãos do MediaPipe.
# base_options: define o arquivo do modelo de reconhecimento das mãos.
# running_mode: configura o processamento de imagens em sequência (vídeo).
# num_hands: limita a detecção a uma única mão.
detector_config = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=modelo),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1
)
# Nomes dos dedos usados nas legendas exibidas na tela, organizados por pino.
finger_names = {
    9: "Polegar",
    10: "Indicador",
    11: "Medio",
    12: "Anelar",
    13: "Minimo",
}

# Inicia o registro dos comandos com todos os dedos abertos (1).
# Após cada novo comando, o valor do pino correspondente é atualizado.
# Esse registro permite evitar o envio repetido do mesmo comando.
# 1 = abrir (0°); 0 = fechar.
last_sent_states = {
    9: 1,
    10: 1,
    11: 1,
    12: 1,
    13: 1,
}


# Um vídeo é uma sequência de imagens, chamadas de quadros ou frames.
# Esta variável conta quantas imagens seguidas ficaram sem detectar uma mão.
# A contagem aumenta quando a mão não aparece e volta para 0 quando aparece.
# Ao chegar a 8, o programa envia o comando para abrir todos os dedos.
frames_without_hand = 0

# Guarda o tempo inicial antes de começar a analisar as imagens da câmera.
# time.monotonic() funciona como um cronômetro: retorna segundos e continua
# avançando mesmo se o horário do computador for alterado.
# Depois, usamos esse valor para calcular quanto tempo passou e criar
# uma marca de tempo para cada imagem, exigida pelo MediaPipe no modo VIDEO.
start_time = time.monotonic()

# Guarda a marca de tempo da imagem anterior, chamada de timestamp.
# O MediaPipe exige que cada imagem tenha um timestamp maior que o anterior.
# Começa em -1 para permitir que a primeira imagem receba o valor 0.
last_timestamp = -1


try:

    # Percorre os pinos guardados no dicionário: 9, 10, 11, 12 e 13.
    # Para cada pino, envia o comando 1, que abre o dedo e coloca o servo em 0°.
    # Assim, todos os dedos recebem o comando de abertura antes da análise da câmera.
    for pino in last_sent_states:
        servos.open_close(pino, 1)

    # Cria o detector e o fecha quando o código recuado abaixo termina.
    with mp.tasks.vision.HandLandmarker.create_from_options(detector_config) as hand_detector:

        # Repete a captura e a análise das imagens até encontrar um break.
        while True:

            # Tenta capturar uma imagem e guarda os dois resultados da operação.
            capture_result = cap.read()

            # Pega o primeiro resultado: True se conseguiu capturar, False se falhou.
            capture_success = capture_result[0]

            # Pega o segundo resultado: a imagem capturada pela câmera.
            frame = capture_result[1]

            # Se a câmera falhar, encerra o laço.
            # O finally executará as instruções de encerramento.
            if capture_success == False:
                break

            # O OpenCV fornece a imagem com as cores na ordem BGR (azul, verde, vermelho).
            # O MediaPipe espera a ordem RGB (vermelho, verde, azul).
            # Esta conversão troca a posição dos canais azul e vermelho para que
            # o MediaPipe interprete as cores corretamente ao analisar a imagem.
            # A imagem convertida fica em frame_rgb; frame mantém a imagem original.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Prepara a imagem para a análise do MediaPipe.
            # A imagem frame_rgb veio do OpenCV, mas o detector exige um objeto mp.Image.
            # Por isso, criamos esse objeto usando os pixels de frame_rgb e informamos
            # que suas cores já estão na ordem RGB. A análise da mão será feita depois.
            mediapipe_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb
            )

            # Calcula quantos segundos passaram desde o início do processamento.
            # Multiplica por 1000 para converter para milissegundos.
            # int() retira a parte decimal, pois o MediaPipe exige um número inteiro.
            # O resultado é o timestamp: a marca de tempo desta imagem no vídeo.
            timestamp = int((time.monotonic() - start_time) * 1000)

            # Cada imagem precisa ter um tempo maior que a anterior.
            # Se a anterior recebeu 100, esta precisa receber pelo menos 101.
            # max() mantém o tempo calculado se ele já for maior; caso contrário,
            # usa o tempo anterior mais 1.
            timestamp = max(timestamp, last_timestamp + 1)

            # Guarda o tempo desta imagem para comparar com o da próxima.
            # Na próxima repetição do while, este será o tempo da imagem anterior.
            last_timestamp = timestamp

            # Envia a imagem e sua marca de tempo ao detector de mãos.
            # Guarda em result o resultado da análise, incluindo os pontos da mão
            # caso ela tenha sido encontrada.
            result = hand_detector.detect_for_video(mediapipe_image, timestamp)

            # Se encontrou uma mão, executa as linhas abaixo.
            if result.hand_landmarks:

                # Zera a contagem de imagens sem mão, pois ela foi encontrada.
                frames_without_hand = 0

                # Pega os 21 pontos da única mão detectada,
                # pois configuramos o detector com num_hands=1.
                hand_points = result.hand_landmarks[0]

                # Imagine uma régua ligando a ponta do polegar à base do dedo mínimo.
                # Este cálculo mede a distância entre esses dois lugares na imagem.
                # Para isso, usa a separação na horizontal (x) e na vertical (y).
                thumb_distance = math.hypot(
                    # Quanto se separam para os lados.
                    hand_points[4].x - hand_points[17].x,
                    # Quanto se separam para cima ou baixo.
                    hand_points[4].y - hand_points[17].y,
                )

                # Mede a largura da palma, como uma régua ligando a base do indicador (5)
                # à base do dedo mínimo (17). Essa medida será usada como referência
                # para comparar a distância do polegar com o tamanho da mão.
                palm_width = math.hypot(
                    # Separação para os lados.
                    hand_points[5].x - hand_points[17].x,
                    # Separação para cima ou baixo.
                    hand_points[5].y - hand_points[17].y,
                )

                # Divide a distância do polegar pela largura da palma para comparar
                # as medidas mesmo quando a mão se aproxima ou se afasta da câmera.
                # max() evita dividir por zero se a largura da palma for calculada como zero.
                thumb_ratio = thumb_distance / max(palm_width, 0.001)

               # Se a distância do polegar for maior que 1,20 vez a largura da palma,
                # considera o polegar aberto. O valor 1 representa o comando de abrir.
                if thumb_ratio > 1.20:
                    new_thumb_state = 1

                # Se for menor que 0,90 vez a largura da palma,
                # considera o polegar fechado. O valor 0 representa o comando de fechar.
                elif thumb_ratio < 0.90:
                    new_thumb_state = 0

                # Entre 0,90 e 1,20, mantém o último estado enviado ao polegar (pino 9).
                # Essa faixa evita mudanças de comando por pequenas oscilações na imagem.
                else:
                    new_thumb_state = last_sent_states[9]

                # -------------------------------------------------
                # OUTROS QUATRO DEDOS
                # -------------------------------------------------

                # Compara a posição vertical (.y) da base e da ponta de cada dedo.
                # Na imagem, y aumenta de cima para baixo.
                # Quando a ponta está acima da base, a subtração dá um valor positivo.
                # Quando está abaixo, dá um valor negativo.
                # Esta regra considera a mão com os dedos apontando para cima.

                # Indicador: ponto 5 = base; ponto 8 = ponta.
                index_difference = hand_points[5].y - hand_points[8].y

                # Médio: ponto 9 = base; ponto 12 = ponta.
                middle_difference = hand_points[9].y - hand_points[12].y

                # Anelar: ponto 13 = base; ponto 16 = ponta.
                ring_difference = hand_points[13].y - hand_points[16].y

                # Mínimo: ponto 17 = base; ponto 20 = ponta.
                little_difference = hand_points[17].y - hand_points[20].y

                # Cria uma cópia dos últimos estados enviados aos servos.
                # Assim, cada dedo começa mantendo seu comando anterior.
                # A cópia permite preparar os novos comandos sem alterar esse registro.
                new_states = last_sent_states.copy()

                # Adiciona o estado do polegar, que já foi calculado.
                # O pino 9 controla o polegar.
                new_states[9] = new_thumb_state

                # Os limites abaixo criam uma margem para reduzir tremores:
                # acima de 0.02, abre; abaixo de -0.02, fecha.
                # Entre esses valores, mantém o estado anterior.
                # Como y é proporcional à altura da imagem, 0.02 corresponde a 2% dela.

                # Indicador, ligado ao pino 10.
                if index_difference > 0.02:
                    new_states[10] = 1  # Comando para abrir.
                elif index_difference < -0.02:
                    new_states[10] = 0  # Comando para fechar.

                # Médio, ligado ao pino 11.
                if middle_difference > 0.02:
                    new_states[11] = 1
                elif middle_difference < -0.02:
                    new_states[11] = 0

                # Anelar, ligado ao pino 12.
                if ring_difference > 0.02:
                    new_states[12] = 1
                elif ring_difference < -0.02:
                    new_states[12] = 0

                # Mínimo, ligado ao pino 13.
                if little_difference > 0.02:
                    new_states[13] = 1
                elif little_difference < -0.02:
                    new_states[13] = 0

                # Não precisamos de else: quando nenhum limite é ultrapassado,
                # permanece o estado anterior, copiado para new_states.
                # Até aqui, apenas preparamos os comandos; o envio aos servos vem depois.

                # Percorre os pinos dos cinco servos: 9, 10, 11, 12 e 13.
                for pin in last_sent_states:

                    # Compara o novo estado do dedo com o último estado enviado.
                    # != significa "diferente de". Se forem iguais, não envia nada.
                    if new_states[pin] != last_sent_states[pin]:

                        # Envia o comando ao servo desse pino.
                        # new_states[pin] contém 1 para abrir ou 0 para fechar.
                        servos.open_close(pin, new_states[pin])

                        # Atualiza o registro com o comando que acabou de ser enviado.
                        # Na próxima imagem, esse valor será usado na comparação.
                        last_sent_states[pin] = new_states[pin]

                # Obtém as dimensões da imagem: altura, largura e quantidade de canais de cor.
                # O _ recebe a quantidade de canais, pois não precisamos dela neste trecho.
                height, width, _ = frame.shape

                # Percorre os 21 pontos da mão encontrados pelo MediaPipe.
                for point in hand_points:

                    # O MediaPipe fornece posições proporcionais ao tamanho da imagem.
                    # Multiplicamos pela largura e pela altura para obter posições em pixels.
                    # int() transforma os resultados em números inteiros para desenhar.
                    x = int(point.x * width)
                    y = int(point.y * height)

                    # Desenha um círculo na posição desse ponto.
                    # frame: imagem onde desenhar.
                    # (x, y): posição do centro do círculo.
                    # 4: raio do círculo em pixels.
                    # (255, 0, 0): azul na ordem BGR usada pelo OpenCV.
                    # -1: preenche o círculo, em vez de desenhar apenas a borda.
                    cv2.circle(frame, (x, y), 4, (255, 0, 0), -1)

                # Define a posição vertical da primeira legenda: 25 pixels abaixo do topo.
                # As próximas legendas serão desenhadas mais abaixo, aumentando esse valor.
                text_y = 25

                # Percorre os pinos para mostrar uma legenda para cada dedo.
                for pin in last_sent_states:

                    # Escolhe o texto de acordo com o último comando enviado ao servo.
                    # 1 significa abrir; 0 significa fechar.
                    if last_sent_states[pin] == 1:
                        state_text = "aberto"
                    else:
                        state_text = "fechado"

                    # Escreve o nome do dedo e seu estado na imagem.
                    cv2.putText(
                        # Imagem onde escrever.
                        frame,
                        # Exemplo: "Polegar: aberto".
                        f"{finger_names[pin]}: {state_text}",
                        # Posição: 10 pixels da esquerda.
                        (10, text_y),
                        # Tipo de fonte.
                        cv2.FONT_HERSHEY_SIMPLEX,
                        # Tamanho do texto.
                        0.55,
                        # Cor verde, na ordem BGR.
                        (0, 255, 0),
                        # Espessura das letras.
                        2,
                    )

                    # Desce 23 pixels para escrever a próxima legenda sem sobrepor a anterior.
                    text_y += 23

        # Este else pertence ao if result.hand_landmarks.
        # Executa quando o MediaPipe não encontra uma mão na imagem atual.
            else:

                # Soma 1 à contagem de imagens seguidas sem detectar uma mão.
                # Quando uma mão é encontrada, essa contagem volta para zero.
                frames_without_hand += 1

                # Mostra um aviso vermelho na imagem com a contagem atual.
                # Exemplo: "Mao nao detectada: 3/8".
                # O número 8 indica o limite usado depois para mandar abrir os dedos.
                cv2.putText(
                    # Imagem onde escrever.
                    frame,
                    # Texto do aviso.
                    f"Mao nao detectada: {frames_without_hand}/8",
                    # Posição: x=10, y=30.
                    (10, 30),
                    # Tipo de fonte.
                    cv2.FONT_HERSHEY_SIMPLEX,
                    # Tamanho do texto.
                    0.6,
                    # Cor vermelha em BGR.
                    (0, 0, 255),
                    # Espessura das letras.
                    2
                )

                # Ao completar 8 imagens seguidas sem detectar uma mão, abre todos os dedos.
                # Usar == 8 faz esse comando acontecer apenas quando a contagem chega a 8,
                # evitando repeti-lo nas imagens seguintes, com contagens 9, 10, 11...
                if frames_without_hand == 8:

                    # Percorre os pinos dos cinco servos.
                    for pin in last_sent_states:

                        # Envia o comando 1: abrir o dedo e colocar o servo em 0°.
                        servos.open_close(pin, 1)

                        # Registra que o último comando enviado para esse servo foi abrir.
                        last_sent_states[pin] = 1

            # Mostra a imagem com os pontos e as legendas na janela "Mao robotica".
            cv2.imshow("Mao robotica", frame)

            # Atualiza a janela e espera aproximadamente 1 milissegundo por uma tecla.
            # & 0xFF mantém a parte do código usada nesta comparação.
            # ord("q") fornece o código da tecla q.
            # Se q foi pressionado, break encerra o while.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

# Executa o encerramento ao sair do try principal,
# tanto ao pressionar Q quanto se ocorrer um erro.
finally:
    try:
        # Percorre os pinos dos cinco servos e tenta abrir cada dedo.
        # O comando 1 posiciona o servo em 0°.
        for pin in last_sent_states:
            servos.open_close(pin, 1)

    # Se um comando aos servos falhar, este bloco ainda será executado.
    # Assim, o erro não impede a tentativa de liberar a câmera
    # e encerrar a comunicação com o Arduino.
    finally:
        # Libera a câmera para que outros programas possam utilizá-la.
        cap.release()

        # Fecha as janelas de imagem abertas pelo OpenCV.
        cv2.destroyAllWindows()

        # Encerra a conexão com o Arduino.
        servos.board.exit()

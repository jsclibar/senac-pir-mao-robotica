import math
import time
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
import servo_controller as mao


# Pinos: polegar, indicador, medio, anelar e minimo.
pinos = [9, 10, 11, 12, 13]
nomes = ["Polegar", "Indicador", "Medio", "Anelar", "Minimo"]

# Guarda o ultimo estado enviado para cada servo.
# No servo_controller: 1 = aberto em 0 graus; 0 = fechado.
ultimo_estado = {pino: 1 for pino in pinos}

# Guarda cinco leituras de cada dedo. A maioria vence e reduz tremores.
historico = {pino: deque([1] * 5, maxlen=5) for pino in pinos}


def calcular_angulo(a, b, c):
    """Calcula o angulo A-B-C. Dedo esticado fica perto de 180 graus."""
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)

    divisor = math.hypot(*ba) * math.hypot(*bc)
    if divisor == 0:
        return 0

    cos = (ba[0] * bc[0] + ba[1] * bc[1]) / divisor
    return math.degrees(math.acos(max(-1, min(1, cos))))


def enviar_estado(pino, leitura):
    """Filtra a leitura e envia somente quando o estado realmente muda."""
    historico[pino].append(leitura)
    estado = 1 if sum(historico[pino]) >= 3 else 0

    if estado != ultimo_estado[pino]:
        mao.abrir_fechar(pino, estado)
        ultimo_estado[pino] = estado


def abrir_todos():
    """Retorna todos os servos para 0 graus."""
    for pino in pinos:
        mao.abrir_fechar(pino, 1)
        ultimo_estado[pino] = 1
        historico[pino] = deque([1] * 5, maxlen=5)


# Abre a camera. No Windows, CAP_DSHOW pode ser acrescentado se necessario:
# camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not camera.isOpened():
    raise RuntimeError("Nao foi possivel abrir a camera.")


# O modelo hand_landmarker.task deve ficar na mesma pasta deste arquivo.
modelo = Path(__file__).parent / "hand_landmarker.task"

opcoes = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1,
)


# Linhas usadas para desenhar a mao.
conexoes = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


frames_sem_mao = 0
mao_ja_aberta = False

try:
    abrir_todos()

    with mp.tasks.vision.HandLandmarker.create_from_options(opcoes) as detector:
        inicio = time.monotonic()
        ultimo_timestamp = -1

        while True:
            success, img = camera.read()

            if not success:
                frames_sem_mao += 1
                if frames_sem_mao >= 8 and not mao_ja_aberta:
                    abrir_todos()
                    mao_ja_aberta = True
                continue

            # Converte a imagem para o formato usado pelo MediaPipe.
            frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            imagem_mp = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb,
            )

            # O modo VIDEO exige um timestamp sempre crescente.
            timestamp = int((time.monotonic() - inicio) * 1000)
            timestamp = max(timestamp, ultimo_timestamp + 1)
            ultimo_timestamp = timestamp

            resultado = detector.detect_for_video(imagem_mp, timestamp)

            if resultado.hand_landmarks:
                frames_sem_mao = 0
                mao_ja_aberta = False
                pontos = resultado.hand_landmarks[0]

                # Angulos dos quatro dedos comuns.
                angulo_indicador = calcular_angulo(
                    pontos[5], pontos[6], pontos[8])
                angulo_medio = calcular_angulo(
                    pontos[9], pontos[10], pontos[12])
                angulo_anelar = calcular_angulo(
                    pontos[13], pontos[14], pontos[16])
                angulo_minimo = calcular_angulo(
                    pontos[17], pontos[18], pontos[20])

                # O polegar usa angulo e distancia proporcional ao tamanho da palma.
                angulo_polegar = calcular_angulo(
                    pontos[2], pontos[3], pontos[4])
                largura_palma = math.hypot(
                    pontos[5].x - pontos[17].x,
                    pontos[5].y - pontos[17].y,
                )
                distancia_polegar = math.hypot(
                    pontos[4].x - pontos[5].x,
                    pontos[4].y - pontos[5].y,
                ) / max(largura_palma, 0.000001)

                # 1 significa aberto; 0 significa fechado.
                polegar = 1 if angulo_polegar > 140 and distancia_polegar > 0.65 else 0
                indicador = 1 if angulo_indicador > 145 else 0
                medio = 1 if angulo_medio > 145 else 0
                anelar = 1 if angulo_anelar > 145 else 0
                minimo = 1 if angulo_minimo > 145 else 0

                enviar_estado(9, polegar)
                enviar_estado(10, indicador)
                enviar_estado(11, medio)
                enviar_estado(12, anelar)
                enviar_estado(13, minimo)

                # Converte os pontos para pixels e desenha a mao.
                altura, largura, _ = img.shape
                pontos_tela = [
                    (int(p.x * largura), int(p.y * altura))
                    for p in pontos
                ]

                for x, y in pontos_tela:
                    cv2.circle(img, (x, y), 4, (255, 0, 0), -1)

                for inicio_linha, fim_linha in conexoes:
                    cv2.line(
                        img,
                        pontos_tela[inicio_linha],
                        pontos_tela[fim_linha],
                        (0, 255, 0),
                        2,
                    )

                # Legendas mantidas na tela.
                for linha, (pino, nome) in enumerate(zip(pinos, nomes), start=1):
                    estado = "aberto" if ultimo_estado[pino] == 1 else "fechado"
                    cv2.putText(
                        img,
                        f"{nome}: {estado}",
                        (10, linha * 23),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2,
                    )

            else:
                frames_sem_mao += 1

                cv2.putText(
                    img,
                    f"Mao nao detectada: {frames_sem_mao}/8",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )

                # Abre a mao apenas uma vez depois de oito frames sem deteccao.
                if frames_sem_mao >= 8 and not mao_ja_aberta:
                    abrir_todos()
                    mao_ja_aberta = True

            cv2.imshow("Mao robotica", img)

            # Pressione Q ou Esc para sair.
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q") or tecla == 27:
                break

finally:
    # Sempre retorna os servos para 0 graus antes de encerrar.
    try:
        abrir_todos()
        time.sleep(0.3)
    finally:
        camera.release()
        cv2.destroyAllWindows()
        mao.board.exit()

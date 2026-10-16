import math
import time
from pathlib import Path

import cv2
import mediapipe as mp
import servo_controller as mao


# Abre a camera.
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)


# Configura o MediaPipe atual.
modelo = Path(__file__).parent / "hand_landmarker.task"

opcoes = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1,
)


# Relacao entre os dedos e os pinos do Arduino.
nomes = {
    9: "Polegar",
    10: "Indicador",
    11: "Medio",
    12: "Anelar",
    13: "Minimo",
}


# Estado 1 = dedo aberto e servo em 0 graus.
# Estado 0 = dedo fechado.
estados = {
    9: 1,
    10: 1,
    11: 1,
    12: 1,
    13: 1,
}


frames_sem_mao = 0
inicio = time.monotonic()
ultimo_timestamp = -1


try:
    # Garante que o programa comece com todos os dedos abertos.
    for pino in estados:
        mao.abrir_fechar(pino, 1)

    with mp.tasks.vision.HandLandmarker.create_from_options(opcoes) as hands:

        while True:
            success, img = cap.read()

            if not success:
                continue

            # Converte a imagem para RGB.
            frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            imagem_mp = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb,
            )

            # O MediaPipe precisa saber o tempo de cada imagem.
            timestamp = int((time.monotonic() - inicio) * 1000)
            timestamp = max(timestamp, ultimo_timestamp + 1)
            ultimo_timestamp = timestamp
            resultado = hands.detect_for_video(imagem_mp, timestamp)

            if resultado.hand_landmarks:
                frames_sem_mao = 0
                pontos = resultado.hand_landmarks[0]

                # -------------------------------------------------
                # POLEGAR
                # -------------------------------------------------

                # Compara a distancia do polegar com a largura da palma.
                # Assim, aproximar a mao da camera nao altera o resultado.
                distancia_polegar = math.hypot(
                    pontos[4].x - pontos[17].x,
                    pontos[4].y - pontos[17].y,
                )
                largura_palma = math.hypot(
                    pontos[5].x - pontos[17].x,
                    pontos[5].y - pontos[17].y,
                )
                proporcao_polegar = distancia_polegar / \
                    max(largura_palma, 0.001)

                # Dois limites criam uma pequena zona neutra.
                # Dentro dessa zona, o estado anterior e mantido.
                if proporcao_polegar > 1.20:
                    novos_estados_polegar = 1
                elif proporcao_polegar < 0.90:
                    novos_estados_polegar = 0
                else:
                    novos_estados_polegar = estados[9]

                # -------------------------------------------------
                # OUTROS QUATRO DEDOS
                # -------------------------------------------------

                # A coordenada Y aumenta de cima para baixo.
                # Se a ponta estiver acima da base, o dedo esta aberto.
                dist_indicador = pontos[5].y - pontos[8].y
                dist_medio = pontos[9].y - pontos[12].y
                dist_anelar = pontos[13].y - pontos[16].y
                dist_minimo = pontos[17].y - pontos[20].y

                # Comeca mantendo os estados anteriores.
                novos_estados = estados.copy()
                novos_estados[9] = novos_estados_polegar

                # A zona entre -0.02 e 0.02 evita tremores.
                if dist_indicador > 0.02:
                    novos_estados[10] = 1
                elif dist_indicador < -0.02:
                    novos_estados[10] = 0

                if dist_medio > 0.02:
                    novos_estados[11] = 1
                elif dist_medio < -0.02:
                    novos_estados[11] = 0

                if dist_anelar > 0.02:
                    novos_estados[12] = 1
                elif dist_anelar < -0.02:
                    novos_estados[12] = 0

                if dist_minimo > 0.02:
                    novos_estados[13] = 1
                elif dist_minimo < -0.02:
                    novos_estados[13] = 0

                # Envia um comando somente quando o estado muda.
                for pino in estados:
                    if novos_estados[pino] != estados[pino]:
                        mao.abrir_fechar(pino, novos_estados[pino])
                        estados[pino] = novos_estados[pino]

                # Desenha os 21 pontos encontrados pelo MediaPipe.
                altura, largura, _ = img.shape

                for ponto in pontos:
                    x = int(ponto.x * largura)
                    y = int(ponto.y * altura)
                    cv2.circle(img, (x, y), 4, (255, 0, 0), -1)

                # Mostra o estado de cada dedo na tela.
                linha = 25

                for pino in estados:
                    texto = "aberto" if estados[pino] == 1 else "fechado"

                    cv2.putText(
                        img,
                        f"{nomes[pino]}: {texto}",
                        (10, linha),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2,
                    )

                    linha += 23

            else:
                # Conta quantas imagens consecutivas ficaram sem uma mao.
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

                # Depois de oito imagens sem mao, abre todos os dedos.
                if frames_sem_mao == 8:
                    for pino in estados:
                        mao.abrir_fechar(pino, 1)
                        estados[pino] = 1

            cv2.imshow("Mao robotica", img)

            # Pressione Q para encerrar.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


finally:
    # Abre todos os dedos antes de fechar o programa.
    for pino in estados:
        mao.abrir_fechar(pino, 1)

    cap.release()
    cv2.destroyAllWindows()
    mao.board.exit()

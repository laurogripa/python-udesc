# Amarelinha

Amarelinha projetada no chão.

Este projeto renderiza a amarelinha em uma tela ou projetor apontado para o piso, enquanto uma webcam observa a área de jogo. O sistema usa visão computacional para rastrear mão e corpo, detectar gestos e estimar onde os pés do jogador estão sobre a projeção.

## Como funciona

Tecnicamente, a calibração existe para resolver a relação entre dois espaços diferentes:

- o espaço da câmera, onde os landmarks do corpo são detectados
- o espaço do jogo, onde a amarelinha é desenhada na projeção

Na calibração, o sistema identifica os quatro cantos da área projetada no chão e calcula uma transformação de perspectiva. Essa homografia permite converter pontos medidos pela câmera, como os pés do jogador, para coordenadas equivalentes dentro da tela do jogo.

Depois dessa etapa:

- os landmarks do corpo são extraídos com MediaPipe Pose
- os pontos dos pés são estimados a partir de `heel` e `foot_index`
- cada pé é projetado para o sistema de coordenadas da amarelinha
- a lógica do jogo decide se o jogador está pulando com um pé ou com dois

Isso permite tratar a projeção no chão como uma superfície interativa: o jogo não depende apenas de teclado ou mão, mas da posição física do corpo em relação ao desenho projetado.

## Execução

Exemplos:

```bash
python main.py
python main.py --screen 1
python main.py --skeleton
python main.py --show-markers
python main.py --show-feet
```

## Requisitos técnicos

- `pygame` para renderização e loop do jogo
- `opencv-python` para captura de câmera e calibração
- `mediapipe` para rastreamento de mão e pose
- modelos `.task` em `assets/models/`

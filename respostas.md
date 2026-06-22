# Respostas dos exercícios

## Exercício 1

Em `exercicio-1/main.py`, adicionar os dois-pontos ao final da declaração:

```python
def parse_args() -> argparse.Namespace:
```

## Exercício 2

Em `exercicio-2/main.py`, substituir a chamada ao método inexistente:

```python
game.iniciar()
```

por:

```python
game.run()
```

## Exercício 3

Em `exercicio-3/game/main.py`, enviar números inteiros para `_try_hop`:

```python
if key == pygame.K_1:
    self._try_hop(feet=1)
elif key == pygame.K_2:
    self._try_hop(feet=2)
```

Os valores `"1"` e `"2"` eram textos e nunca seriam iguais ao número inteiro retornado por
`len(group)`.

## Exercício 4

Em `exercicio-4/game/main.py`, completar `_handle_key` com:

```python
if key == pygame.K_1:
    self._try_hop(feet=1)
elif key == pygame.K_2:
    self._try_hop(feet=2)
```

## Exercício 5

Adicionar o MediaPipe às dependências de `exercicio-5/requirements.txt`:

```text
mediapipe==0.10.35
```

Em `exercicio-5/game/camera.py`, importar `Path`, definir o caminho do modelo e restaurar o
estado necessário para estabilizar os gestos:

```python
from pathlib import Path

from game.settings import GESTURE_STABLE_FRAMES

MODEL_PATH = Path(__file__).parent.parent / "assets" / "models" / "hand_landmarker.task"
```

No `__init__` de `CameraManager`, adicionar:

```python
self._landmarker: Any | None = None
self._pending_gesture: int | None = None
self._pending_frames = 0
self._latched_gesture: int | None = None
self._gesture_event: int | None = None
self._timestamp_ms = 0
```

Depois de abrir a câmera em `select`, criar o detector:

```python
self._landmarker = self._create_landmarker()
```

Em `update`, antes de recortar a imagem, detectar o gesto:

```python
self._detect_gesture(frame)
```

Substituir `consume_gesture` por:

```python
def consume_gesture(self) -> int | None:
    gesture = self._gesture_event
    self._gesture_event = None
    return gesture
```

Adicionar os métodos de criação do detector e reconhecimento:

```python
def _create_landmarker(self) -> Any:
    import mediapipe as mp

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH),
            delegate=mp.tasks.BaseOptions.Delegate.CPU,
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    return mp.tasks.vision.HandLandmarker.create_from_options(options)

def _detect_gesture(self, frame: Any) -> None:
    if self._landmarker is None:
        return

    import mediapipe as mp

    self._timestamp_ms += 1
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = self._landmarker.detect_for_video(image, self._timestamp_ms)
    gesture = self._count_fingers(result)
    self._update_gesture_state(gesture)

def _count_fingers(self, result: Any) -> int | None:
    if not result.hand_landmarks:
        return None

    landmarks = result.hand_landmarks[0]
    index_up = landmarks[8].y < landmarks[6].y
    middle_up = landmarks[12].y < landmarks[10].y
    ring_up = landmarks[16].y < landmarks[14].y
    pinky_up = landmarks[20].y < landmarks[18].y

    if index_up and not middle_up and not ring_up and not pinky_up:
        return 1
    if index_up and middle_up and not ring_up and not pinky_up:
        return 2
    return None

def _update_gesture_state(self, gesture: int | None) -> None:
    if gesture != self._pending_gesture:
        self._pending_gesture = gesture
        self._pending_frames = 1
        return

    self._pending_frames += 1
    if self._pending_frames < GESTURE_STABLE_FRAMES:
        return

    if gesture is None:
        self._latched_gesture = None
    elif gesture != self._latched_gesture:
        self._gesture_event = gesture
        self._latched_gesture = gesture
```

Em `close`, fechar o detector e limpar seu estado:

```python
if self._landmarker is not None:
    self._landmarker.close()
self._landmarker = None
self._reset_gesture_state()
```

Por fim, adicionar:

```python
def _reset_gesture_state(self) -> None:
    self._pending_gesture = None
    self._pending_frames = 0
    self._latched_gesture = None
    self._gesture_event = None
    self._timestamp_ms = 0
```

A implementação completa também pode ser consultada na pasta `amarelinha`.

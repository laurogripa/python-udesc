# Introdução ao Python

Projeto de implementação do clássico jogo infantil Amarelinha, desenvolvido para a disciplina de Computação Gráfica Avançada da UDESC.

**Objetivo:** Introdução ao Python e PyGame. Desafios progressivos de código.

## Requisitos

- **pyenv** 2.7.2
- **Python** 3.13.7
- **pip** — incluso com Python 3.13.7 (`python3 -m pip`)

### Instalação

Consulte a documentação oficial de cada ferramenta:

- **pyenv:** <https://github.com/pyenv/pyenv#installation>
- **Python 3.13.7:** <https://www.python.org/downloads/release/python-3137/>
- **pip:** <https://pip.pypa.io/en/stable/installation/>

Run:

```bash
cd amarelinha
python3 -m pip install -r requirements-dev.txt
```

Para a versão com projeção no chão:

```bash
cd amarelinha-chao
python3 -m pip install -r requirements-dev.txt
```

Repita o comando em cada pasta de exercício (`exercicio-1`, `exercicio-2`, etc.) para instalar as dependências de desenvolvimento.

# Progressão dos exercícios da Amarelinha

A pasta `amarelinha` contém a implementação final e não deve ser alterada. Em todos os
exercícios, o jogo usa as teclas `1` e `2`: `1` representa um pé e `2` representa dois pés.

## Exercício 1 — erro de sintaxe

- Base sem câmera.
- O jogo já contém a lógica de movimentação pelas teclas `1` e `2`.
- Um erro simples de sintaxe impede o Python de carregar o programa.
- Objetivo: identificar e corrigir o problema de sintaxe.

## Exercício 2 — erro em tempo de execução

- Corrige o erro de sintaxe do exercício 1.
- O programa pode ser interpretado, mas apresenta um erro ao iniciar o jogo.
- Objetivo: localizar e corrigir a operação inválida.

## Exercício 3 — incompatibilidade de tipos

- Corrige a chamada do exercício 2.
- O jogo abre, mas há uma inconsistência nos dados usados durante a movimentação.
- Objetivo: manter os tipos utilizados pelo jogo consistentes.

## Exercício 4 — entrada incompleta

- Corrige a incompatibilidade de tipos do exercício 3.
- O jogo abre e desenha a amarelinha, mas a interação ainda está incompleta.
- Objetivo: completar o tratamento das entradas `1` e `2`.

## Exercício 5 — câmera sem gestos

- Implementa corretamente os controles de teclado do exercício 4.
- Adiciona seleção de câmera, prévia de vídeo com OpenCV e o modelo
  `assets/models/hand_landmarker.task`.
- O jogo funciona integralmente pelas teclas `1` e `2`.
- O reconhecimento de gestos ainda não está implementado.
- Objetivo: integrar MediaPipe e reconhecer somente os gestos equivalentes aos números `1` e `2`.

## Implementação final

`amarelinha` acrescenta ao exercício 5 a criação do `HandLandmarker`, a leitura dos pontos da
mão e a estabilização dos gestos entre quadros. Ela continua aceitando as teclas `1` e `2`,
além dos gestos correspondentes.

## Amarelinha no chão

`amarelinha-chao` é uma cópia separada da implementação com projeção no chão. Ela preserva a
versão final original em `amarelinha` e adiciona calibração da área projetada, rastreamento de
pose, posição dos pés e indicadores visuais para uso com projetor e câmera.

Atalhos principais da versão `amarelinha-chao`:

- `Ctrl+C`: calibração automática pelos marcadores vermelhos.
- `Ctrl+M`: calibração manual clicando os quatro cantos no preview da câmera.
- `Ctrl+S`: seleção/configuração da câmera.
- `--show-feet`: mostra os círculos dos pés e do centro na tela do jogo.
- `--skeleton`: mostra o esqueleto detectado no preview da câmera.

Exemplo:

```bash
cd amarelinha-chao
python3 main.py --show-feet --skeleton
```

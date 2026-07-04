import argparse

from game.main import Amarelinha


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jogo simples de amarelinha feito com pygame.")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Initialize and draw one frame, then exit."
    )
    parser.add_argument(
        "--skeleton",
        action="store_true",
        help="Renderiza o esqueleto conectado da mão e do corpo na câmera.",
    )
    parser.add_argument(
        "--screen",
        type=int,
        default=0,
        help="Índice da tela onde o jogo será aberto. Padrão: 0.",
    )
    parser.add_argument(
        "--show-markers",
        action="store_true",
        help="Mantém os marcadores de calibração visíveis durante o jogo.",
    )
    parser.add_argument(
        "--show-feet",
        action="store_true",
        help="Mostra os indicadores dos pés na projeção do jogo.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = Amarelinha(
        show_skeleton=args.skeleton,
        screen_index=args.screen,
        show_markers=args.show_markers,
        show_feet=args.show_feet,
    )
    if args.smoke_test:
        game.smoke_test()
    else:
        game.run()


if __name__ == "__main__":
    main()

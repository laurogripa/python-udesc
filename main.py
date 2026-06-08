import argparse

from hopscotch.game import HopscotchGame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jogo simples de amarelinha feito com pygame.")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Initialize and draw one frame, then exit."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = HopscotchGame()
    if args.smoke_test:
        game.smoke_test()
    else:
        game.run()


if __name__ == "__main__":
    main()

"""Compatibility entrypoint. Prefer: python -u -m bot.embersea_rep."""

from bot.embersea_rep import CONFIG, main, run


if __name__ == "__main__":
    run()

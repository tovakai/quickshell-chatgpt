"""Safe command-line entry point. Live auth and inference are not implemented."""

import argparse

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(description="quickshell-chatgpt bridge (scaffold only)")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()
    print("Scaffold ready. Authentication and inference are not implemented yet.")


if __name__ == "__main__":
    main()

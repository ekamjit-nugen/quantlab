"""Entry point: `python -m quantlab` runs this file."""

from quantlab import __version__


def main() -> None:
    """Print the installed version and exit."""
    print(f"quantlab {__version__}")


if __name__ == "__main__":
    main()

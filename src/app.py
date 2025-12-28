"""Entry point placeholder.

Currently just validates that the project imports and logs a startup banner.
Actual bot startup will be wired in subsequent steps.
"""

import logging


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("EEW Discord Bot skeleton started (no runtime logic yet).")


if __name__ == "__main__":
    main()
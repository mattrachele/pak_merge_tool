#!/usr/bin/env python3

# Version 0.1.0

"""This module contains functions to handle formatting of directories."""

# Usage:    python format_dir.py --format_dir=<directory_path>
# Example:  clear;python pak_merge_tool\scripts\format_dir.py --format_dir=~merged_mods_v2-0_P

import logging
import argparse
import os

from format_handler import format_file
from requirements_handler import load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format="%(asctime)s | %(levelname)s | %(message)s",  # Set the log format
    handlers=[
        logging.FileHandler("merge_tool.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the console
    ],
)

# Create a logger object
logger = logging.getLogger(__name__)


def recursive_format_dir(path: str, max_perf_chunk_size: int) -> None:
    """Recursively format all files in a directory and its subdirectories."""
    dir_list = os.listdir(path)
    sorted_dir_list = sorted(dir_list, key=lambda x: x.lower())
    for item in sorted_dir_list:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            recursive_format_dir(item_path, max_perf_chunk_size)
        else:
            format_file(item_path, max_perf_chunk_size)


def main() -> bool:
    """Main function to handle directory formatting."""
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description="Merge mod directories.")
    parser.add_argument(
        "--format_dir", type=str, help="The directory to format.", required=True
    )

    args = parser.parse_args()

    if not os.path.isdir(args.format_dir):
        logger.error(f"The specified path is not a directory: {args.format_dir}")
        return False

    # Load the config file
    config = load_config("config.json")
    max_perf_chunk_size = config["max_perf_chunk_size"]

    recursive_format_dir(args.format_dir, max_perf_chunk_size)

    return True


if __name__ == "__main__":
    main()

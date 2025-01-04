#!/usr/bin/env python3

# Version 0.1.0

"""Tool to fill a file with line numbers for testing."""

# Usage: python long_file_filler.py --path="<file_path>" --num_lines=<int>
# Example: clear;python tests\long_file_filler.py --path="tests\merged_test_dir\m_dir\long_file.cfg" --num_lines=1200

import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the log level
    format="%(asctime)s | %(levelname)s | %(message)s",  # Set the log format
    handlers=[
        logging.FileHandler("merge_tool.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the console
    ],
)

# Create a logger object
logger = logging.getLogger(__name__)


def fill_file_with_config_lines(file_path, num_lines):
    """
    Fill a file with a specified number of lines of config formatted text.

    :param file_path: Path to the file to be filled.
    :param num_lines: Number of lines to write to the file.
    """
    # TODO: Add more variation to the lines written to the file.
    with open(file_path, "w", encoding="utf-8") as file:
        max_depth = 3
        struct_size = 0
        max_struct_size = 10
        current_depth = 0
        begin_str = "struct.begin"
        end_str = "struct.end"
        mid_str = "tag = stuff::tag"

        for i in range(num_lines):
            lines_left = num_lines - i

            if current_depth == 0:
                file.write(f"{i} | {begin_str}\n")
                current_depth += 1
                struct_size = 1
            elif (
                struct_size == (max_struct_size - current_depth)
                or lines_left == current_depth
            ):
                current_depth -= 1
                file.write(f"{'    ' * current_depth}{i} | {end_str}\n")
                struct_size += 1
            elif current_depth == max_depth:
                file.write(f"{'    ' * current_depth}{i} | {mid_str}\n")
                struct_size += 1
            elif current_depth < max_depth:
                file.write(f"{'    ' * current_depth}{i} | {begin_str}\n")
                current_depth += 1
                struct_size += 1
            else:
                file.write(f"{'    ' * current_depth}{i} | {mid_str}\n")
                struct_size += 1


def main():
    """Main function for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fill a file with line numbers for testing."
    )
    parser.add_argument("--path", type=str, help="Path to the file to be filled.")
    parser.add_argument(
        "--num_lines", type=int, help="Number of lines to write to the file."
    )

    args = parser.parse_args()

    fill_file_with_config_lines(args.path, args.num_lines)


if __name__ == "__main__":
    main()

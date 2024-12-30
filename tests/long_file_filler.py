#!/usr/bin/env python3

# Version 0.1.0

"""Tool to fill a file with line numbers for testing."""

# Usage: python long_file_filler.py --path="<file_path>" --num_lines=<int>
# Example: clear;python tests\long_file_filler.py --path="tests\merged_test_dir\m_dir\long_file.cfg" --num_lines=1200


def fill_file_with_line_numbers(file_path, num_lines):
    """
    Fill a file with line numbers for testing.

    :param file_path: Path to the file to be filled.
    :param num_lines: Number of lines to write to the file.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        for i in range(1, num_lines + 1):
            file.write(f"line{i}\n")


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

    fill_file_with_line_numbers(args.path, args.num_lines)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# Version 0.1.0

"""This module contains functions to handle formatting of files."""

import logging
import os
import re
import shutil

from colorama import init

# Initialize colorama
init(autoreset=True)

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


def strip_whitespace(line) -> str:
    """Strip leading and trailing whitespace from a line."""
    return re.sub(r"^[ \t]+|[ \t]+$", "", line)


def remove_trailing_whitespace_and_newlines(line) -> str:
    """Remove trailing whitespace from a line."""
    return re.sub(r"[ \t\n]+$", "", line)


def display_file_parts(final_file, new_file) -> None:
    """Display the parts of the final and new files."""
    # TODO: Visual progress of merging - line numbers and total lines
    final_merged_mod_dir, final_filename = os.path.split(final_file)
    new_mods_dir, new_filename = os.path.split(new_file)
    logger.info(
        f"\n\t{'Mrg:':<10} {final_filename:<25} | {final_merged_mod_dir:<35} | {final_file}"
        f"\n\t{'New:':<10} {new_filename:<25} | {new_mods_dir:<35} | {new_file}"
    )


# FIXME: Test the merge lines and dup line check more - seems still has issues
def duplicate_line_check(
    temp_merged_mod_file, new_tmp_merged_mod_lines, perf_chunk, final_perf_chunk_sizes
) -> list:
    """Check for duplicate lines in the temporary merged mod file."""
    if perf_chunk == 1:
        return new_tmp_merged_mod_lines

    # Check for duplicate lines caused by matching lines crossing over chunks
    cleansed_lines = []
    last_perf_chunk_lines = []
    if perf_chunk > 1:
        last_perf_chunk_start_line = sum(final_perf_chunk_sizes[:-1])
        last_perf_chunk_end_line = sum(final_perf_chunk_sizes)

        with open(temp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
            for i, line in enumerate(tmp_merged_mod):
                if last_perf_chunk_start_line <= i < last_perf_chunk_end_line:
                    last_perf_chunk_lines.append(line.strip())

        # Check for chunks of duplicate lines in the last performance chunk
        # NOTE: There could be singular duplicate lines or a few lines that are expected
        max_duplicate_lines = 8
        duplicate_line_count = 0
        tmp_dup_lines = []
        tmp_last_lines = []

        for i, line in enumerate(new_tmp_merged_mod_lines):
            # Check if the line is in the last performance chunk
            tmp_last_lines.append(line.strip())
            if len(tmp_last_lines) > max_duplicate_lines:
                tmp_last_lines.pop(0)  # Remove the first line

            if line.strip() in last_perf_chunk_lines:
                duplicate_line_count += 1
                tmp_dup_lines.append(line)

                # If the duplicate line count exceeds the max then empty the tmp_dup_lines
                if duplicate_line_count > max_duplicate_lines:
                    logger.info(
                        f"Duplicate lines detected in performance chunk {perf_chunk}."
                    )
                    # logger.debug(f"Duplicate lines: {tmp_dup_lines}")
                    duplicate_line_count = 0
                    tmp_dup_lines = []
            else:
                duplicate_line_count = 0

                if tmp_dup_lines:
                    recent_dup_lines = 0
                    for dup_line in tmp_dup_lines:
                        if dup_line.strip() in tmp_last_lines:
                            recent_dup_lines += 1

                    if recent_dup_lines < 2:
                        logger.debug("Adding duplicate lines to cleansed lines.")
                        cleansed_lines.extend(tmp_dup_lines)

                    tmp_dup_lines = []

                cleansed_lines.append(line)

    return cleansed_lines


# TODO: This formatting is only for cfg files - clarify and add more file types
def config_file_formatter(unformatted_lines, tab_level) -> list:
    """Format the lines of a config file."""
    formatted_lines = []
    for line in unformatted_lines:
        formatted_line = ""
        stripped_line = strip_whitespace(line)  # Use to avoid removing newlines
        if "struct.begin" in line:
            formatted_line = f"{'    ' * tab_level}{stripped_line}"
            tab_level += 1
        elif "struct.end" in line:
            tab_level -= 1
            formatted_line = f"{'    ' * tab_level}{stripped_line}"
        else:
            formatted_line = f"{'    ' * tab_level}{stripped_line}"

        formatted_lines.append(formatted_line)

    return {
        "formatted_lines": formatted_lines,
        "tab_level": tab_level,
    }


def format_file(file_path, performance_chunk_size) -> bool:
    """Format a file."""
    # Check if cfg file and format it accordingly, else just skip it until more file types are added
    if not file_path.endswith(".cfg"):
        logger.debug(f"Skipping non-cfg file: {file_path}")
        return False

    if not os.path.exists(file_path):
        logger.error(f"Given file path does not exist: {file_path}")
        return False

    temp_formatted_file = file_path + "_format.tmp"
    current_depth = 0
    with open(file_path, "r", encoding="utf-8") as f, open(
        temp_formatted_file, "w", encoding="utf-8"
    ) as f_temp:
        while True:
            lines = f.readlines(performance_chunk_size)
            if not lines:
                break

            formatted_data = config_file_formatter(lines, current_depth)
            formatted_lines = formatted_data["formatted_lines"]
            current_depth = formatted_data["tab_level"]
            f_temp.writelines(formatted_lines)

        # Flush the file to ensure all data is written
        f_temp.flush()

        if current_depth != 0:
            logger.warning(
                f"Failed to format file - Did not end at tab level 0: {file_path}"
            )
            return False

    if not os.path.exists(temp_formatted_file):
        logger.error(f"Temporary formatted file does not exist: {temp_formatted_file}")
        return False

    if os.path.getsize(temp_formatted_file) == 0:
        logger.error(f"Temporary formatted file is empty: {temp_formatted_file}")
        return False

    try:
        shutil.move(temp_formatted_file, file_path)
    except PermissionError:
        logger.error(
            f"Permission denied while replacing file: \n\tOrg: {file_path}\n\tNew: {temp_formatted_file}"
        )
        return False
    except Exception as e:
        logger.error(f"An error occurred while replacing file: {file_path}")
        logger.error(e)
        return False

    return True

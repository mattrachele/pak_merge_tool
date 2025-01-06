#!/usr/bin/env python3

# Version 0.1.0

"""This module contains functions to handle formatting of files."""

import logging
import os
import re

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
# TODO: Seems to just increase the tab level - need to clear it out first - leading tabs
def config_file_formatter(unformatted_lines, tab_level) -> list:
    """Format the lines of a config file."""
    formatted_lines = []
    for line in unformatted_lines:
        formatted_line = ""
        # no_trail_line = re.sub(r"[ \t]+$", "", line)
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


def format_file(file_path) -> bool:
    """Format a file."""
    temp_formatted_file = file_path + "_format.tmp"
    performance_chunk_size = 1024
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

    os.replace(temp_formatted_file, file_path)
    if current_depth != 0:
        logger.warning(
            "Config file is not formatted correctly. Did not end at tab level 0."
        )
        return False

    return True

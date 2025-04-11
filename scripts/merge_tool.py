#!/usr/bin/env python3

# Version 0.2.0

"""Tool to merge Stalker 2 mod pak files into a single pak file.
    Most of the files in the pak files are text files, so the tool
    will merge the text files and remove duplicates."""

# Usage: python merge_tool.py --verbose --confirm --new_mods_dir="<dir>" --final_merged_mod_dir="<dir>"
# Example: clear;python .\merge_tool.py --new_mods_dir="..\unpacked\mod_dir" --final_merged_mod_dir="..\~merged_mods_v1-0_P"
# Test Example: clear;python scripts\merge_tool.py --new_mods_dir="tests\new_test_dir\m_dir" --final_merged_mod_dir="tests\merged_test_dir\m_dir"

# Step 1: Unpak the pak files using ReUnpak.bat (Uses repak.exe)

# Step 2: Scan through unpacked/ and merge the new directories into the ~merged_mods_v1-0/ directory
# Should add new code from incoming mods without removing any existing code
# Should update existing code with new code from incoming mods
# Should have an option to give user a choice between existing code and new code

# NOTE: Unified Diff starts indexing at 1, but this script uses 0-based indexing
# So all indexing is forced to start at 0 in this script

# TODO: Update to allow usage with other editors
# TODO: Add a comment to the merged file with the name of the mod that the code came from with a date and version number
# TODO: Add support for version checking to display version differences and check for lines removed in newer versions


import os
import shutil
import difflib
import argparse
import time
import logging
import json

from choice_handler import (
    choice_handler,
    non_text_file_choice_handler,
    open_files_in_vscode_compare,
    bad_format_choice_handler,
)
from requirements_handler import validate_requirements, load_config
from format_handler import format_file, duplicate_line_check, display_file_parts


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


def reload_temp_merged_mod_file(temp_merged_mod_file) -> int:
    """Reload the temporary merged mod file and return the last processed line."""
    if not os.path.exists(temp_merged_mod_file):
        return 0

    with open(temp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
        lines = tmp_merged_mod.readlines()
        last_processed_line = len(lines)

    return last_processed_line


def merge_files(
    new_mods_file,
    final_merged_mod_file,
    valid_requirements,
    config,
    confirm_user_choice=False,
) -> str:
    """Merge the contents of two text files, handling conflicts."""
    max_perf_chunk_size = config[
        "max_perf_chunk_size"
    ]  # Define the chunk size for reading the files
    perf_chunk = 0  # Initialize the performance chunk counter
    quit_out_bool = False
    skip_file_bool = False
    overwrite_file_bool = False
    final_perf_chunk_sizes = []
    last_display_diff = ""
    last_user_choice = 0
    final_merged_mod_filepath_no_ext, _ = os.path.splitext(final_merged_mod_file)
    perf_chunk_sizes_file = final_merged_mod_filepath_no_ext + "_perf_chunk_sizes.tmp"

    # Reload the perf_chunk_sizes_file to get the final_perf_chunk_sizes
    if os.path.exists(perf_chunk_sizes_file):
        with open(perf_chunk_sizes_file, "r", encoding="utf-8") as f:
            final_perf_chunk_sizes = json.loads(f.read())

    display_file_parts(final_merged_mod_file, new_mods_file)

    start_time = time.time()

    # Create a temporary file to store the merged contents
    temp_merged_mod_file = final_merged_mod_file + ".tmp"
    # Check if the temporary file exists and reload the last processed line
    last_processed_line = reload_temp_merged_mod_file(temp_merged_mod_file)

    # Pre-format the files before reading them
    format_file(new_mods_file, max_perf_chunk_size)
    format_file(final_merged_mod_file, max_perf_chunk_size)

    with open(new_mods_file, "r", encoding="utf-8") as new_mod, open(
        final_merged_mod_file, "r", encoding="utf-8"
    ) as final_merged_mod, open(
        temp_merged_mod_file, "a", encoding="utf-8"
    ) as temp_merged_mod:
        # if last_processed_line is not 0, skip to the last processed line
        if last_processed_line:
            for _ in range(last_processed_line):
                next(new_mod)
                next(final_merged_mod)

        # Loop through the merge files until the end of the two files
        while True:
            # Read a chunk of lines from each file based on the chunk size
            perf_chunk += 1
            new_mod_chunk = [
                line
                for line in (next(new_mod, None) for _ in range(max_perf_chunk_size))
                if line is not None
            ]
            final_merged_mod_chunk = [
                line
                for line in (
                    next(final_merged_mod, None) for _ in range(max_perf_chunk_size)
                )
                if line is not None
            ]

            if not new_mod_chunk and not final_merged_mod_chunk:
                break

            if new_mod_chunk == final_merged_mod_chunk:
                # If the chunks are identical, write the final_merged_mod_chunk to the temporary file
                final_perf_chunk_sizes.append(len(final_merged_mod_chunk))
                temp_merged_mod.writelines(final_merged_mod_chunk)
                temp_merged_mod.flush()  # Flush the buffer to write the lines to the file
                continue

            # Use difflib to create a unified diff for the chunk
            diff = difflib.unified_diff(
                final_merged_mod_chunk,
                new_mod_chunk,
                fromfile=final_merged_mod_file,
                tofile=new_mods_file,
            )

            logger.info("\n\nHandling diff...")
            # Handle the user's choice for the diff
            choice = choice_handler(
                new_mods_file,
                final_merged_mod_file,
                diff,
                final_merged_mod_chunk,
                new_mod_chunk,
                valid_requirements,
                temp_merged_mod_file,
                last_display_diff,
                last_user_choice,
                confirm_user_choice,
            )

            if choice["status"] == "skip":
                skip_file_bool = True
                break

            if choice["status"] == "overwrite":
                overwrite_file_bool = True
                break

            if choice["status"] == "quit-save":
                # Scan temp lines for duplicate lines caused by matching lines crossing over chunks
                cleansed_lines = duplicate_line_check(
                    temp_merged_mod_file,
                    choice["processed_lines"],
                    perf_chunk,
                    final_perf_chunk_sizes,
                )
                final_perf_chunk_sizes.append(len(cleansed_lines))
                temp_merged_mod.writelines(cleansed_lines)

                # Write final_perf_chunk_sizes to a file to track the chunk sizes
                with open(perf_chunk_sizes_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(final_perf_chunk_sizes))

                return "quit"

            if choice["status"] == "quit":
                quit_out_bool = True
                break

            # Scan temp lines for duplicate lines caused by matching lines crossing over chunks
            cleansed_lines = duplicate_line_check(
                temp_merged_mod_file,
                choice["processed_lines"],
                perf_chunk,
                final_perf_chunk_sizes,
            )
            last_display_diff = choice["last_display_diff"]
            last_user_choice = choice["last_user_choice"]

            # Write the new lines to the temporary file
            final_perf_chunk_sizes.append(len(cleansed_lines))
            temp_merged_mod.writelines(cleansed_lines)
            temp_merged_mod.flush()  # Flush the buffer to write the lines to the file

    if not quit_out_bool and not skip_file_bool and not overwrite_file_bool:
        # Validate the formatting of the temp_merged_mod_file
        format_result = format_file(temp_merged_mod_file, max_perf_chunk_size)
        if not format_result:
            # If the file is not formatted correctly, then give user options to manually fix the file
            if valid_requirements["code"]:
                logger.info(
                    "Opening the temp merged mod file in VS Code for manual formatting."
                )
                open_files_in_vscode_compare(
                    final_merged_mod_file, temp_merged_mod_file
                )

            bad_format_choice = bad_format_choice_handler(skip_file_bool, quit_out_bool)
            skip_file_bool = bad_format_choice["skip_file_bool"]
            quit_out_bool = bad_format_choice["quit_out_bool"]

        # Move the temporary file to the final_merged_mod_file
        shutil.move(temp_merged_mod_file, final_merged_mod_file)

    # Delete the temporary file
    if os.path.exists(temp_merged_mod_file):
        os.remove(temp_merged_mod_file)

    # Delete the perf_chunk_sizes_file
    if os.path.exists(perf_chunk_sizes_file):
        os.remove(perf_chunk_sizes_file)

    # If whole file overwrite chosen, then overwrite the final_merged_mod_file with the new_mods_file
    if overwrite_file_bool:
        shutil.copy2(new_mods_file, final_merged_mod_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Processing time: {elapsed_time:.2f} seconds\n")

    if quit_out_bool:
        return "quit"

    return "continue"


def merge_directories(
    new_mods_dir,
    final_merged_mod_dir,
    valid_requirements,
    config,
    confirm_user_choice=False,
    org_comp=False,
) -> str:
    """Recursively merge the contents of two directories."""
    # Ensure the final_merged_mod directory exists
    if not os.path.exists(final_merged_mod_dir):
        os.makedirs(final_merged_mod_dir)

    new_mods_dir_list = os.listdir(new_mods_dir)
    sorted_new_mods_dir_list = sorted(new_mods_dir_list)

    # Iterate through all items in the new_mods directory
    for item in sorted_new_mods_dir_list:
        new_mods_item = os.path.join(new_mods_dir, item)
        final_merged_mod_item = os.path.join(final_merged_mod_dir, item)

        if os.path.isdir(new_mods_item):
            # logger.debug(f"New Mods Item is a dir: {new_mods_item}")
            if not os.path.exists(final_merged_mod_item) and not org_comp:
                logger.info(
                    f"Final merged mod directory does not exist. Copying {new_mods_item} to {final_merged_mod_item}"
                )
                shutil.copytree(new_mods_item, final_merged_mod_item)
                continue

            if not os.path.exists(final_merged_mod_item) and org_comp:
                logger.debug(
                    f"Final merged mod directory does not exist: {final_merged_mod_item}\n\tSkipping Merge of: {new_mods_item}"
                )
                continue

            # If the item is a directory, recursively merge it
            result = merge_directories(
                new_mods_item,
                final_merged_mod_item,
                valid_requirements,
                config,
                confirm_user_choice,
                org_comp,
            )
            if result == "quit":
                return "quit"
        else:
            # If the item is a file, handle conflicts
            # logger.debug(f"New Mods Item is a file: {new_mods_item}")

            # Check if the final merged mod file exists and just copy it over if it doesn't
            #   Unless the org_comp flag is set, then don't copy over the file
            if not os.path.exists(final_merged_mod_item) and not org_comp:
                logger.info(
                    f"Final merged mod file does not exist. Copying {new_mods_item} to {final_merged_mod_item}"
                )
                shutil.copy2(new_mods_item, final_merged_mod_item)
                continue

            if not os.path.exists(final_merged_mod_item) and org_comp:
                logger.debug(
                    f"Final merged mod file does not exist: {final_merged_mod_item}\n\tSkipping Merge of: {new_mods_item}"
                )
                continue

            # Validate the file extension to ensure it's a text file and not a binary file
            file_extension = os.path.splitext(new_mods_item)[1]
            valid_file_extensions = config["valid_file_extensions"]

            if (
                file_extension not in valid_file_extensions
                and confirm_user_choice
                and not org_comp
            ):
                logger.info("Handling non-text file.")
                result = non_text_file_choice_handler(
                    final_merged_mod_item, new_mods_item
                )
                if result["status"] == "quit":
                    return "quit"

                if result["status"] == "skip":
                    continue

                if result["status"] == "overwrite":
                    shutil.copy2(new_mods_item, final_merged_mod_item)
                continue

            if file_extension not in valid_file_extensions and not org_comp:
                logger.info("Handling non-text file.")
                shutil.copy2(new_mods_item, final_merged_mod_item)
                continue

            if file_extension not in valid_file_extensions:
                continue

            result = merge_files(
                new_mods_item,
                final_merged_mod_item,
                valid_requirements,
                config,
                confirm_user_choice,
            )
            if result == "quit":
                logger.info("Merge aborted.")
                return "quit"

    return "continue"


def main() -> bool:
    """Main function to merge mod directories."""
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description="Merge mod directories.")
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output", required=False
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Disable user confirmation",
        required=False,
    )
    parser.add_argument(
        "--org_comp",
        action="store_true",
        help="Enable comparison to base game files",
        required=False,
    )
    parser.add_argument(
        "--new_mods_dir", help="The directory containing the new mods", required=True
    )
    parser.add_argument(
        "--final_merged_mod_dir",
        help="The directory containing the final merged mods",
        required=True,
    )
    args = parser.parse_args()

    # Update log level if verbose is set
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"Log Level: {logger.level}")
    logger.debug(f"Verbose: {args.verbose}")
    logger.debug(f"Confirm: {args.confirm}")

    # Validate the requirements
    valid_requirements = validate_requirements()

    # Load the config file
    config = load_config("config.json")

    result = merge_directories(
        args.new_mods_dir,
        args.final_merged_mod_dir,
        valid_requirements,
        config,
        args.confirm,
        args.org_comp,
    )

    if result == "quit":
        return False

    logger.info("Merge complete.\n")
    return True


if __name__ == "__main__":
    main()

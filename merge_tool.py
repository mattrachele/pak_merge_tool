#!/usr/bin/env python3

# Version 0.2.0

"""Tool to merge Stalker 2 mod pak files into a single pak file.
    Most of the files in the pak files are text files, so the tool
    will merge the text files and remove duplicates."""

# Usage: python merge_tool.py --verbose --confirm --new_mods_dir="<dir>" --final_merged_mod_dir="<dir>"
# Example: clear;python .\merge_tool.py --new_mods_dir="..\unpacked" --final_merged_mod_dir="..\~merged_mods_v1-0_P"

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
import subprocess
import pydoc
import re
import time
import logging
import json

from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

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


def version_check(command) -> bool:
    """Check the version of a command."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            shell=True,
            check=True,
        )
        if result.returncode != 0:
            logger.warning(f"{command} is not available.")
    except FileNotFoundError:
        logger.warning(
            f"Command '{command}' not found. Ensure it is installed and added to your PATH."
        )
        return False

    return True


def validate_requirements() -> dict:
    """Validate that the required tools are available."""
    validated_requirements = {}

    # Check if less is available
    less_installed = version_check("less")
    validated_requirements["less"] = less_installed

    # Check if code is available
    code_installed = version_check("code")
    validated_requirements["code"] = code_installed

    return validated_requirements


def strip_whitespace(lines) -> list:
    """Strip leading and trailing whitespace from each line."""
    return [re.sub(r"^[ \t]+|[ \t]+$", "", line) for line in lines]


def filter_updated_lines(original_lines, new_lines) -> list:
    """Filter out the lines that were not changed."""
    return [line for line in new_lines if line not in original_lines]


def confirm_choice(original_lines, new_lines) -> str:
    """Display the new lines and ask for confirmation."""
    updated_lines = filter_updated_lines(original_lines, new_lines)
    logger.info("New lines to be added:")
    for line in updated_lines:
        logger.info("%s%s", Fore.GREEN, line.strip())
    while True:
        user_choice = input(
            "Confirm your choice:\n"
            "1. Accept\n"
            "2. Choose another option\n"
            "3. Quit and Save\n"
            "4. Quit\n"
            "Enter your choice: "
        ).strip()

        if not user_choice or user_choice not in {"1", "2", "3", "4"}:
            logger.warning("Invalid choice. Please choose again.")
            continue

        return user_choice


def view_text_with_pydoc(text) -> None:
    """View the contents of a text using pydoc."""
    # NOTE: Adding color for pydoc adds color to more than just the text provided
    pydoc_txt = "".join(text)
    pydoc.pager(pydoc_txt)


def view_text_with_less(text) -> None:
    """View the contents of a text using less."""
    # Use a copy of the text to avoid modifying the original text
    color_text = text.copy()
    # Add color to the text
    for i, line in enumerate(color_text):
        if line.startswith("+"):
            color_text[i] = Fore.GREEN + line
        elif line.startswith("-"):
            color_text[i] = Fore.RED + line
        elif line.startswith("@"):
            color_text[i] = Fore.CYAN + line

    less_txt = "".join(color_text)
    with subprocess.Popen(["less", "-R"], stdin=subprocess.PIPE) as process:
        process.communicate(input=less_txt.encode("utf-8"))


def open_files_in_vscode_compare(file1, file2) -> None:
    """Open two files in VS Code compare mode."""
    logger.info("Opening in VS Code...")
    logger.info(f"Final Merged Mod File: {file1}\n" f"New Mods File: {file2}")
    logger.info(f"Current working directory: {os.getcwd()}")

    abs_file1 = os.path.abspath(file1)
    abs_file2 = os.path.abspath(file2)

    subprocess.run(["code", "--diff", abs_file1, abs_file2], shell=True, check=True)


def disp_diff_re_print(input_vars) -> dict:
    """Re-print the display diff."""
    disp_diff_chunk = input_vars["disp_diff_chunk"]

    for line in disp_diff_chunk:
        if line.startswith("+"):
            logger.info("%s%s", Fore.GREEN, line.strip())
        elif line.startswith("-"):
            logger.info("%s%s", Fore.RED, line.strip())
        elif line.startswith("@"):
            logger.info("%s%s", Fore.CYAN, line.strip())
        else:
            logger.info("%s", line.strip())

    return {
        "status": "continue",
    }


def disp_chunk_skip_no_changes(input_vars) -> dict:
    """Skip - Keep the current chunk."""
    disp_final_merged_mod_chunk = input_vars["disp_final_merged_mod_chunk"]
    return {
        "processed_lines": disp_final_merged_mod_chunk,
        "status": "pass_through",
    }


def disp_chunk_overwrite_new_changes(input_vars) -> dict:
    """Overwrite the final_merged_mod chunk with the new_mods chunk"""
    disp_new_mod_chunk = input_vars["disp_new_mod_chunk"]
    return {
        "processed_lines": disp_new_mod_chunk,
        "status": "pass_through",
    }


def disp_chunk_save_merged_diff(input_vars) -> dict:
    """Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod"""
    disp_diff_chunk = input_vars["disp_diff_chunk"]
    merged_lines = []

    logger.info("Merging the display chunk...")

    # Use the diff to add matching lines and differing lines to the merged chunk in order
    for line in disp_diff_chunk:
        if line.startswith("@") or "++" in line or "--" in line:
            continue

        line = line[1:]
        merged_lines.append(line)

    return {
        "processed_lines": merged_lines,
        "status": "pass_through",
    }


def whole_chunk_skip_no_changes(input_vars) -> dict:
    """Skip - Keep the current chunk"""
    new_lines = input_vars["f_final_merged_mod_chunk"]
    return {
        "processed_lines": new_lines,
        "status": "return_continue",
    }


def whole_chunk_overwrite_new_changes(input_vars) -> dict:
    """Overwrite the final_merged_mod chunk with the new_mods chunk"""
    new_lines = input_vars["f_new_mod_chunk"]
    return {
        "processed_lines": new_lines,
        "status": "return_continue",
    }


def whole_chunk_save_merged_diff(input_vars) -> dict:
    """Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod"""
    f_final_merged_mod_chunk = input_vars["f_final_merged_mod_chunk"]
    display_chunk_array = input_vars["display_chunk_array"]
    diff_lines_list = input_vars["diff_lines_list"]
    merged_lines = []
    final_merged_mod_current_process_line = 0

    logger.info("Merging the whole chunk...")

    # Loop through the chunked lines and display them in chunks
    for disp_chunk_line_info in display_chunk_array:
        if not disp_chunk_line_info or disp_chunk_line_info[0] is None:
            break

        # Unified Diff starts indexing at 1, but this script uses 0-based indexing
        final_merged_mod_start_line = (
            disp_chunk_line_info[0] - 1
        )  # Force 0-based indexing
        final_merged_mod_length = disp_chunk_line_info[1]
        disp_diff_start_line = disp_chunk_line_info[4]
        disp_diff_end_line = disp_chunk_line_info[5] + 1

        disp_diff_chunk = list(diff_lines_list[disp_diff_start_line:disp_diff_end_line])

        # Load in matching lines by loading in lines from the final merged mod chunk from the last process line
        #   to the start of the current display chunk
        tmp_matching_lines = f_final_merged_mod_chunk[
            final_merged_mod_current_process_line:final_merged_mod_start_line
        ]
        if tmp_matching_lines:
            merged_lines.extend(tmp_matching_lines)
            final_merged_mod_current_process_line = final_merged_mod_start_line

        # Use the diff to add matching lines and differing lines to the merged chunk in order
        for line in disp_diff_chunk:
            if line.startswith("@") or "++" in line or "--" in line:
                continue

            line = line[1:]
            merged_lines.append(line)

        final_merged_mod_current_process_line = (
            final_merged_mod_start_line + final_merged_mod_length
        )

    # Add the last matching lines to the merged chunk
    tmp_matching_lines = f_final_merged_mod_chunk[
        final_merged_mod_current_process_line:
    ]
    if tmp_matching_lines:
        merged_lines.extend(tmp_matching_lines)

    return {
        "processed_lines": merged_lines,
        "status": "return_continue",
    }


def whole_chunk_view_diff_less(input_vars) -> dict:
    """View the whole chunk in less"""
    diff_lines_list = input_vars["diff_lines_list"]
    view_text_with_less(diff_lines_list)
    return {
        "status": "continue",
    }


def whole_file_view_temp_merged_mod_less(input_vars) -> dict:
    """View Temp Merged Mod in less"""
    temp_merged_mod_file = input_vars["temp_merged_mod_file"]
    tmp_merged_mod_lines = []
    with open(temp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
        tmp_merged_mod_lines = tmp_merged_mod.readlines()
    view_text_with_less(tmp_merged_mod_lines)
    return {
        "status": "continue",
    }


def whole_chunk_view_diff_pydoc(input_vars) -> dict:
    """View the whole chunk in pydoc"""
    diff_lines_list = input_vars["diff_lines_list"]
    view_text_with_pydoc(diff_lines_list)
    return {
        "status": "continue",
    }


def whole_file_view_temp_merged_mod_pydoc(input_vars) -> dict:
    """View Temp Merged Mod in pydoc"""
    temp_merged_mod_file = input_vars["temp_merged_mod_file"]
    tmp_merged_mod_lines = []
    with open(temp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
        tmp_merged_mod_lines = tmp_merged_mod.readlines()
    view_text_with_pydoc(tmp_merged_mod_lines)
    return {
        "status": "continue",
    }


def whole_file_open_diff_vs_code(input_vars) -> dict:
    """Open the whole chunk in VS Code"""
    new_mods_file = input_vars["new_mods_file"]
    final_merged_mod_file = input_vars["final_merged_mod_file"]
    open_files_in_vscode_compare(new_mods_file, final_merged_mod_file)
    return {
        "status": "continue",
    }


def whole_file_open_temp_merged_mod_vs_code(input_vars) -> dict:
    """Open Temp Merged Mod in VS Code"""
    final_merged_mod_file = input_vars["final_merged_mod_file"]
    open_files_in_vscode_compare(final_merged_mod_file, final_merged_mod_file + ".tmp")
    return {
        "status": "continue",
    }


def quit_save(input_vars) -> dict:
    """Quit and save the changes."""
    tmp_merged_mod_lines = input_vars["tmp_merged_mod_lines"]
    return {
        "processed_lines": tmp_merged_mod_lines,
        "status": "quit-save",
    }


def quit_out(input_vars) -> dict:
    """Quit without saving the changes."""
    return {"status": "quit"}


def load_choice_functions(valid_requirements) -> dict:
    """Load the choice functions based on the valid requirements."""
    # Define the choices for the user
    choice_number = 1
    choice_functions = {}
    default_choice_functions = [
        {"disp_diff_re_print": "Re-print the Display Diff"},
        {"disp_chunk_skip_no_changes": "Display Chunk: Skip - Make No Changes"},
        {
            "disp_chunk_overwrite_new_changes": "Display Chunk: Overwrite with New Changes"
        },
        {"disp_chunk_save_merged_diff": "Display Chunk: Merge Changes"},
        {"whole_chunk_skip_no_changes": "Whole Chunk: Skip - Make No Changes"},
        {
            "whole_chunk_overwrite_new_changes": "Whole Chunk: Overwrite with New Changes"
        },
        {"whole_chunk_save_merged_diff": "Whole Chunk: Merge Changes"},
    ]

    for choice_function in default_choice_functions:
        choice_functions[str(choice_number)] = choice_function
        choice_number += 1

    if valid_requirements["less"]:
        choice_functions[str(choice_number)] = {
            "whole_chunk_view_diff_less": "Whole Chunk: View Diff in CLI"
        }
        choice_number += 1
        choice_functions[str(choice_number)] = {
            "whole_file_view_temp_merged_mod_less": "Whole File: View Temp Merged Mod in CLI"
        }
        choice_number += 1
    else:
        logger.info("less is not available using pydoc instead.")
        choice_functions[str(choice_number)] = {
            "whole_chunk_view_diff_pydoc": "Whole Chunk: View Diff in CLI"
        }
        choice_number += 1
        choice_functions[str(choice_number)] = {
            "whole_file_view_temp_merged_mod_pydoc": "Whole File: View Temp Merged Mod in CLI"
        }
        choice_number += 1

    if valid_requirements["code"]:
        choice_functions[str(choice_number)] = {
            "whole_file_open_diff_vs_code": "Whole File: Open Diff in VS Code"
        }
        choice_number += 1
        choice_functions[str(choice_number)] = {
            "whole_file_open_temp_merged_mod_vs_code": "Whole File: Open Temp Merged Mod in VS Code"
        }
        choice_number += 1

    return choice_functions


def choice_handler(
    new_mods_file,
    final_merged_mod_file,
    diff_lines,
    f_final_merged_mod_chunk,
    f_new_mod_chunk,
    valid_requirements,
    temp_merged_mod_file,
    last_display_diff,
    last_user_choice,
    confirm_user_choice=False,
) -> dict:
    """Handle the user's choice for the diff.
    Takes in the performanced chunked lines, splits them into display chunks,
    asks the user for a choice per display chunk, allows confirmation of the choice,
    and finally outputs the new lines to be written to the tmp_merged_mod file."""

    # total_diff_lines = len(diff_lines) # Err: can't use len on a generator
    # chunk_offset = 0
    tmp_merged_mod_lines = []
    final_merged_mod_current_process_line = 0
    diff_lines_list = list(diff_lines)

    # Definitions:
    # Whole Merged Mod Chunk:       Up to 1024 lines of the Merged Mod File
    # Whole New Mod Chunk:          Up to 1024 lines of the New Mod File
    # Whole Diff Chunk:             Diff of the Whole Merged Mod Chunk and Whole New Mod Chunk
    # Display Diff Chunk:           Split Whole Diff Chunk - Start of @ to line before the next @ -> split on @
    # Display Merged Mod Chunk:     Start line to length of the Display Diff Chunk
    # Display New Mod Chunk:        Start line to length of the Display Diff Chunk

    # Search the diff_lines_list for the diff header and split the chunks based on the header
    display_chunk_array = (
        []
    )  # 2D array to store the display chunks as start line and length
    display_chunk_current_line = 0
    display_chunk_last_end_line = 0
    for line in diff_lines_list:
        if line.startswith("@"):
            if display_chunk_current_line > 0 and display_chunk_array:
                display_chunk_last_end_line = display_chunk_current_line - 1
                display_chunk_array[-1].append(display_chunk_last_end_line)
            header_parts = line.split(" ")
            final_merged_mod_chunk_info = header_parts[1]
            new_mod_chunk_info = header_parts[2]

            final_merged_mod_start_line, final_merged_mod_length = map(
                int, final_merged_mod_chunk_info[1:].split(",")
            )
            new_mod_start_line, new_mod_length = map(
                int, new_mod_chunk_info[1:].split(",")
            )

            display_chunk_array.append(
                [
                    final_merged_mod_start_line,
                    final_merged_mod_length,
                    new_mod_start_line,
                    new_mod_length,
                    display_chunk_current_line,
                ]
            )
        display_chunk_current_line += 1

    # Add the last end line to the last display chunk
    if display_chunk_array:
        display_chunk_array[-1].append(display_chunk_current_line)

    # Loop through the chunked lines and display them in chunks
    for disp_chunk_line_info in display_chunk_array:
        if not disp_chunk_line_info or disp_chunk_line_info[0] is None:
            break

        # Print the nested display chunk info
        # logger.debug(f"Display Chunk Info: {json.dumps(disp_chunk_line_info, indent=4)}")

        # Unified Diff starts indexing at 1, but this script uses 0-based indexing
        final_merged_mod_start_line = (
            disp_chunk_line_info[0] - 1
        )  # Force 0-based indexing
        final_merged_mod_length = disp_chunk_line_info[1]
        new_mod_start_line = disp_chunk_line_info[2] - 1  # Force 0-based indexing
        new_mod_length = disp_chunk_line_info[3]
        disp_diff_start_line = disp_chunk_line_info[4]
        disp_diff_end_line = disp_chunk_line_info[5] + 1

        disp_final_merged_mod_chunk = list(
            f_final_merged_mod_chunk[
                final_merged_mod_start_line : final_merged_mod_start_line
                + final_merged_mod_length
            ]
        )
        disp_new_mod_chunk = list(
            f_new_mod_chunk[new_mod_start_line : new_mod_start_line + new_mod_length]
        )
        disp_diff_chunk = list(diff_lines_list[disp_diff_start_line:disp_diff_end_line])

        # Load in matching lines by loading in lines from the final merged mod chunk from the last process line
        #   to the start of the current display chunk
        tmp_matching_lines = f_final_merged_mod_chunk[
            final_merged_mod_current_process_line:final_merged_mod_start_line
        ]
        if tmp_matching_lines:
            tmp_merged_mod_lines.extend(tmp_matching_lines)
            final_merged_mod_current_process_line = final_merged_mod_start_line

        # Check if the current display diff is the same as the previous display diff
        #   If it is, then skip the user choice and continue with the same choice as the previous display diff
        #   Most likely need to handle in the merge_files function to keep track of the previous display diff across performance chunks
        # Last Display Diff:    @@ -944,81    +1022,3 @@
        # Current Display Diff: @@ -1,3       +1,81   @@
        dup_diff_found = False
        if last_display_diff:
            last_disp_diff_parts = last_display_diff.split(" ")
            # last_disp_diff_final_mod_start_line = last_disp_diff_parts[1].split(",")[0]
            last_disp_diff_final_mod_length = last_disp_diff_parts[1].split(",")[1]
            # last_disp_diff_new_mod_start_line = last_disp_diff_parts[2].split(",")[0]
            last_disp_diff_new_mod_length = last_disp_diff_parts[2].split(",")[1]

            # TODO: Test this and see if more conditions are needed
            if int(last_disp_diff_final_mod_length) == int(new_mod_length) and int(
                last_disp_diff_new_mod_length
            ) == int(final_merged_mod_length):
                dup_diff_found = True
            else:
                logger.info(
                    f"Last Display Final Mod Length: {last_disp_diff_final_mod_length} | New Mod Length: {new_mod_length}"
                )
                logger.info(
                    f"Last Display New Mod Length: {last_disp_diff_new_mod_length} | Final Mod Length: {final_merged_mod_length}"
                )

        if last_display_diff and last_user_choice and dup_diff_found:
            logger.info("Last display diff is the same as the current display diff.")
            logger.info(f"Using the last user choice: {last_user_choice}")

            # Define the choices for the user
            choice_functions = load_choice_functions(valid_requirements)
            choice_function_dict = choice_functions.get(last_user_choice)
            choice_function = list(choice_function_dict.keys())[0]

            input_vars = {
                "disp_final_merged_mod_chunk": disp_final_merged_mod_chunk,
                "disp_new_mod_chunk": disp_new_mod_chunk,
                "disp_diff_chunk": disp_diff_chunk,
                "display_chunk_array": display_chunk_array,
                "f_final_merged_mod_chunk": f_final_merged_mod_chunk,
                "f_new_mod_chunk": f_new_mod_chunk,
                "diff_lines_list": diff_lines_list,
                "tmp_merged_mod_lines": tmp_merged_mod_lines,
                "final_merged_mod_start_line": final_merged_mod_start_line,
                "final_merged_mod_length": final_merged_mod_length,
                "valid_requirements": valid_requirements,
                "new_mods_file": new_mods_file,
                "final_merged_mod_file": final_merged_mod_file,
            }

            # Call the choice function
            result = globals()[choice_function](input_vars)
            new_lines = []

            if result["status"] == "pass_through":
                new_lines = result["processed_lines"]
            elif result["status"] == "return_continue":
                return {
                    "status": "continue",
                    "processed_lines": result["processed_lines"],
                    "last_display_diff": last_display_diff,
                    "last_user_choice": last_user_choice,
                }
            elif result["status"] == "continue":
                continue

            tmp_merged_mod_lines.extend(new_lines)
            final_merged_mod_current_process_line = (
                final_merged_mod_start_line + final_merged_mod_length
            )
            continue

        # Display the chunked lines with color coding
        for line in disp_diff_chunk:
            if line.startswith("+"):
                logger.info("%s%s", Fore.GREEN, line.strip())
            elif line.startswith("-"):
                logger.info("%s%s", Fore.RED, line.strip())
            elif line.startswith("@"):
                logger.info("%s%s", Fore.CYAN, line.strip())
                last_display_diff = line.strip()
            else:
                logger.info("%s", line.strip())

        # Define the choices for the user
        choice_functions = load_choice_functions(valid_requirements)
        choice_number = len(choice_functions) + 1

        # End by adding quit and save and quit options
        choice_functions[str(choice_number)] = {"quit_save": "Quit and Save"}
        choice_number += 1
        choice_functions[str(choice_number)] = {"quit_out": "Quit"}

        while True:
            # Ask the user for a choice for the chunk
            input_option_text = "\nOptions:\n"
            for choice_number, choice_function in choice_functions.items():
                input_option_text += (
                    f"{choice_number}. {list(choice_function.values())[0]}\n"
                )

            input_option_text += "Enter your choice: "
            user_choice = input(input_option_text)

            if not user_choice in choice_functions:
                logger.warning("Invalid choice. Please choose again.")
                continue

            choice_function_dict = choice_functions.get(user_choice)
            choice_function = list(choice_function_dict.keys())[0]

            input_vars = {
                "disp_final_merged_mod_chunk": disp_final_merged_mod_chunk,
                "disp_new_mod_chunk": disp_new_mod_chunk,
                "disp_diff_chunk": disp_diff_chunk,
                "display_chunk_array": display_chunk_array,
                "f_final_merged_mod_chunk": f_final_merged_mod_chunk,
                "f_new_mod_chunk": f_new_mod_chunk,
                "diff_lines_list": diff_lines_list,
                "tmp_merged_mod_lines": tmp_merged_mod_lines,
                "temp_merged_mod_file": temp_merged_mod_file,
                "final_merged_mod_start_line": final_merged_mod_start_line,
                "final_merged_mod_length": final_merged_mod_length,
                "valid_requirements": valid_requirements,
                "new_mods_file": new_mods_file,
                "final_merged_mod_file": final_merged_mod_file,
            }

            # Call the choice function
            result = globals()[choice_function](input_vars)
            new_lines = []

            if result["status"] == "pass_through":
                new_lines = result["processed_lines"]
            elif result["status"] == "return_continue":
                return {
                    "status": "continue",
                    "processed_lines": result["processed_lines"],
                    "last_display_diff": last_display_diff,
                    "last_user_choice": user_choice,
                }
            elif result["status"] == "continue":
                continue
            elif result["status"] == "quit-save":
                return {
                    "status": "quit-save",
                    "processed_lines": result["processed_lines"],
                }
            elif result["status"] == "quit":
                return {"status": "quit"}

            # If cmd line argument is set, confirm the user's choice
            if confirm_user_choice:
                confirm = confirm_choice(disp_final_merged_mod_chunk, new_lines)
                if confirm == "1":
                    tmp_merged_mod_lines.extend(new_lines)
                    final_merged_mod_current_process_line = (
                        final_merged_mod_start_line + final_merged_mod_length
                    )
                    break

                if confirm == "2":
                    continue

                if confirm == "3":
                    tmp_merged_mod_lines.extend(new_lines)
                    return {
                        "status": "quit-save",
                        "processed_lines": tmp_merged_mod_lines,
                    }

                if confirm == "4":
                    return {"status": "quit"}
            else:
                tmp_merged_mod_lines.extend(new_lines)
                final_merged_mod_current_process_line = (
                    final_merged_mod_start_line + final_merged_mod_length
                )
                break

    # Add the last matching lines to the merged chunk
    tmp_matching_lines = f_final_merged_mod_chunk[
        final_merged_mod_current_process_line:
    ]
    if tmp_matching_lines:
        tmp_merged_mod_lines.extend(tmp_matching_lines)

    return {
        "status": "continue",
        "processed_lines": tmp_merged_mod_lines,
        "last_display_diff": last_display_diff,
        "last_user_choice": user_choice,
    }


def reload_temp_merged_mod_file(temp_merged_mod_file) -> int:
    """Reload the temporary merged mod file and return the last processed line."""
    if not os.path.exists(temp_merged_mod_file):
        return 0

    with open(temp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
        lines = tmp_merged_mod.readlines()
        last_processed_line = len(lines)

    return last_processed_line


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


def merge_files(
    new_mods_file, final_merged_mod_file, valid_requirements, confirm_user_choice=False
) -> str:
    """Merge the contents of two text files, handling conflicts."""
    max_perf_chunk_size = 1024  # Define the chunk size for reading the files
    perf_chunk = 0  # Initialize the performance chunk counter
    quit_out_bool = False
    final_perf_chunk_sizes = []
    last_display_diff = ""
    last_user_choice = 0
    final_merged_mod_filepath_no_ext, _ = os.path.splitext(final_merged_mod_file)
    perf_chunk_sizes_file = final_merged_mod_filepath_no_ext + "_perf_chunk_sizes.tmp"

    # Reload the perf_chunk_sizes_file to get the final_perf_chunk_sizes
    if os.path.exists(perf_chunk_sizes_file):
        with open(perf_chunk_sizes_file, "r", encoding="utf-8") as f:
            final_perf_chunk_sizes = json.loads(f.read())

    logger.info(f"\n\tMrg: {new_mods_file}\n\tNew: {final_merged_mod_file}")
    start_time = time.time()

    # Create a temporary file to store the merged contents
    temp_merged_mod_file = final_merged_mod_file + ".tmp"
    # Check if the temporary file exists and reload the last processed line
    last_processed_line = reload_temp_merged_mod_file(temp_merged_mod_file)

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

            formatted_new_mod_chunk = strip_whitespace(new_mod_chunk)
            formatted_final_merged_mod_chunk = strip_whitespace(final_merged_mod_chunk)

            if formatted_new_mod_chunk == formatted_final_merged_mod_chunk:
                # If the chunks are identical, write the final_merged_mod_chunk to the temporary file
                final_perf_chunk_sizes.append(len(formatted_final_merged_mod_chunk))
                temp_merged_mod.writelines(final_merged_mod_chunk)
                temp_merged_mod.flush()  # Flush the buffer to write the lines to the file
                continue

            # Use difflib to create a unified diff for the chunk
            diff = difflib.unified_diff(
                formatted_final_merged_mod_chunk,
                formatted_new_mod_chunk,
                fromfile=final_merged_mod_file,
                tofile=new_mods_file,
            )

            logger.info("\n\nHandling diff...")
            # Handle the user's choice for the diff
            choice = choice_handler(
                new_mods_file,
                final_merged_mod_file,
                diff,
                formatted_final_merged_mod_chunk,
                formatted_new_mod_chunk,
                valid_requirements,
                temp_merged_mod_file,
                last_display_diff,
                last_user_choice,
                confirm_user_choice,
            )

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

    if not quit_out_bool:
        # Move the temporary file to the final_merged_mod_file
        shutil.move(temp_merged_mod_file, final_merged_mod_file)

    # Delete the temporary file
    if os.path.exists(temp_merged_mod_file):
        os.remove(temp_merged_mod_file)

    # Delete the perf_chunk_sizes_file
    if os.path.exists(perf_chunk_sizes_file):
        os.remove(perf_chunk_sizes_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Processing time: {elapsed_time:.2f} seconds\n")

    if quit_out_bool:
        return "quit"

    return "continue"


def merge_directories(
    new_mods_dir, final_merged_mod_dir, valid_requirements, confirm_user_choice=False
) -> str:
    """Recursively merge the contents of two directories."""
    # Ensure the final_merged_mod directory exists
    if not os.path.exists(final_merged_mod_dir):
        os.makedirs(final_merged_mod_dir)

    # Iterate through all items in the new_mods directory
    for item in os.listdir(new_mods_dir):
        new_mods_item = os.path.join(new_mods_dir, item)
        final_merged_mod_item = os.path.join(final_merged_mod_dir, item)

        if os.path.isdir(new_mods_item):
            logger.debug(f"New Mods Item is a dir: {new_mods_item}")
            # If the item is a directory, recursively merge it
            result = merge_directories(
                new_mods_item,
                final_merged_mod_item,
                valid_requirements,
                confirm_user_choice,
            )
            if result == "quit":
                return "quit"
        else:
            logger.debug(f"New Mods Item is a file: {new_mods_item}")
            # If the item is a file, handle conflicts
            if os.path.exists(final_merged_mod_item):
                logger.debug(f"Final Merged Mod Item exists: {final_merged_mod_item}")
                result = merge_files(
                    new_mods_item,
                    final_merged_mod_item,
                    valid_requirements,
                    confirm_user_choice,
                )
                if result == "quit":
                    return "quit"
            else:
                logger.debug(
                    f"Final Merged Mod Item does not exist: {final_merged_mod_item}"
                )
                shutil.copy2(new_mods_item, final_merged_mod_item)
    return "continue"


def main() -> bool:
    """Main function to merge mod directories."""
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description="Merge mod directories.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--confirm", action="store_true", help="Disable user confirmation"
    )
    parser.add_argument("--new_mods_dir", help="The directory containing the new mods")
    parser.add_argument(
        "--final_merged_mod_dir", help="The directory containing the final merged mods"
    )
    args = parser.parse_args()

    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Confirm: {args.confirm}")

    if not args.new_mods_dir or not args.final_merged_mod_dir:
        logger.error(
            "new_mods_dir and final_merged_mod_dir are required as cmd ln args."
        )
        return False

    # Validate the requirements
    valid_requirements = validate_requirements()

    # Check if the final_merged_mod_dir is a directory and isn't inside the new_mods_dir
    if not os.path.isdir(args.final_merged_mod_dir):
        logger.error(f"{args.final_merged_mod_dir} is not a directory.")
        return False

    # Check if the new_mods_dir is a directory
    if not os.path.isdir(args.new_mods_dir):
        logger.error(f"{args.new_mods_dir} is not a directory.")
        return False

    final_merged_mod_dir_abs = os.path.abspath(args.final_merged_mod_dir)
    new_mods_dir_abs = os.path.abspath(args.new_mods_dir)
    if new_mods_dir_abs.startswith(
        final_merged_mod_dir_abs
    ) or final_merged_mod_dir_abs.startswith(new_mods_dir_abs):
        logger.error("Cannot merge directories that are inside each other.")
        return False

    # Iterate through all directories in the new_mods base directory
    for path_name in os.listdir(args.new_mods_dir):
        new_mods_path = os.path.join(args.new_mods_dir, path_name)
        final_merged_mod_path = os.path.join(args.final_merged_mod_dir, path_name)

        logger.info(f"{'Processing new mods path:':<33} {new_mods_path}")

        # Check if the item is a directory
        if os.path.isdir(new_mods_path):
            logger.info(
                f"Merging new mods dir: {new_mods_path} to final merged mod dir: {final_merged_mod_path}"
            )
            result = merge_directories(
                new_mods_path,
                final_merged_mod_path,
                valid_requirements,
                args.confirm,
            )
            if result == "quit":
                logger.info("Merge aborted.")
                return False

        # Handle the case where the item is a file in the root directory
        else:
            logger.info(f"Processing final merged mod path: {final_merged_mod_path}")

            # Validate the file extension to ensure it's a text file and not a binary file
            file_extension = os.path.splitext(new_mods_path)[1]
            valid_file_extensions = {
                ".txt",
                ".cfg",
                ".ini",
                ".lua",
                ".json",
                ".xml",
                ".yml",
                ".yaml",
                ".md",
                ".bat",
                ".sh",
            }
            if file_extension not in valid_file_extensions:
                logger.warning(
                    f"Skipping {new_mods_path} because it's not a text file or a known file type."
                )
                continue

            # Check if the final merged mod file exists and just copy it over if it doesn't
            if not os.path.exists(final_merged_mod_path):
                logger.info(
                    f"Final merged mod file does not exist. Copying {new_mods_path} to {final_merged_mod_path}"
                )
                shutil.copy2(new_mods_path, final_merged_mod_path)
                continue

            result = merge_files(
                new_mods_path,
                final_merged_mod_path,
                valid_requirements,
                args.confirm,
            )
            if result == "quit":
                logger.info("Merge aborted.")
                return False

    logger.info("Merge complete.")
    return True


if __name__ == "__main__":
    main()

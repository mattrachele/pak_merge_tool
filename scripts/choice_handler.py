#!/usr/bin/env python3

# Version 0.1.0

"""This module contains functions to handle choices for the merge tool."""

import logging
import subprocess
import pydoc
import os

from colorama import init, Fore

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


def confirm_choice(original_lines, new_lines) -> str:
    """Display the new lines and ask for confirmation."""
    updated_lines = [line for line in new_lines if line not in original_lines]
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


def skip_file(input_vars) -> dict:
    """Skip the file and continue to the next file."""
    return {
        "status": "skip",
    }


def overwrite(input_vars) -> dict:
    """Overwrite the whole file with the new mod file."""
    return {
        "status": "overwrite",
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
        choice_functions[str(len(choice_functions) + 1)] = choice_function

    if valid_requirements["less"]:
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_chunk_view_diff_less": "Whole Chunk: View Diff in CLI"
        }
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_file_view_temp_merged_mod_less": "Whole File: View Temp Merged Mod in CLI"
        }
    else:
        logger.info("less is not available using pydoc instead.")
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_chunk_view_diff_pydoc": "Whole Chunk: View Diff in CLI"
        }
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_file_view_temp_merged_mod_pydoc": "Whole File: View Temp Merged Mod in CLI"
        }

    if valid_requirements["code"]:
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_file_open_diff_vs_code": "Whole File: Open Diff in VS Code"
        }
        choice_functions[str(len(choice_functions) + 1)] = {
            "whole_file_open_temp_merged_mod_vs_code": "Whole File: Open Temp Merged Mod in VS Code"
        }

    choice_functions[str(len(choice_functions) + 1)] = {
        "skip_file": "Whole File: Skip - Make No Changes"
    }
    choice_functions[str(len(choice_functions) + 1)] = {
        "overwrite": "Whole File: Overwrite with New Changes"
    }
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
    MAX_LINES_TO_DISPLAY = 100

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

    user_choice = ""

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

        # If display diff is too large then force into less if available if not then pydoc
        disp_diff_chunk_size = len(disp_diff_chunk)
        if disp_diff_chunk_size > MAX_LINES_TO_DISPLAY:
            if valid_requirements["less"]:
                view_text_with_less(disp_diff_chunk)
            else:
                view_text_with_pydoc(disp_diff_chunk)

            for line in disp_diff_chunk:
                if line.startswith("@"):
                    last_display_diff = line.strip()
        else:
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

        # TODO: Visual progress of merging - line numbers and total lines
        # TODO: Display new mod name and final merged mod name in a more readable format and add path after the name
        logger.info(
            f"\n\t{'Final Merged Mod File:':<25} {final_merged_mod_file}\n\t{'New Mods File:':<25} {new_mods_file}"
        )

        # Define the choices for the user
        choice_functions = load_choice_functions(valid_requirements)
        choice_number = len(choice_functions) + 1

        # End by adding quit and save and quit options
        choice_functions[str(len(choice_functions) + 1)] = {
            "quit_save": "Quit and Save"
        }
        choice_functions[str(len(choice_functions) + 1)] = {"quit_out": "Quit"}

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
            elif result["status"] == "skip":
                return {"status": "skip"}
            elif result["status"] == "overwrite":
                return {"status": "overwrite"}
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


def non_text_file_choice_handler(final_merged_mod_path, new_mods_path) -> dict:
    """Handle the choice for non-text files."""
    while True:
        logger.info(f"\n\tMrg: {final_merged_mod_path}\n\tNew: {new_mods_path}")
        user_choice = (
            input(
                "\nNon-text file detected. Options:\n"
                "1. Skip\n"
                "2. Overwrite\n"
                "3. Quit\n"
                "Enter your choice: "
            )
            .strip()
            .lower()
        )

        if not user_choice or user_choice not in {"1", "2", "3"}:
            logger.warning("Invalid choice. Please choose again.")
            continue

        if user_choice == "1":
            return {"status": "skip"}
        if user_choice == "2":
            return {"status": "overwrite"}
        if user_choice == "3":
            return {"status": "quit"}

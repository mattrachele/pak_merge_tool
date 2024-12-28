#!/usr/bin/env python3

# Version 0.1.1

"""Tool to merge Stalker 2 mod pak files into a single pak file.
    Most of the files in the pak files are text files, so the tool
    will merge the text files and remove duplicates."""

# Usage: python merge_tool.py --verbose --confirm
# Example: clear;python .\merge_tool.py --new_mods_dir="..\unpacked" --final_merged_mod_dir="..\unpacked\~merged_mods_v1-0_P"

# Step 1: Unpak the pak files using ReUnpak.bat (Uses repak.exe)

# Step 2: Scan through unpacked/ and merge the new directories into the ~merged_mods_v1-0/ directory
# Should add new code from incoming mods without removing any existing code
# Should update existing code with new code from incoming mods
# Should have an option to give user a choice between existing code and new code

# TODO: Add a comment to the merged file with the name of the mod that the code came from with a date and version number
# TODO: Add support for version checking to display version differences and check for lines removed in newer versions
# TODO: Add direct support to call repak to handle the pak files
# TODO: Add handling for utoc and ucas files

import os
import shutil
import difflib
import argparse
import subprocess
import pydoc
import json
import re
import time
from tqdm import tqdm
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)


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
            print(f"{command} is not available.")
    except FileNotFoundError:
        print(
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
    print("New lines to be added:")
    for line in updated_lines:
        print(Fore.GREEN + line, end="")
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
            print("Invalid choice. Please choose again.")
            continue

        return user_choice


def view_text_with_pydoc(text) -> None:
    """View the contents of a text using pydoc."""
    pydoc_txt = "".join(text)
    pydoc.pager(pydoc_txt)


def view_text_with_less(text) -> None:
    """View the contents of a text using less."""
    # Add color to the text
    for i, line in enumerate(text):
        if line.startswith("+"):
            text[i] = Fore.GREEN + line
        elif line.startswith("-"):
            text[i] = Fore.RED + line
        elif line.startswith("@"):
            text[i] = Fore.CYAN + line

    less_txt = "".join(text)
    with subprocess.Popen(["less", "-R"], stdin=subprocess.PIPE) as process:
        process.communicate(input=less_txt.encode("utf-8"))


def open_files_in_vscode_compare(file1, file2) -> None:
    """Open two files in VS Code compare mode."""
    print("Opening in VS Code...")
    print(f"Final Merged Mod File: {file1}\n" f"New Mods File: {file2}")
    print(f"Current working directory: {os.getcwd()}")

    abs_file1 = os.path.abspath(file1)
    abs_file2 = os.path.abspath(file2)

    subprocess.run(["code", "--diff", abs_file1, abs_file2], shell=True, check=True)


def choice_handler(
    new_mods_file,
    final_merged_mod_file,
    diff_lines,
    f_final_merged_mod_chunk,
    f_new_mod_chunk,
    valid_requirements,
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
        print(f"Display Chunk Info: {json.dumps(disp_chunk_line_info, indent=4)}")

        final_merged_mod_start_line = disp_chunk_line_info[0]
        final_merged_mod_length = disp_chunk_line_info[1]
        new_mod_start_line = disp_chunk_line_info[2]
        new_mod_length = disp_chunk_line_info[3]
        disp_diff_start_line = disp_chunk_line_info[4]
        disp_diff_end_line = disp_chunk_line_info[5]

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

        # NOTE: Could be issues near end of chunks, however, KISS for now - just use gui editor for those cases

        # Display the chunked lines with color coding
        for line in disp_diff_chunk:
            if line.startswith("+"):
                print(Fore.GREEN + line, end="")
            elif line.startswith("-"):
                print(Fore.RED + line, end="")
            elif line.startswith("@"):
                print(Fore.CYAN + line, end="")
            else:
                print(line, end="")

        while True:
            # Ask the user for a choice for the chunk
            user_choice = input(
                "\nOptions:\n"
                "1.  Display Chunk: Skip - Make No Changes\n"
                "2.  Display Chunk: Overwrite with New Changes\n"
                "3.  Display Chunk: Insert only New Lines\n"
                "4.  Whole Chunk: Skip - Make No Changes\n"
                "5.  Whole Chunk: Overwrite with New Changes\n"
                "6.  Whole Chunk: Insert only New Lines\n"
                "7.  Whole Chunk: View in CLI\n"
                "8.  Whole Chunk: Open in VS Code\n"
                "9.  Quit and Save\n"
                "10. Quit\n"
                "Enter your choice: "
            ).strip()

            if not user_choice or user_choice not in {
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
            }:
                print("Invalid choice. Please choose again.")
                continue

            if user_choice == "9":
                return {
                    "processed_lines": tmp_merged_mod_lines,
                    "status": "quit-save",
                }

            if user_choice == "10":
                return {"status": "quit"}

            if user_choice == "1":
                # Skip - Keep the current chunk
                new_lines = disp_final_merged_mod_chunk
            elif user_choice == "2":
                # Overwrite the final_merged_mod chunk with the new_mods chunk
                new_lines = disp_new_mod_chunk
            elif user_choice == "3":
                # Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod
                new_lines = [
                    line
                    for line in disp_new_mod_chunk
                    if line not in disp_final_merged_mod_chunk
                ]
            elif user_choice == "4":
                # Skip - Keep the current chunk
                new_lines = f_final_merged_mod_chunk
                return {
                    "processed_lines": new_lines,
                    "status": "continue",
                }
            elif user_choice == "5":
                # Overwrite the final_merged_mod chunk with the new_mods chunk
                new_lines = f_new_mod_chunk
                return {
                    "processed_lines": new_lines,
                    "status": "continue",
                }
            elif user_choice == "6":
                # Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod
                new_lines = [
                    line
                    for line in f_new_mod_chunk
                    if line not in f_final_merged_mod_chunk
                ]
                return {
                    "processed_lines": new_lines,
                    "status": "continue",
                }
            elif user_choice == "7":
                if not valid_requirements["less"]:
                    print(
                        "less is not available. Please install it to use this feature. Viewing with pydoc instead."
                    )
                    view_text_with_pydoc(diff_lines_list)
                    continue
                # View the whole chunk in the CLI
                view_text_with_less(diff_lines_list)
                continue
            elif user_choice == "8":
                # TODO: Update to allow usage with other editors
                if not valid_requirements["code"]:
                    print(
                        "code is not available. Please install it to use this feature."
                    )
                    continue
                # Open the whole chunk in VS Code
                open_files_in_vscode_compare(final_merged_mod_file, new_mods_file)
                continue

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

    return {
        "status": "continue",
        "processed_lines": tmp_merged_mod_lines,
    }


def reload_tmp_merged_mod_file(tmp_merged_mod_file) -> int:
    """Reload the temporary merged mod file and return the last processed line."""
    if not os.path.exists(tmp_merged_mod_file):
        return 0

    with open(tmp_merged_mod_file, "r", encoding="utf-8") as tmp_merged_mod:
        lines = tmp_merged_mod.readlines()
        last_processed_line = len(lines)

    return last_processed_line


def merge_files(
    new_mods_file, final_merged_mod_file, valid_requirements, confirm_user_choice=False
) -> str:
    """Merge the contents of two text files, handling conflicts."""
    max_perf_chunk_size = 1024  # Define the chunk size for reading the files

    print(f"Mrg: {new_mods_file}\n" f"New: {final_merged_mod_file}")

    new_mod_size = os.path.getsize(new_mods_file)
    # final_merged_mod_size = os.path.getsize(final_merged_mod_file)
    start_time = time.time()

    # Create a temporary file to store the merged contents
    temp_merged_mod_file = final_merged_mod_file + ".tmp"
    # Check if the temporary file exists and reload the last processed line
    last_processed_line = reload_tmp_merged_mod_file(temp_merged_mod_file)

    with open(new_mods_file, "r", encoding="utf-8") as new_mod, open(
        final_merged_mod_file, "r", encoding="utf-8"
    ) as final_merged_mod, open(
        temp_merged_mod_file, "w", encoding="utf-8"
    ) as temp_merged_mod:
        with tqdm(
            total=new_mod_size, unit="B", unit_scale=True, desc=new_mods_file
        ) as pbar:
            # if last_processed_line is not 0, skip to the last processed line
            if last_processed_line:
                for _ in range(last_processed_line):
                    next(new_mod)
                    next(final_merged_mod)

            while True:
                # Read a chunk of lines from each file based on the chunk size
                new_mod_chunk = [
                    line
                    for line in (
                        next(new_mod, None) for _ in range(max_perf_chunk_size)
                    )
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
                formatted_final_merged_mod_chunk = strip_whitespace(
                    final_merged_mod_chunk
                )

                if formatted_new_mod_chunk == formatted_final_merged_mod_chunk:
                    # If the chunks are identical, write the final_merged_mod_chunk to the temporary file
                    temp_merged_mod.writelines(final_merged_mod_chunk)
                    pbar.update(len("".join(new_mod_chunk)))
                    continue

                # Use difflib to create a unified diff for the chunk
                diff = difflib.unified_diff(
                    formatted_final_merged_mod_chunk,
                    formatted_new_mod_chunk,
                    fromfile=final_merged_mod_file,
                    tofile=new_mods_file,
                )

                print("\nHandling diff...")
                # Handle the user's choice for the diff
                choice = choice_handler(
                    new_mods_file,
                    final_merged_mod_file,
                    diff,
                    formatted_final_merged_mod_chunk,
                    formatted_new_mod_chunk,
                    valid_requirements,
                    confirm_user_choice,
                )

                if choice["status"] == "quit-save":
                    temp_merged_mod.writelines(choice["processed_lines"])
                    return "quit"

                if choice["status"] == "quit":
                    return "quit"

                # Write the new lines to the temporary file
                temp_merged_mod.writelines(choice["processed_lines"])

                pbar.update(len("".join(new_mod_chunk)))
            # if EOF update the progress bar to 100%
            pbar.update(new_mod_size - pbar.n)

    # Move the temporary file to the final_merged_mod_file
    shutil.move(temp_merged_mod_file, final_merged_mod_file)

    # Delete the temporary file
    if os.path.exists(temp_merged_mod_file):
        os.remove(temp_merged_mod_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Processing time: {elapsed_time:.2f} seconds")
    print()
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
            # If the item is a file, handle conflicts
            if os.path.exists(final_merged_mod_item):
                result = merge_files(
                    new_mods_item,
                    final_merged_mod_item,
                    valid_requirements,
                    confirm_user_choice,
                )
                if result == "quit":
                    return "quit"
            else:
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

    print(f"Verbose: {args.verbose}")
    print(f"Confirm: {args.confirm}")

    if not args.new_mods_dir or not args.final_merged_mod_dir:
        print("new_mods_dir and final_merged_mod_dir are required as cmd ln args.")
        return False

    # Validate the requirements
    valid_requirements = validate_requirements()

    # Check if the final_merged_mod_dir is a directory and isn't inside the new_mods_dir
    if not os.path.isdir(args.final_merged_mod_dir):
        print(f"{args.final_merged_mod_dir} is not a directory.")
        return False

    # Check if the new_mods_dir is a directory
    if not os.path.isdir(args.new_mods_dir):
        print(f"{args.new_mods_dir} is not a directory.")
        return False

    final_merged_mod_dir_abs = os.path.abspath(args.final_merged_mod_dir)
    new_mods_dir_abs = os.path.abspath(args.new_mods_dir)
    if new_mods_dir_abs.startswith(
        final_merged_mod_dir_abs
    ) or final_merged_mod_dir_abs.startswith(new_mods_dir_abs):
        print("Cannot merge directories that are inside each other.")
        return False

    # Iterate through all directories in the new_mods base directory
    for path_name in os.listdir(args.new_mods_dir):
        new_mods_path = os.path.join(args.new_mods_dir, path_name)
        print(f"Processing new mods path: {new_mods_path}")
        # Check if the item is a directory
        if os.path.isdir(new_mods_path):
            result = merge_directories(
                new_mods_path,
                args.final_merged_mod_dir,
                valid_requirements,
                args.confirm,
            )
            if result == "quit":
                print("Merge aborted.")
                return False

        # Handle the case where the item is a file in the root directory
        else:
            final_merged_mod_path = os.path.join(args.final_merged_mod_dir, path_name)
            print(f"Processing final merged mod path: {final_merged_mod_path}")

            # Check if the final merged mod file exists and just copy it over if it doesn't
            if not os.path.exists(final_merged_mod_path):
                shutil.copy2(new_mods_path, final_merged_mod_path)
                continue

            result = merge_files(
                new_mods_path,
                final_merged_mod_path,
                valid_requirements,
                args.confirm,
            )
            if result == "quit":
                print("Merge aborted.")
                return False

    print("Merge complete.")
    return True


if __name__ == "__main__":
    main()

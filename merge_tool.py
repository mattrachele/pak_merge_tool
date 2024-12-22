#!/usr/bin/env python3

"""Tool to merge Stalker 2 mod pak files into a single pak file.
    Most of the files in the pak files are text files, so the tool
    will merge the text files and remove duplicates."""

# Step 1: Unpak the pak files using ReUnpak.bat (Uses repak.exe)

# Step 2: Scan through unpacked/ and merge the new directories into the ~merged_mods_v1-0/ directory
    # Should add new code from incoming mods without removing any existing code
    # Should update existing code with new code from incoming mods
        # Should have an option to give user a choice between existing code and new code

# Wishlist:
# - Add a comment to the merged file with the name of the mod that the code came from with a date and version number
#   - Add support for version checking to display version differences and check for lines removed in newer versions
# - Add direct support to call repak to handle the pak files
# - Add handling for utoc and ucas files

import os
import shutil
import difflib
import argparse
from tqdm import tqdm
import time
from colorama import init, Fore, Style
import re

# Initialize colorama
init(autoreset=True)

def strip_whitespace(lines):
    """Strip leading and trailing whitespace from each line."""
    return [re.sub(r'^[ \t]+|[ \t]+$', '', line) for line in lines]

# def display_diff(diff_lines, disp_chunk_size=10):
#     """Display the diff in chunks and allow the user to handle each chunk."""
#     diff_iter = iter(diff_lines)
#     while True:
#         chunk = list(next(diff_iter, None) for _ in range(disp_chunk_size))
#         if not chunk or chunk[0] is None:
#             break
#         for line in chunk:
#             if line.startswith('+'):
#                 print(Fore.GREEN + line, end='')
#             elif line.startswith('-'):
#                 print(Fore.RED + line, end='')
#             elif line.startswith('@'):
#                 print(Fore.CYAN + line, end='')
#             else:
#                 print(line, end='')
#         user_choice = input("Choose an option for this chunk:\n"
#                             "1. Skip - Make No Changes\n"
#                             "2. Overwrite with New Changes\n"
#                             "3. Insert only New Lines\n"
#                             "4. Quit\n"
#                             "Enter your choice (1/2/3/4): ").strip()
#         if user_choice in {'1', '2', '3', '4'}:
#             return user_choice
#     return None

def filter_updated_lines(original_lines, new_lines):
    """Filter out the lines that were not changed."""
    return [line for line in new_lines if line not in original_lines]

def confirm_choice(original_lines, new_lines):
    """Display the new lines and ask for confirmation."""
    # FIXME: Still displays way too many lines at once
    updated_lines = filter_updated_lines(original_lines, new_lines)
    print("New lines to be added:")
    for line in updated_lines:
        print(Fore.GREEN + line, end='')
    while True:
        user_choice = input("Confirm your choice:\n"
                            "1. Accept\n"
                            "2. Choose another option\n"
                            "3. Quit\n"
                            "Enter your choice (1/2/3): ").strip()
        if user_choice in {'1', '2', '3'}:
            return user_choice
        else:
            print("Invalid choice. Please choose again.")

def choice_handler(diff_lines, f_final_merged_mod_chunk, f_new_mod_chunk, confirm=False, disp_chunk_size=10):
    """Handle the user's choice for the diff.
    Takes in the performanced chunked lines, splits them into display chunks,
    asks the user for a choice per display chunk, allows confirmation of the choice,
    and finally outputs the new lines to be written to the tmp_merged_mod file."""

    total_diff_lines = len(diff_lines)
    chunk_offset = 0
    tmp_merged_mod_lines = []

    # Create an array to store the start and end line numbers for the merged and new mod chunks
    diff_chunk_line_numbers = []
    for line in diff_lines:
        if line.startswith('@'):
            # Example of diff header: @@ -1,4 +1,5 @@
            header_parts = line.split(' ')
            final_merged_mod_chunk_info = header_parts[1]
            new_mod_chunk_info = header_parts[2]

            final_merged_mod_start_line, final_merged_mod_length = map(int, final_merged_mod_chunk_info[1:].split(','))
            new_mod_start_line, new_mod_length = map(int, new_mod_chunk_info[1:].split(','))

            final_merged_mod_end_line = final_merged_mod_start_line + final_merged_mod_length - 1
            new_mod_end_line = new_mod_start_line + new_mod_length - 1

            diff_chunk_line_numbers.append({
                'final_merged_mod_chunk_start_line': final_merged_mod_start_line,
                'final_merged_mod_chunk_end_line': final_merged_mod_end_line,
                'new_mod_chunk_start_line': new_mod_start_line,
                'new_mod_chunk_end_line': new_mod_end_line
            })

    # Loop through the chunked lines and display them in chunks
    while chunk_offset < total_diff_lines:
        disp_diff_chunk = list(diff_lines[chunk_offset:chunk_offset+disp_chunk_size])
        if not disp_diff_chunk or disp_diff_chunk[0] is None:
            break

        # TODO: Get start and end line numbers from the diff chunk to save the final and new mod chunks
        # disp_final_merged_mod_chunk = list(f_final_merged_mod_chunk[chunk_offset:chunk_offset+disp_chunk_size])
        # disp_new_mod_chunk = list(f_new_mod_chunk[chunk_offset:chunk_offset+disp_chunk_size])

        # TODO: Use the start and end line numbers to get the final and new mod chunks


        # Display the chunked lines with color coding
        for line in disp_diff_chunk:
            if line.startswith('+'):
                print(Fore.GREEN + line, end='')
            elif line.startswith('-'):
                print(Fore.RED + line, end='')
            elif line.startswith('@'):
                print(Fore.CYAN + line, end='')
            else:
                print(line, end='')

        while True:
            # Ask the user for a choice for the chunk
            user_choice = input("Choose an option for this chunk:\n"
                                "1. Skip - Make No Changes\n"
                                "2. Overwrite with New Changes\n"
                                "3. Insert only New Lines\n"
                                "4. Quit\n"
                                "Enter your choice (1/2/3/4): ").strip()

            if not user_choice or user_choice not in {'1', '2', '3', '4'}:
                print("Invalid choice. Please choose again.")
                continue

            if user_choice in {'1', '2', '3', '4'}:
                if user_choice == '4':
                    return 'quit'

                if user_choice == '1':
                    # Skip - Keep the current chunk
                    new_lines = disp_final_merged_mod_chunk
                elif user_choice == '2':
                    # Overwrite the final_merged_mod chunk with the new_mods chunk
                    new_lines = disp_new_mod_chunk
                elif user_choice == '3':
                    # Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod
                    new_lines = [line for line in disp_new_mod_chunk if line not in disp_final_merged_mod_chunk]

                # If cmd line argument is set, confirm the user's choice
                if confirm:
                    confirm = confirm_choice(disp_final_merged_mod_chunk, new_lines)
                    if confirm == '1':
                        tmp_merged_mod_lines.extend(new_lines)
                        chunk_offset += disp_chunk_size
                        break
                    elif confirm == '2':
                        continue
                    elif confirm == '3':
                        return 'quit'

                tmp_merged_mod_lines.extend(new_lines)
                chunk_offset += disp_chunk_size
                break

    return tmp_merged_mod_lines

def merge_files(new_mods_file, final_merged_mod_file, verbose=False, confirm_changes=False):
    """Merge the contents of two text files, handling conflicts."""
    perf_chunk_size = 1024 # Define the chunk size for reading the files

    print(f"Mrg: {new_mods_file}\n"
          f"New: {final_merged_mod_file}")

    new_mod_size = os.path.getsize(new_mods_file)
    final_merged_mod_size = os.path.getsize(final_merged_mod_file)
    start_time = time.time()

    # Create a temporary file to store the merged contents
    temp_merged_mod_file = final_merged_mod_file + '.tmp'
    with open(new_mods_file, 'r') as new_mod, open(final_merged_mod_file, 'r') as final_merged_mod, open(temp_merged_mod_file, 'w') as temp_merged_mod:
        with tqdm(total=new_mod_size, unit='B', unit_scale=True, desc=new_mods_file) as pbar:
            while True:
                # Read a chunk of lines from each file based on the chunk size
                # NOTE: Seems next iterates so no need for an offset variable
                new_mod_chunk = [line for line in (next(new_mod, None) for _ in range(perf_chunk_size)) if line is not None]
                final_merged_mod_chunk = [line for line in (next(final_merged_mod, None) for _ in range(perf_chunk_size)) if line is not None]

                if not new_mod_chunk and not final_merged_mod_chunk:
                    break

                formatted_new_mod_chunk = strip_whitespace(new_mod_chunk)
                formatted_final_merged_mod_chunk = strip_whitespace(final_merged_mod_chunk)

                if formatted_new_mod_chunk == formatted_final_merged_mod_chunk:
                    # If the chunks are identical, do nothing
                    pbar.update(len(''.join(new_mod_chunk)))
                    continue

                # Use difflib to create a unified diff for the chunk
                diff = difflib.unified_diff(formatted_final_merged_mod_chunk, formatted_new_mod_chunk, fromfile=final_merged_mod_file, tofile=new_mods_file)

                print("\nHandling diff...")
                # FIXME: Seems like still getting 1000 lines, making one choice, then going to next 1000 lines
                # Display the diff in chunks and ask the user how to handle it
                # while True:
                #     user_choice = display_diff(diff)
                #     if user_choice == '1':
                #         # Skip - Keep the current chunk
                #         break
                #     elif user_choice == '2':
                #         # Overwrite the final_merged_mod chunk with the new_mods chunk
                #         new_lines = new_mod_chunk
                #         break
                #     elif user_choice == '3':
                #         # Merge the chunks by appending non-duplicate lines from new_mods to final_merged_mod
                #         new_lines = [line for line in new_mod_chunk if line not in final_merged_mod_chunk]
                #         break
                #     elif user_choice == '4':
                #         # Return a special value to indicate the user chose to quit
                #         print("Quiting...")
                #         return 'quit'
                #     else:
                #         print("Invalid choice. Please choose again.")

                # # Confirm the user's choice
                # # FIXME: Doesn't loop back to display_diff if user chooses '2' or '3'
                # if confirm_changes and user_choice in {'2', '3'}:
                #     confirm = confirm_choice(final_merged_mod_chunk, new_lines)
                #     if confirm == '1':
                #         with open(final_merged_mod_file, 'a') as final_merged_mod_append:
                #             temp_merged_mod.writelines(new_lines)
                #         break
                #     elif confirm == '2':
                #         continue
                #     elif confirm == '3':
                #         print("Quiting...")
                #         return 'quit'
                # else:
                #     with open(final_merged_mod_file, 'a') as final_merged_mod_append:
                #         temp_merged_mod.writelines(new_lines)
                #     break

                # Handle the user's choice for the diff
                tmp_merged_mod_lines = choice_handler(diff, formatted_final_merged_mod_chunk, formatted_new_mod_chunk, confirm_changes)
                if tmp_merged_mod_lines == 'quit':
                    return 'quit'

                # Write the new lines to the temporary file
                temp_merged_mod.writelines(tmp_merged_mod_lines)

                pbar.update(len(''.join(new_mod_chunk)))
            # if EOF update the progress bar to 100%
            pbar.update(new_mod_size - pbar.n)

    # Move the temporary file to the final_merged_mod_file
    shutil.move(temp_merged_mod_file, final_merged_mod_file)

    # Delete the temporary file
    os.remove(temp_merged_mod_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Processing time: {elapsed_time:.2f} seconds")
    print()
    return None

def merge_directories(new_mods_dir, final_merged_mod_dir, verbose=False, confirm_changes=True):
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
            result = merge_directories(new_mods_item, final_merged_mod_item, verbose, confirm_changes)
            if result == 'quit':
                return 'quit'
        else:
            # If the item is a file, handle conflicts
            if os.path.exists(final_merged_mod_item):
                result = merge_files(new_mods_item, final_merged_mod_item, verbose, confirm_changes)
                if result == 'quit':
                    return 'quit'
            else:
                shutil.copy2(new_mods_item, final_merged_mod_item)
    return None

def main():
    """Main function to merge mod directories."""
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Merge mod directories.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--confirm', action='store_true', help='Disable user confirmation')
    args = parser.parse_args()

    print(f"Verbose: {args.verbose}")
    print(f"Confirm: {args.confirm}")

    # Define the new_mods and final_merged_mod directories
    new_mods_base_dir = r'..\unpacked'
    final_merged_mod_base_dir = r'..\unpacked\~merged_mods_v1-0_P'

    # Iterate through all directories in the new_mods base directory
    for dir_name in os.listdir(new_mods_base_dir):
        new_mods_dir = os.path.join(new_mods_base_dir, dir_name)
        if os.path.isdir(new_mods_dir) and not new_mods_dir == final_merged_mod_base_dir:
            result = merge_directories(new_mods_dir, final_merged_mod_base_dir, args.verbose, args.confirm)
            if result == 'quit':
                print('Merge aborted.')
                return

    print('Merge complete.')

if __name__ == '__main__':
    main()

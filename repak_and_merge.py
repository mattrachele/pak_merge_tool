#!/usr/bin/env python3

# Version 0.1.0

"""Use repak.exe to unpack mods and then call merge_tool.py to merge the mods."""

# Usage: python repak_and_merge.py --verbose --confirm
# Example: clear;python .\repak_and_merge.py --new_mods_dir="..\unpacked" --final_merged_mod_dir="..\~merged_mods_v1-0_P"

# TODO: Add handling for utoc and ucas files

import os

# import shutil
import argparse
import subprocess

# import json
# import re
# import time
import logging

from merge_tool import merge_tool

# from colorama import init, Fore

# Initialize colorama
# init(autoreset=True)

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
            logger.info(f"{command} is not available.")
    except FileNotFoundError:
        logger.info(
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
        logger.info(
            "new_mods_dir and final_merged_mod_dir are required as cmd ln args."
        )
        return False

    # Validate the requirements
    # valid_requirements = validate_requirements()

    # @echo off
    # setlocal EnableDelayedExpansion

    # set "aes_key=0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386"
    # set "pak_directory=."
    # set "output_directory=unpacked"

    # if not exist "%output_directory%" (
    #     mkdir "%output_directory%"
    # )

    # for %%f in (%pak_directory%\*.pak) do (
    #     set "pak_name=%%~nf"
    #     set "current_output_directory=%output_directory%\!pak_name!"

    #     if not exist "!current_output_directory!" (
    #         mkdir "!current_output_directory!"
    #     )

    #     echo Unpacking %%f to !current_output_directory!
    #     repak --aes-key %aes_key% unpack "%%f" --output "!current_output_directory!"

    #     if !errorlevel! neq 0 (
    #         echo Error unpacking %%f
    #         pause
    #         exit /b !errorlevel!
    #     )

    #     echo Done unpacking %%f
    # )

    # endlocal

    # TODO: Add direct support to call repak to handle the pak files
    # TODO: Unpack the pak files if not unpacked yet or if there are new mods or updated mods
    aes_key = "0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386"

    # Merge the mods - call merge_tool.py once per mod
    new_mods_dir = args.new_mods_dir
    final_merged_mod_dir = args.final_merged_mod_dir

    logger.info(f"Final Merged Mod Directory: {final_merged_mod_dir}")

    new_mods_dir_list = os.listdir(new_mods_dir)
    sorted_new_mods_dir_list = sorted(new_mods_dir_list)

    # TODO: Add resume functionality
    for new_mod_dir in sorted_new_mods_dir_list:
        new_mod_dir_path = os.path.join(new_mods_dir, new_mod_dir)
        if not os.path.isdir(new_mod_dir_path):
            continue

        logger.info(f"Processing mod: {new_mod_dir}")
        logger.info(f"New Mod Directory: {new_mod_dir_path}")

        result = merge_tool(
            new_mods_dir=new_mod_dir_path,
            final_merged_mod_dir=final_merged_mod_dir,
            verbose=args.verbose,
            confirm=args.confirm,
        )

        # TODO: Add more return code handling
        if not result:
            return False

    return True


if __name__ == "__main__":
    main()

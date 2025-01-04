#!/usr/bin/env python3

# Version 0.1.0

"""Use repak.exe to unpack mods and then call merge_tool.py to merge the mods."""
# NOTE: repak.exe only unpaks the .pak data files, which contain some config files
#   and scripts but not the actual game assets. Use FModel to extract the game assets.

# TODO: Add shortcuts - maybe in a separate script or as powershell alias of somekind
# Usage: python repak_and_merge.py --verbose --confirm --repak_path="repak.exe" --unpak --new_mods_dir=<dir> --final_merged_mod_dir=<dir>
# Only Unpak New Mods Example:
#   clear;python pak_merge_tool\scripts\repak_and_merge.py --unpak_only --repak_path="repak.exe" --new_mods_dir="." --final_merged_mod_dir="unpacked"
# Merge New Mods Example:
#   clear;python pak_merge_tool\scripts\repak_and_merge.py --new_mods_dir="unpacked" --final_merged_mod_dir="~merged_mods_v2-0_P"
# Only Unpak Game Files Example:
#   clear;python pak_merge_tool\scripts\repak_and_merge.py --unpak_only --repak_path="repak.exe" --new_mods_dir="C:\Program Files (x86)\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl\Stalker2\Content\Paks" --final_merged_mod_dir="unpacked_game_paks"
# Merge Check Against Base Game Files Example:
#   clear;python pak_merge_tool\scripts\repak_and_merge.py --org_comp --new_mods_dir="unpacked_game_paks" --final_merged_mod_dir="~merged_mods_v2-0_P"

import os
import argparse
import subprocess
import json
import logging
import re

from datetime import datetime
from merge_tool import merge_tool

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


def sanitize_mod_name(pak_file_name) -> dict:
    """Sanitize the mod name to remove special characters and version numbers."""
    # Remove .pak, split on _, remove zz's, remove other special characters, and lowercase
    lower_no_zzs_pak_file_name = re.sub(r"^[zZ]+_", "", pak_file_name.lower())
    no_spec_chars_pak_file_name = re.sub(r"[\(\)~]", "", lower_no_zzs_pak_file_name)
    no_ext_end_pak_file_name = re.sub(r"\.pak$", "", no_spec_chars_pak_file_name)
    no_p_end_pak_file_name = re.sub(r"_p$", "", no_ext_end_pak_file_name)
    pak_file_name_parts = no_p_end_pak_file_name.split("_")

    version_pattern = re.compile(r'v\d+[\.\-]\d+(\.\d+)?')
    new_pak_file_version = ""
    for part in pak_file_name_parts:
        if version_pattern.match(part):
            new_pak_file_version = part
            pak_file_name_parts.remove(part) # Remove the version part from the list
            break

    pak_file_clean_name = "_".join(pak_file_name_parts)

    return {
        "clean_name": pak_file_clean_name,
        "version": new_pak_file_version,
    }


def update_mod_version(history, pak_file_clean_name, new_pak_file_version) -> dict:
    """Update the version of a mod in the history file."""
    pak_file_history = history.get(pak_file_clean_name) or {}
    version_history = pak_file_history.get("version") or []
    last_version = version_history[-1] if version_history else None

    if not new_pak_file_version:
        new_pak_file_version = "1"
        if pak_file_history and last_version:
            new_pak_file_version = str(int(last_version) + 1)

    if last_version and new_pak_file_version == last_version:
        logger.info(f"Version number matches last version for {pak_file_clean_name}: {new_pak_file_version}")
        return pak_file_history

    version_history.append(new_pak_file_version)
    pak_file_history["version"] = version_history
    return pak_file_history


def unpack_files(repak_path, pak_dir, extract_dir, resume) -> bool:
    """Unpack the .pak, .ucas, and .utoc files in the directory."""
    aes_key = "0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386"

    # Json config path: ..\configs\config.json
    json_config = os.path.join(
        os.path.dirname(__file__), "..", "configs", "config.json"
    )
    config = (
        json.load(open(json_config, "r", encoding="utf-8"))
        if os.path.exists(json_config)
        else {}
    )

    # Check if the repak_path is valid and save to config file if new
    if not repak_path:
        logger.info("repak path not provided. Checking config file.")
        # Check if there is a valid repak path in the config file
        if not config.get("repak_path"):
            logger.error("repak path not found in config file.")
            return False

        if (
            not os.path.exists(config["repak_path"])
            or "repak.exe" not in config["repak_path"]
        ):
            logger.error(f"Invalid repak path in config file: {config['repak_path']}")
            return False

        repak_path = config["repak_path"]
    else:
        # Check if the repak_path is valid
        if not os.path.exists(repak_path) or "repak.exe" not in repak_path:
            logger.error(f"Invalid repak path provided: {repak_path}")
            return False

        # Save the repak_path to the config file
        config["repak_path"] = repak_path
        with open(json_config, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    # List all .pak files in the directory
    pak_files = [f for f in os.listdir(pak_dir) if f.endswith(".pak")]
    history = load_history()

    for pak_file in pak_files:
        pak_file_path = os.path.join(pak_dir, pak_file)
        extract_path = os.path.join(extract_dir, pak_file)

        # Pak file names can change between version - need to save in history with a unique identifier and regex match
        pak_file_name_parts = sanitize_mod_name(pak_file)
        pak_file_clean_name = pak_file_name_parts.get("clean_name")
        new_pak_file_version = pak_file_name_parts.get("version")
        pak_file_history = history.get(pak_file_clean_name) or {}
        version_history = pak_file_history.get("version") or []
        last_version = version_history[-1] if version_history else None

        if resume and pak_file_history and last_version and new_pak_file_version == last_version and pak_file_history.get("unpacked"):
            logger.info(f"Version number matches last version for {pak_file}: {new_pak_file_version}")
            logger.info(f"Skipping {pak_file} as it has already been unpacked.")
            continue

        history[pak_file_clean_name] = update_mod_version(history, pak_file_clean_name, new_pak_file_version)

        # Save the last modified date of the pak file to the history file
        timestamp = os.path.getmtime(pak_file_path)
        last_modified = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        history[pak_file_clean_name]["last_modified"] = last_modified
        history[pak_file_clean_name]["unpacked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Run repak to unpack the files
        result = subprocess.run(
            [
                repak_path,
                "--aes-key",
                aes_key,
                "unpack",
                pak_file_path,
                "--output",
                extract_path,
            ],
            shell=True,
        )
        if result.returncode != 0:
            logger.error(f"Error unpacking {pak_file_path}")
            save_history(history)
            return False

    save_history(history)
    return True


def save_history(history) -> bool:
    """Save the history to a file."""
    # History config path: ..\configs\history.json
    history_config = os.path.join(
        os.path.dirname(__file__), "..", "configs", "history.json"
    )
    with open(history_config, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    return True


def load_history() -> dict:
    """Load the history from a file."""
    # History config path: ..\configs\history.json
    history_config = os.path.join(
        os.path.dirname(__file__), "..", "configs", "history.json"
    )
    history = (
        json.load(open(history_config, "r", encoding="utf-8"))
        if os.path.exists(history_config)
        else {}
    )

    return history


def merge_mods(
    sorted_new_mods_dir_list, new_mods_dir, final_merged_mod_dir, verbose, confirm, org_comp, resume
) -> bool:
    """Merge the mods in the new_mods_dir into the final_merged_mod_dir."""
    # Load the history file
    history = load_history()
    for new_mod_dir in sorted_new_mods_dir_list:
        new_mod_dir_path = os.path.join(new_mods_dir, new_mod_dir)
        if not os.path.isdir(new_mod_dir_path):
            continue

        # Skip mods that have already been merged
        mod_history = history.get(new_mod_dir)
        merged_date = mod_history.get("merged")
        last_modified_date = mod_history.get("last_modified")
        if resume and merged_date and last_modified_date and merged_date >= last_modified_date:
            logger.info(f"Resume set and current mod version in history | Skipping mod: {new_mod_dir}")
            continue

        logger.info(f"Processing mod: {new_mod_dir}")
        logger.info(f"New Mod Directory: {new_mod_dir_path}")

        # TODO: Pass org_comp flag to merge_tool.py to enable comparison to base game files - build out support in merge_tool.py
        # This will help prevent overwriting updates from the base game and/or crashing the game
        result = merge_tool(
            new_mods_dir=new_mod_dir_path,
            final_merged_mod_dir=final_merged_mod_dir,
            verbose=verbose,
            confirm=confirm,
            # org_comp=org_comp,
        )

        if not result:
            save_history(history)
            return False

        # Add the mod to the history file as merged with the current date
        pak_file_name_parts = sanitize_mod_name(new_mod_dir)
        pak_file_clean_name = pak_file_name_parts.get("clean_name")
        new_pak_file_version = pak_file_name_parts.get("version")

        history[pak_file_clean_name] = update_mod_version(history, pak_file_clean_name, new_pak_file_version)
        history[pak_file_clean_name]["merged"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_history(history)
    return True


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
        "--repak_path", help="The path to the repak executable", required=False
    )
    parser.add_argument(
        "--unpak", action="store_true", help="Unpack the mods", required=False
    )
    parser.add_argument(
        "--unpak_only", action="store_true", help="Only unpack the mods", required=False
    )
    parser.add_argument(
        "--org_comp",
        action="store_true",
        help="Compare the original base game files",
        required=False,
    )
    parser.add_argument(
        "--new_mods_dir", help="The directory containing the new mods", required=True
    )
    parser.add_argument(
        "--resume", help="Resume merging the mods", required=False, default=False
    )
    parser.add_argument(
        "--final_merged_mod_dir",
        help="The directory containing the final merged mods",
        required=True,
    )
    args = parser.parse_args()

    # Log boolean cmd ln args
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Confirm: {args.confirm}")
    logger.info(f"Unpak: {args.unpak or args.unpak_only}")
    logger.info(f"Org Comp: {args.org_comp}")
    logger.info(f"Resume: {args.resume}")

    # TODO: Add option to save default directories to the config file

    # Merge the mods - call merge_tool.py once per mod
    new_mods_dir = args.new_mods_dir
    final_merged_mod_dir = args.final_merged_mod_dir

    logger.info(f"Final Merged Mod Directory: {final_merged_mod_dir}")

    new_mods_dir_list = os.listdir(new_mods_dir)
    sorted_new_mods_dir_list = sorted(new_mods_dir_list)

    # Unpack new mods or base game paks if requested
    if args.unpak or args.unpak_only:
        if not args.repak_path:
            logger.error("Set to unpack files but no repak path provided.")
            return False

        repak_path = args.repak_path
        pak_dir = new_mods_dir
        extract_dir = final_merged_mod_dir
        unpack_files(repak_path, pak_dir, extract_dir, args.resume)

        if args.unpak_only:
            return True

    # Merge the new mods using merge_tool.py
    merge_mods(
        sorted_new_mods_dir_list,
        new_mods_dir,
        final_merged_mod_dir,
        args.verbose,
        args.confirm,
        args.org_comp,
        args.resume,
    )

    return True


if __name__ == "__main__":
    main()

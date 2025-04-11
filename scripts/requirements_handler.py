#!/usr/bin/env python3

# Version 0.1.0

"""This module contains functions to check if the required tools are available."""

import logging
import subprocess
import json
import os

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


def load_config(config_name) -> dict:
    """Load the config file."""
    # Json config path: ..\configs\config.json
    json_config = os.path.join(os.path.dirname(__file__), "..", "configs", config_name)
    config = {}
    with open(json_config, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def save_config(config) -> None:
    """Save the config file."""
    json_config = os.path.join(
        os.path.dirname(__file__), "..", "configs", "config.json"
    )
    with open(json_config, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

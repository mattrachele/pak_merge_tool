#!/usr/bin/env python3

"""Functional tests for pak_merge_tool -> merge_tool.py"""

import io
import os
import json
import unittest
from unittest.mock import patch
import pytest
import zipfile


class TestMergeTool(unittest.TestCase):
    """Functional tests for pak_merge_tool -> merge_tool.py"""

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.test_data_dir = os.path.join(self.test_dir, "test_data")
        self.test_output_dir = os.path.join(self.test_dir, "test_output")
        self.test_output_zip = os.path.join(self.test_output_dir, "output.zip")
        self.test_output_json = os.path.join(self.test_output_dir, "output.json")

        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)

    def tearDown(self):
        if os.path.exists(self.test_output_dir):
            for file in os.listdir(self.test_output_dir):
                os.remove(os.path.join(self.test_output_dir, file))
            os.rmdir(self.test_output_dir)

    def test_merge_tool_zip(self):
        """Test merge_tool with zip files"""

        # Test with two zip files
        with patch(
            "sys.argv",
            [
                "merge_tool.py",
                os.path.join(self.test_data_dir, "test1.zip"),
                os.path.join(self.test_data_dir, "test2.zip"),
                self.test_output_zip,
            ],
        ):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                import merge_tool

                self.assertEqual(mock_stdout.getvalue(), "Merged 2 files\n")

        # Check the output zip file
        with zipfile.ZipFile(self.test_output_zip, "r") as zip_file:
            self.assertEqual(len(zip_file.namelist()), 2)
            with zip_file.open("test1.txt") as file:
                self.assertEqual(file.read(), b"Test 1\n")
            with zip_file.open("test2.txt") as file:
                self.assertEqual(file.read(), b"Test 2\n")

    def test_merge_tool_json(self):
        """Test merge_tool with json files"""

        # Test with two json files
        with patch(
            "sys.argv",
            [
                "merge_tool.py",
                os.path.join(self.test_data_dir, "test1.json"),
                os.path.join(self.test_data_dir, "test2.json"),
                self.test_output_json,
            ],
        ):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                import merge_tool

                self.assertEqual(mock_stdout.getvalue(), "Merged 2 files\n")

        # Check the output json file
        with open(self.test_output_json, "r") as file:
            data = json.load(file)

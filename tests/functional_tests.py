#!/usr/bin/env python3

"""Functional tests for pak_merge_tool -> merge_tool.py"""

# Usage: clear;pytest .\tests\functional_tests.py

import os
import unittest
from unittest.mock import patch, mock_open, Mock
import sys
import argparse

# Add the directory containing merge_tool.py to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestMergeTool(unittest.TestCase):
    """Functional tests for pak_merge_tool -> merge_tool.py"""

    # Test version_check(command) -> bool
    @patch("subprocess.run")
    def test_version_check(self, mock_subprocess_run):
        """Test version_check(command) -> bool"""
        from scripts.merge_tool import version_check

        # Return an object with a returncode of 0
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = version_check("code")
        assert result is True

    # Test validate_requirements() -> dict
    @patch("merge_tool.version_check")
    def test_validate_requirements(self, mock_version_check):
        """Test validate_requirements() -> dict"""
        from scripts.merge_tool import validate_requirements

        mock_version_check.return_value = True

        result = validate_requirements()
        assert result["code"] is True
        assert result["less"] is True

    # Test strip_whitespace(lines) -> list
    def test_strip_whitespace(self):
        """Test strip_whitespace(lines) -> list"""
        from scripts.merge_tool import strip_whitespace

        lines = ["  test  ", "  test2  "]
        result = strip_whitespace(lines)
        assert result == ["test", "test2"]

    # Test filter_updated_lines(original_lines, new_lines) -> list
    def test_filter_updated_lines(self):
        """Test filter_updated_lines(original_lines, new_lines) -> list"""
        from scripts.merge_tool import filter_updated_lines

        original_lines = ["test", "test2"]
        new_lines = ["test", "test3"]
        result = filter_updated_lines(original_lines, new_lines)
        assert result == ["test3"]

    # Test confirm_choice(original_lines, new_lines) -> str
    @patch("merge_tool.filter_updated_lines")
    @patch("merge_tool.input")
    def test_confirm_choice(self, mock_input, mock_filter_updated_lines):
        """Test confirm_choice(original_lines, new_lines) -> str"""
        from scripts.merge_tool import confirm_choice

        mock_input.return_value = "1"
        mock_filter_updated_lines.return_value = ["test3"]

        original_lines = ["test", "test2"]
        new_lines = ["test", "test3"]
        result = confirm_choice(original_lines, new_lines)
        assert result == "1"

    # Test view_text_with_pydoc(text) -> None
    @patch("pydoc.pager")
    def test_view_text_with_pydoc(self, mock_pager):
        """Test view_text_with_pydoc(text) -> None"""
        from scripts.merge_tool import view_text_with_pydoc

        text = "test"
        view_text_with_pydoc(text)
        mock_pager.assert_called_once()

    # Test view_text_with_less(text) -> None
    @patch("subprocess.Popen")
    @patch("subprocess.Popen.communicate")
    def test_view_text_with_less(self, mock_communicate, mock_popen):
        """Test view_text_with_less(text) -> None"""
        from scripts.merge_tool import view_text_with_less

        text = ["test"]
        view_text_with_less(text)
        mock_popen.assert_called_once()

    # Test open_files_in_vscode_compare(file1, file2) -> None
    @patch("subprocess.run")
    def test_open_files_in_vscode_compare(self, mock_subprocess_run):
        """Test open_files_in_vscode_compare(file1, file2) -> None"""
        from scripts.merge_tool import open_files_in_vscode_compare

        file1 = "test1"
        file2 = "test2"
        open_files_in_vscode_compare(file1, file2)
        mock_subprocess_run.assert_called_once()

    # Test def disp_diff_re_print(input_vars) -> dict:
    def test_disp_diff_re_print(self):
        """Test disp_diff_re_print(input_vars) -> dict"""
        from scripts.merge_tool import disp_diff_re_print

        input_vars = {
            "disp_diff_chunk": ["@@ -1,2 +1,2 @@\n", "-test3\n", "+test2\n", "test4\n"],
        }
        result = disp_diff_re_print(input_vars)
        assert result["status"] == "continue"

    # Test def disp_chunk_skip_no_changes(input_vars) -> dict
    def test_disp_chunk_skip_no_changes(self):
        """Test disp_chunk_skip_no_changes(input_vars) -> dict"""
        from scripts.merge_tool import disp_chunk_skip_no_changes

        input_vars = {
            "disp_final_merged_mod_chunk": ["test1", "test2"],
        }
        result = disp_chunk_skip_no_changes(input_vars)
        assert result["status"] == "pass_through"
        assert result["processed_lines"] == ["test1", "test2"]

    # Test disp_chunk_overwrite_new_changes(input_vars) -> dict
    def test_disp_chunk_overwrite_new_changes(self):
        """Test disp_chunk_overwrite_new_changes(input_vars) -> dict"""
        from scripts.merge_tool import disp_chunk_overwrite_new_changes

        input_vars = {
            "disp_new_mod_chunk": ["test3", "test4"],
        }
        result = disp_chunk_overwrite_new_changes(input_vars)
        assert result["status"] == "pass_through"
        assert result["processed_lines"] == ["test3", "test4"]

    # Test def disp_chunk_save_merged_diff(input_vars) -> dict
    def test_disp_chunk_save_merged_diff(self):
        """Test disp_chunk_save_merged_diff(input_vars) -> dict"""
        from scripts.merge_tool import disp_chunk_save_merged_diff

        input_vars = {
            "disp_diff_chunk": [
                "@@ -1,2 +1,2 @@\n",
                "-test3\n",
                "+test2\n",
                " test4\n",
            ],
        }
        result = disp_chunk_save_merged_diff(input_vars)
        assert result["status"] == "pass_through"
        assert result["processed_lines"] == ["test3\n", "test2\n", "test4\n"]

    # Test def whole_chunk_skip_no_changes(input_vars) -> dict
    def test_whole_chunk_skip_no_changes(self):
        """Test whole_chunk_skip_no_changes(input_vars) -> dict"""
        from scripts.merge_tool import whole_chunk_skip_no_changes

        input_vars = {
            "f_final_merged_mod_chunk": ["test1", "test2"],
        }
        result = whole_chunk_skip_no_changes(input_vars)
        assert result["status"] == "return_continue"
        assert result["processed_lines"] == ["test1", "test2"]

    # Test def whole_chunk_overwrite_new_changes(input_vars) -> dict
    def test_whole_chunk_overwrite_new_changes(self):
        """Test whole_chunk_overwrite_new_changes(input_vars) -> dict"""
        from scripts.merge_tool import whole_chunk_overwrite_new_changes

        input_vars = {
            "f_new_mod_chunk": ["test3", "test4"],
        }
        result = whole_chunk_overwrite_new_changes(input_vars)
        assert result["status"] == "return_continue"
        assert result["processed_lines"] == ["test3", "test4"]

    # Test def whole_chunk_save_merged_diff(input_vars) -> dict
    def test_whole_chunk_save_merged_diff(self):
        """Test whole_chunk_save_merged_diff(input_vars) -> dict"""
        from scripts.merge_tool import whole_chunk_save_merged_diff

        input_vars = {
            "f_final_merged_mod_chunk": ["test3", "test4"],
            "display_chunk_array": [[1, 2, 1, 2, 1, 4]],
            "diff_lines_list": [
                "@@ -1,2 +1,2 @@\n",
                "-test3\n",
                "+test2\n",
                " test4\n",
            ],
        }
        result = whole_chunk_save_merged_diff(input_vars)
        assert result["status"] == "return_continue"
        assert result["processed_lines"] == ["test3\n", "test2\n", "test4\n"]

    # Test def whole_chunk_view_diff_less(input_vars) -> dict
    @patch("merge_tool.view_text_with_less")
    def test_whole_chunk_view_diff_less(self, mock_view_text_with_less):
        """Test whole_chunk_view_diff_less(input_vars) -> dict"""
        from scripts.merge_tool import whole_chunk_view_diff_less

        input_vars = {
            "diff_lines_list": ["test1", "test2"],
        }
        result = whole_chunk_view_diff_less(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_less.assert_called_once()

    # Test def whole_file_view_temp_merged_mod_less(input_vars) -> dict
    @patch("builtins.open", new_callable=mock_open)
    @patch("merge_tool.view_text_with_less")
    def test_whole_file_view_temp_merged_mod_less(
        self, mock_view_text_with_less, mock_open_var
    ):
        """Test whole_file_view_temp_merged_mod_less(input_vars) -> dict"""
        from scripts.merge_tool import whole_file_view_temp_merged_mod_less

        input_vars = {
            "temp_merged_mod_file": "test1",
        }
        result = whole_file_view_temp_merged_mod_less(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_less.assert_called_once()

    # Test def whole_chunk_view_diff_pydoc(input_vars) -> dict
    @patch("merge_tool.view_text_with_pydoc")
    def test_whole_chunk_view_diff_pydoc(self, mock_view_text_with_pydoc):
        """Test whole_chunk_view_diff_pydoc(input_vars) -> dict"""
        from scripts.merge_tool import whole_chunk_view_diff_pydoc

        input_vars = {
            "diff_lines_list": ["test1", "test2"],
        }
        result = whole_chunk_view_diff_pydoc(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_pydoc.assert_called_once()

    # Test def whole_file_view_temp_merged_mod_pydoc(input_vars) -> dict
    @patch("builtins.open", new_callable=mock_open)
    @patch("merge_tool.view_text_with_pydoc")
    def test_whole_file_view_temp_merged_mod_pydoc(
        self, mock_view_text_with_pydoc, mock_open_var
    ):
        """Test whole_file_view_temp_merged_mod_pydoc(input_vars) -> dict"""
        from scripts.merge_tool import whole_file_view_temp_merged_mod_pydoc

        input_vars = {
            "temp_merged_mod_file": "test1",
        }
        result = whole_file_view_temp_merged_mod_pydoc(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_pydoc.assert_called_once()

    # Test def whole_file_open_diff_vs_code(input_vars) -> dict
    @patch("merge_tool.open_files_in_vscode_compare")
    def test_whole_file_open_diff_vs_code(self, mock_open_files_in_vscode_compare):
        """Test whole_file_open_diff_vs_code(input_vars) -> dict"""
        from scripts.merge_tool import whole_file_open_diff_vs_code

        input_vars = {
            "new_mods_file": "test1",
            "final_merged_mod_file": "test2",
        }
        result = whole_file_open_diff_vs_code(input_vars)
        assert result["status"] == "continue"
        mock_open_files_in_vscode_compare.assert_called_once()

    # Test def whole_file_open_temp_merged_mod_vs_code(input_vars) -> dict
    @patch("merge_tool.open_files_in_vscode_compare")
    def test_whole_file_open_temp_merged_mod_vs_code(
        self, mock_open_files_in_vscode_compare
    ):
        """Test whole_file_open_temp_merged_mod_vs_code(input_vars) -> dict"""
        from scripts.merge_tool import whole_file_open_temp_merged_mod_vs_code

        input_vars = {
            "final_merged_mod_file": "test2",
        }
        result = whole_file_open_temp_merged_mod_vs_code(input_vars)
        assert result["status"] == "continue"
        mock_open_files_in_vscode_compare.assert_called_once()

    # Test def quit_save(input_vars) -> dict
    def test_quit_save(self):
        """Test quit_save(input_vars) -> dict"""
        from scripts.merge_tool import quit_save

        input_vars = {
            "tmp_merged_mod_lines": ["test1", "test2"],
        }
        result = quit_save(input_vars)
        assert result["status"] == "quit-save"

    # Test def quit_out(input_vars) -> dict
    def test_quit_out(self):
        """Test quit_out(input_vars) -> dict"""
        from scripts.merge_tool import quit_out

        input_vars = {}
        result = quit_out(input_vars)
        assert result["status"] == "quit"

    # Test load_choice_functions(valid_requirements) -> dict:
    def test_load_choice_functions(self):
        """Test load_choice_functions(valid_requirements) -> dict"""
        from scripts.merge_tool import load_choice_functions

        valid_requirements = {"code": True, "less": True}
        result = load_choice_functions(valid_requirements)

        assert result["1"]["disp_diff_re_print"] == "Re-print the Display Diff"
        assert (
            result["2"]["disp_chunk_skip_no_changes"]
            == "Display Chunk: Skip - Make No Changes"
        )
        assert (
            result["3"]["disp_chunk_overwrite_new_changes"]
            == "Display Chunk: Overwrite with New Changes"
        )
        assert (
            result["4"]["disp_chunk_save_merged_diff"] == "Display Chunk: Merge Changes"
        )
        assert (
            result["5"]["whole_chunk_skip_no_changes"]
            == "Whole Chunk: Skip - Make No Changes"
        )
        assert (
            result["6"]["whole_chunk_overwrite_new_changes"]
            == "Whole Chunk: Overwrite with New Changes"
        )
        assert (
            result["7"]["whole_chunk_save_merged_diff"] == "Whole Chunk: Merge Changes"
        )
        assert (
            result["8"]["whole_chunk_view_diff_less"] == "Whole Chunk: View Diff in CLI"
        )
        assert (
            result["9"]["whole_file_view_temp_merged_mod_less"]
            == "Whole File: View Temp Merged Mod in CLI"
        )
        assert (
            result["10"]["whole_file_open_diff_vs_code"]
            == "Whole File: Open Diff in VS Code"
        )
        assert (
            result["11"]["whole_file_open_temp_merged_mod_vs_code"]
            == "Whole File: Open Temp Merged Mod in VS Code"
        )

    # Test choice_handler(
    #     new_mods_file,
    #     final_merged_mod_file,
    #     diff_lines,
    #     f_final_merged_mod_chunk,
    #     f_new_mod_chunk,
    #     valid_requirements,
    #     confirm_user_choice=False,
    # ) -> dict
    @patch("merge_tool.input")
    @patch("merge_tool.confirm_choice")
    @patch("merge_tool.view_text_with_less")
    @patch("merge_tool.view_text_with_pydoc")
    @patch("merge_tool.open_files_in_vscode_compare")
    @patch("merge_tool.disp_chunk_skip_no_changes")
    @patch("merge_tool.disp_chunk_overwrite_new_changes")
    @patch("merge_tool.disp_chunk_save_merged_diff")
    @patch("merge_tool.whole_chunk_skip_no_changes")
    @patch("merge_tool.whole_chunk_overwrite_new_changes")
    @patch("merge_tool.whole_chunk_save_merged_diff")
    @patch("merge_tool.whole_chunk_view_diff_less")
    @patch("merge_tool.whole_file_view_temp_merged_mod_less")
    @patch("merge_tool.whole_chunk_view_diff_pydoc")
    @patch("merge_tool.whole_file_view_temp_merged_mod_pydoc")
    @patch("merge_tool.whole_file_open_diff_vs_code")
    @patch("merge_tool.whole_file_open_temp_merged_mod_vs_code")
    @patch("merge_tool.quit_save")
    @patch("merge_tool.quit_out")
    def test_choice_handler(
        self,
        mock_quit_out,
        mock_quit_save,
        mock_whole_file_open_temp_merged_mod_vs_code,
        mock_whole_file_open_diff_vs_code,
        mock_whole_file_view_temp_merged_mod_pydoc,
        mock_whole_chunk_view_diff_pydoc,
        mock_whole_file_view_temp_merged_mod_less,
        mock_whole_chunk_view_diff_less,
        mock_whole_chunk_save_merged_diff,
        mock_whole_chunk_overwrite_new_changes,
        mock_whole_chunk_skip_no_changes,
        mock_disp_chunk_save_merged_diff,
        mock_disp_chunk_overwrite_new_changes,
        mock_disp_chunk_skip_no_changes,
        mock_open_files_in_vscode_compare,
        mock_view_text_with_pydoc,
        mock_view_text_with_less,
        mock_confirm_choice,
        mock_input,
    ):
        """Test choice_handler() -> dict"""
        from scripts.merge_tool import choice_handler

        new_mods_file = "test1"
        final_merged_mod_file = "test2"
        diff_lines = ["@@ -1,2 +1,2 @@\n", "-test3\n", "+test2\n", "test4\n"]
        f_final_merged_mod_chunk = ["test3", "test4"]
        f_new_mod_chunk = ["test2", "test4"]
        valid_requirements = {"code": True, "less": True}
        temp_merged_mod_file = "test3"
        last_display_diff = ""
        last_user_choice = "2"

        mock_input.return_value = "2"
        mock_confirm_choice.return_value = "2"
        mock_disp_chunk_skip_no_changes.return_value = {
            "status": "pass_through",
            "processed_lines": ["test3", "test4"],
        }

        result = choice_handler(
            new_mods_file,
            final_merged_mod_file,
            diff_lines,
            f_final_merged_mod_chunk,
            f_new_mod_chunk,
            valid_requirements,
            temp_merged_mod_file,
            last_display_diff,
            last_user_choice,
        )
        assert result["status"] == "continue"
        assert result["processed_lines"] == ["test3", "test4"]

    # Test reload_temp_merged_mod_file(tmp_merged_mod_file) -> int
    def test_reload_temp_merged_mod_file(self):
        """Test reload_temp_merged_mod_file(tmp_merged_mod_file) -> int"""
        from scripts.merge_tool import reload_temp_merged_mod_file

        tmp_merged_mod_file = "test"
        result = reload_temp_merged_mod_file(tmp_merged_mod_file)
        assert result == 0

    # Test def duplicate_line_check(temp_merged_mod_file, new_tmp_merged_mod_lines, perf_chunk, final_perf_chunk_sizes) -> list:
    @patch("builtins.open", new_callable=mock_open)
    def test_duplicate_line_check(self, mock_open_var):
        """Test duplicate_line_check(temp_merged_mod_file, new_tmp_merged_mod_lines, perf_chunk, final_perf_chunk_sizes) -> list"""
        from scripts.merge_tool import duplicate_line_check

        temp_merged_mod_file = "test"
        new_tmp_merged_mod_lines = ["test1", "test2"]
        perf_chunk = 1  # Change to 2 for further testing
        final_perf_chunk_sizes = [1, 2]

        result = duplicate_line_check(
            temp_merged_mod_file,
            new_tmp_merged_mod_lines,
            perf_chunk,
            final_perf_chunk_sizes,
        )
        assert result == ["test1", "test2"]

    # Test merge_files(new_mods_file, final_merged_mod_file, valid_requirements) -> str
    @patch("os.path.getsize")
    @patch("merge_tool.reload_temp_merged_mod_file")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.loads")
    @patch("merge_tool.strip_whitespace")
    @patch("merge_tool.choice_handler")
    @patch("shutil.move")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_merge_files(
        self,
        mock_remove,
        mock_exists,
        mock_move,
        mock_choice_handler,
        mock_strip_whitespace,
        mock_json_loads,
        mock_builtin_open,
        mock_reload_temp_merged_mod_file,
        mock_getsize,
    ):
        """Test merge_files(new_mods_file, final_merged_mod_file) -> str"""
        from scripts.merge_tool import merge_files

        new_mods_file = "test1"
        final_merged_mod_file = "test2"
        valid_requirements = {"code": True, "less": True}

        mock_getsize.return_value = 0
        mock_reload_temp_merged_mod_file.return_value = 0
        mock_strip_whitespace.return_value = ["test"]
        mock_choice_handler.return_value = {
            "status": "continue",
            "processed_lines": ["test"],
        }
        mock_json_loads.return_value = {"test": "test"}
        mock_exists.return_value = True
        mock_move.return_value = None

        result = merge_files(new_mods_file, final_merged_mod_file, valid_requirements)
        assert result == "continue"

    # Test merge_directories(new_mods_dir, final_merged_mod_dir, valid_requirements) -> str
    @patch("os.path.join", side_effect=os.path.join)
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("shutil.copy2")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("merge_tool.merge_files")
    @patch("merge_tool.merge_directories")
    def test_merge_directories(
        self,
        mock_merge_directories,
        mock_merge_files,
        mock_exists,
        mock_makedirs,
        mock_copy2,
        mock_list_dir,
        mock_is_dir,
        mock_path_join,
    ):
        """Test merge_directories(new_mods_dir, final_merged_mod_dir) -> str"""
        from scripts.merge_tool import merge_directories

        new_mods_dir = "test1"
        final_merged_mod_dir = "test2"
        valid_requirements = {"code": True, "less": True}

        mock_copy2.return_value = None
        mock_exists.return_value = False
        mock_is_dir.return_value = True
        mock_list_dir.return_value = ["file1", "file2"]
        mock_makedirs.return_value = None
        mock_merge_files.return_value = "continue"
        mock_merge_directories.return_value = "continue"

        result = merge_directories(
            new_mods_dir, final_merged_mod_dir, valid_requirements
        )
        assert result == "continue"

    # Test main() -> bool
    @patch("merge_tool.merge_directories")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.join", side_effect=os.path.join)
    @patch("merge_tool.validate_requirements")
    def test_main(
        self,
        mock_validate_requirements,
        mock_path_join,
        mock_is_dir,
        mock_list_dir,
        mock_parse_args,
        mock_merge_directories,
    ):
        """Test main() -> bool"""
        from scripts.merge_tool import main

        mock_validate_requirements.return_value = {"code": True, "less": True}
        mock_parse_args.return_value = argparse.Namespace(
            new_mods_dir="test1",
            final_merged_mod_dir="test2",
            verbose=False,
            confirm=False,
        )
        mock_merge_directories.return_value = "quit"
        # mock_path_join.side_effect = lambda *args: original_os_path_join(*args)
        mock_list_dir.return_value = ["file1", "file2"]
        mock_is_dir.return_value = True

        result = main()
        assert result is False

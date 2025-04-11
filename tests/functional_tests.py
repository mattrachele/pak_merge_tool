#!/usr/bin/env python3

"""Functional tests for pak_merge_tool -> merge_tool.py"""

# Usage: clear;pytest .\tests\functional_tests.py

import os
import unittest
from unittest.mock import patch, mock_open, Mock, call
import sys
# import argparse
# import subprocess
# import json

# Add the directory containing merge_tool.py to the Python path
os_path_dirname = os.path.dirname(__file__)
joined_path = os.path.join(os_path_dirname, "..")
abs_path = os.path.abspath(joined_path)
sys.path.insert(0, abs_path)

scripts_path = os.path.join(abs_path, "scripts")
abs_scripts_path = os.path.abspath(scripts_path)
sys.path.insert(0, abs_scripts_path)


class TestChoiceHandler(unittest.TestCase):
    @patch("builtins.input")
    def test_get_user_choice(self, mock_input):
        """Test get_user_choice(choices) -> str"""
        from scripts.choice_handler import get_user_choice

        mock_input.return_value = "1"
        choices = {"1": "test", "2": "test2"}
        result = get_user_choice(choices)
        assert result == "1"

    @patch("scripts.choice_handler.get_user_choice")
    def test_confirm_choice(self, mock_get_user_choice):
        """Test confirm_choice(original_lines, new_lines) -> str"""
        from scripts.choice_handler import confirm_choice

        mock_get_user_choice.return_value = "1"
        original_lines = ["test", "test2"]
        new_lines = ["test", "test3"]
        result = confirm_choice(original_lines, new_lines)
        assert result == "1"

    @patch("pydoc.pager")
    def test_view_text_with_pydoc(self, mock_pager):
        """Test view_text_with_pydoc(text) -> None"""
        from scripts.choice_handler import view_text_with_pydoc

        text = ["test", "test2"]
        view_text_with_pydoc(text)
        mock_pager.assert_called_once()

    @patch("subprocess.Popen")
    @patch("subprocess.Popen.communicate")
    def test_view_text_with_less(self, mock_communicate, mock_popen):
        """Test view_text_with_less(text) -> None"""
        from scripts.choice_handler import view_text_with_less

        text = ["test", "test2"]
        view_text_with_less(text)
        mock_popen.assert_called_once()

    @patch("subprocess.run")
    def test_open_files_in_vscode_compare(self, mock_subprocess_run):
        """Test open_files_in_vscode_compare(file1, file2) -> None"""
        from scripts.choice_handler import open_files_in_vscode_compare

        file1 = "test1"
        file2 = "test2"
        open_files_in_vscode_compare(file1, file2)
        mock_subprocess_run.assert_called_once()

    def test_print_disp_diff(self):
        """Test print_disp_diff(input_vars) -> dict"""
        from scripts.choice_handler import print_disp_diff

        input_vars = {
            "disp_diff_chunk": ["test1", "test2"],
            "final_merged_mod_file": "test3",
            "new_mods_file": "test4",
        }
        result = print_disp_diff(input_vars)
        assert result["status"] == "continue"

    def test_disp_chunk_skip_no_changes(self):
        """Test disp_chunk_skip_no_changes(input_vars) -> dict"""
        from scripts.choice_handler import disp_chunk_skip_no_changes

        input_vars = {"disp_final_merged_mod_chunk": ["test1", "test2"]}
        result = disp_chunk_skip_no_changes(input_vars)
        assert result["status"] == "pass_through"

    def test_disp_chunk_overwrite_new_changes(self):
        """Test disp_chunk_overwrite_new_changes(input_vars) -> dict"""
        from scripts.choice_handler import disp_chunk_overwrite_new_changes

        input_vars = {"disp_new_mod_chunk": ["test3", "test4"]}
        result = disp_chunk_overwrite_new_changes(input_vars)
        assert result["status"] == "pass_through"

    def test_disp_chunk_save_merged_diff(self):
        """Test disp_chunk_save_merged_diff(input_vars) -> dict"""
        from scripts.choice_handler import disp_chunk_save_merged_diff

        input_vars = {"disp_diff_chunk": ["test1", "test2"]}
        result = disp_chunk_save_merged_diff(input_vars)
        assert result["status"] == "pass_through"

    def test_whole_chunk_skip_no_changes(self):
        """Test whole_chunk_skip_no_changes(input_vars) -> dict"""
        from scripts.choice_handler import whole_chunk_skip_no_changes

        input_vars = {"f_final_merged_mod_chunk": ["test1", "test2"]}
        result = whole_chunk_skip_no_changes(input_vars)
        assert result["status"] == "return_continue"

    def test_whole_chunk_overwrite_new_changes(self):
        """Test whole_chunk_overwrite_new_changes(input_vars) -> dict"""
        from scripts.choice_handler import whole_chunk_overwrite_new_changes

        input_vars = {"f_new_mod_chunk": ["test3", "test4"]}
        result = whole_chunk_overwrite_new_changes(input_vars)
        assert result["status"] == "return_continue"

    # def test_whole_chunk_save_merged_diff(self):
    #     """Test whole_chunk_save_merged_diff(input_vars) -> dict"""
    #     from scripts.choice_handler import whole_chunk_save_merged_diff

    #     input_vars = {
    #         "f_final_merged_mod_chunk": ["test3", "test4"],
    #         "display_chunk_array": []
    #     }
    #     result = whole_chunk_save_merged_diff(input_vars)
    #     assert result["status"] == "return_continue"
    #     assert result["processed_lines"] == ["test3\n", "test2\n", "test4\n"]

    @patch("scripts.choice_handler.view_text_with_less")
    def test_whole_chunk_view_diff_less(self, mock_view_text_with_less):
        """Test whole_chunk_view_diff_less(input_vars) -> dict"""
        from scripts.choice_handler import whole_chunk_view_diff_less

        input_vars = {"diff_lines_list": ["test1", "test2"]}
        result = whole_chunk_view_diff_less(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_less.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.choice_handler.view_text_with_less")
    def test_whole_file_view_temp_merged_mod_less(
        self, mock_view_text_with_less, mock_open_var
    ):
        """Test whole_file_view_temp_merged_mod_less(input_vars) -> dict"""
        from scripts.choice_handler import whole_file_view_temp_merged_mod_less

        input_vars = {"temp_merged_mod_file": "test1"}
        result = whole_file_view_temp_merged_mod_less(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_less.assert_called_once()

    @patch("scripts.choice_handler.view_text_with_pydoc")
    def test_whole_chunk_view_diff_pydoc(self, mock_view_text_with_pydoc):
        """Test whole_chunk_view_diff_pydoc(input_vars) -> dict"""
        from scripts.choice_handler import whole_chunk_view_diff_pydoc

        input_vars = {"diff_lines_list": ["test1", "test2"]}
        result = whole_chunk_view_diff_pydoc(input_vars)
        assert result["status"] == "continue"
        mock_view_text_with_pydoc.assert_called_once()

    @patch("scripts.choice_handler.open_files_in_vscode_compare")
    def test_whole_file_open_diff_vs_code(self, mock_open_files_in_vscode_compare):
        """Test whole_file_open_diff_vs_code(input_vars) -> dict"""
        from scripts.choice_handler import whole_file_open_diff_vs_code

        input_vars = {"new_mods_file": "test1", "final_merged_mod_file": "test2"}
        result = whole_file_open_diff_vs_code(input_vars)
        assert result["status"] == "continue"
        mock_open_files_in_vscode_compare.assert_called_once()

    @patch("scripts.choice_handler.open_files_in_vscode_compare")
    def test_whole_file_open_temp_merged_mod_vs_code(
        self, mock_open_files_in_vscode_compare
    ):
        """Test whole_file_open_temp_merged_mod_vs_code(input_vars) -> dict"""
        from scripts.choice_handler import whole_file_open_temp_merged_mod_vs_code

        input_vars = {"final_merged_mod_file": "test1"}
        result = whole_file_open_temp_merged_mod_vs_code(input_vars)
        assert result["status"] == "continue"
        mock_open_files_in_vscode_compare.assert_called_once()

    def test_skip_file(self):
        """Test skip_file(input_vars) -> dict"""
        from scripts.choice_handler import skip_file

        input_vars = {}
        result = skip_file(input_vars)
        assert result["status"] == "skip"

    def test_overwrite(self):
        """Test overwrite(input_vars) -> dict"""
        from scripts.choice_handler import overwrite

        input_vars = {}
        result = overwrite(input_vars)
        assert result["status"] == "overwrite"

    def test_quit_save(self):
        """Test quit_save(input_vars) -> dict"""
        from scripts.choice_handler import quit_save

        input_vars = {"tmp_merged_mod_lines": ["test1", "test2"]}
        result = quit_save(input_vars)
        assert result["status"] == "quit-save"
        assert result["processed_lines"] == ["test1", "test2"]

    def test_quit_out(self):
        """Test quit_out(input_vars) -> dict"""
        from scripts.choice_handler import quit_out

        input_vars = {}
        result = quit_out(input_vars)
        assert result["status"] == "quit"

    def test_load_choice_functions(self):
        """Test load_choice_functions(valid_requirements) -> dict"""
        from scripts.choice_handler import load_choice_functions

        valid_requirements = {"code": True, "less": True}
        result = load_choice_functions(valid_requirements)
        print(result)
        assert result == {
            "1": {"print_disp_diff": "Print the Display Diff"},
            "2": {
                "disp_chunk_skip_no_changes": "Display Chunk: Skip - Make No Changes"
            },
            "3": {
                "disp_chunk_overwrite_new_changes": "Display Chunk: Overwrite with New Changes"
            },
            "4": {"disp_chunk_save_merged_diff": "Display Chunk: Merge Changes"},
            "5": {"whole_chunk_skip_no_changes": "Whole Chunk: Skip - Make No Changes"},
            "6": {
                "whole_chunk_overwrite_new_changes": "Whole Chunk: Overwrite with New Changes"
            },
            "7": {"whole_chunk_save_merged_diff": "Whole Chunk: Merge Changes"},
            "8": {"whole_chunk_view_diff_less": "Whole Chunk: View Diff in CLI"},
            "9": {
                "whole_file_view_temp_merged_mod_less": "Whole File: View Temp Merged Mod in CLI"
            },
            "10": {"whole_file_open_diff_vs_code": "Whole File: Open Diff in VS Code"},
            "11": {
                "whole_file_open_temp_merged_mod_vs_code": "Whole File: Open Temp Merged Mod in VS Code"
            },
            "12": {"skip_file": "Whole File: Skip - Make No Changes"},
            "13": {"overwrite": "Whole File: Overwrite with New Changes"},
        }

    # @patch("scripts.choice_handler.input")
    # @patch("scripts.choice_handler.confirm_choice")
    # @patch("scripts.choice_handler.view_text_with_less")
    # @patch("scripts.choice_handler.view_text_with_pydoc")
    # @patch("scripts.choice_handler.open_files_in_vscode_compare")
    # @patch("scripts.choice_handler.disp_chunk_skip_no_changes")
    # @patch("scripts.choice_handler.disp_chunk_overwrite_new_changes")
    # @patch("scripts.choice_handler.disp_chunk_save_merged_diff")
    # @patch("scripts.choice_handler.whole_chunk_skip_no_changes")
    # @patch("scripts.choice_handler.whole_chunk_overwrite_new_changes")
    # @patch("scripts.choice_handler.whole_chunk_save_merged_diff")
    # @patch("scripts.choice_handler.whole_chunk_view_diff_less")
    # @patch("scripts.choice_handler.whole_file_view_temp_merged_mod_less")
    # @patch("scripts.choice_handler.whole_chunk_view_diff_pydoc")
    # @patch("scripts.choice_handler.whole_file_view_temp_merged_mod_pydoc")
    # @patch("scripts.choice_handler.whole_file_open_diff_vs_code")
    # @patch("scripts.choice_handler.whole_file_open_temp_merged_mod_vs_code")
    # @patch("scripts.choice_handler.quit_save")
    # @patch("scripts.choice_handler.quit_out")
    # def test_choice_handler(
    #     self,
    #     mock_quit_out,
    #     mock_quit_save,
    #     mock_whole_file_open_temp_merged_mod_vs_code,
    #     mock_whole_file_open_diff_vs_code,
    #     mock_whole_file_view_temp_merged_mod_pydoc,
    #     mock_whole_chunk_view_diff_pydoc,
    #     mock_whole_file_view_temp_merged_mod_less,
    #     mock_whole_chunk_view_diff_less,
    #     mock_whole_chunk_save_merged_diff,
    #     mock_whole_chunk_overwrite_new_changes,
    #     mock_whole_chunk_skip_no_changes,
    #     mock_disp_chunk_save_merged_diff,
    #     mock_disp_chunk_overwrite_new_changes,
    #     mock_disp_chunk_skip_no_changes,
    #     mock_open_files_in_vscode_compare,
    #     mock_view_text_with_pydoc,
    #     mock_view_text_with_less,
    #     mock_confirm_choice,
    #     mock_input,
    # ):
    #     """Test choice_handler(new_mods_file, final_merged_mod_file, diff_lines, f_final_merged_mod_chunk, f_new_mod_chunk, valid_requirements, temp_merged_mod_file, last_display_diff, last_user_choice, confirm_user_choice) -> dict"""
    #     from scripts.choice_handler import choice_handler

    #     new_mods_file = "test1"
    #     final_merged_mod_file = "test2"
    #     diff_lines = ["test3", "test4"]
    #     f_final_merged_mod_chunk = ["test5", "test6"]
    #     f_new_mod_chunk = ["test7", "test8"]
    #     valid_requirements = {"code": True, "less": True}
    #     temp_merged_mod_file = "test9"
    #     last_display_diff = "test10"
    #     last_user_choice = "test11"
    #     confirm_user_choice = True

    #     result = choice_handler(
    #         new_mods_file,
    #         final_merged_mod_file,
    #         diff_lines,
    #         f_final_merged_mod_chunk,
    #         f_new_mod_chunk,
    #         valid_requirements,
    #         temp_merged_mod_file,
    #         last_display_diff,
    #         last_user_choice,
    #         confirm_user_choice,
    #     )
    #     assert result["status"] == "continue"
    #     mock_quit_out.assert_not_called()
    #     mock_quit_save.assert_not_called()
    #     mock_whole_file_open_temp_merged_mod_vs_code.assert_called_once()
    #     mock_whole_file_open_diff_vs_code.assert_called_once()
    #     mock_disp_chunk_skip_no_changes.assert_called_once()
    #     mock_disp_chunk_overwrite_new_changes.assert_called_once()
    #     mock_disp_chunk_save_merged_diff.assert_called_once()
    #     mock_whole_chunk_skip_no_changes.assert_called_once()
    #     mock_whole_chunk_overwrite_new_changes.assert_called_once()
    #     mock_whole_chunk_save_merged_diff.assert_called_once()
    #     mock_whole_chunk_view_diff_less.assert_called_once()
    #     mock_whole_file_view_temp_merged_mod_less.assert_called_once()
    #     mock_whole_chunk_view_diff_pydoc.assert_called_once()
    #     mock_whole_file_view_temp_merged_mod_pydoc.assert_called_once()
    #     mock_whole_file_open_diff_vs_code.assert_called_once()
    #     mock_whole_file_open_temp_merged_mod_vs_code.assert_called_once()
    #     mock_quit_save.assert_called_once()
    #     mock_quit_out.assert_not_called()

    @patch("scripts.choice_handler.get_user_choice")
    def test_non_text_file_choice_handler(self, mock_get_user_choice):
        """Test non_text_file_choice_handler(final_merged_mod_path, new_mods_path) -> dict"""
        from scripts.choice_handler import non_text_file_choice_handler

        final_merged_mod_path = "test1"
        new_mods_path = "test2"
        mock_get_user_choice.return_value = "1"

        result = non_text_file_choice_handler(final_merged_mod_path, new_mods_path)
        assert result["status"] == "skip"

    @patch("scripts.choice_handler.get_user_choice")
    def test_bad_format_choice_handler(self, mock_get_user_choice):
        """Test bad_format_choice_handler(skip_file_bool, quit_out_bool) -> dict"""
        from scripts.choice_handler import bad_format_choice_handler

        skip_file_bool = False
        quit_out_bool = False
        mock_get_user_choice.return_value = "1"

        result = bad_format_choice_handler(skip_file_bool, quit_out_bool)
        assert result["skip_file_bool"] == True
        assert result["quit_out_bool"] == False


# class TestFormatDir(unittest.TestCase):
#     @patch("format_dir.recursive_format_dir")
#     @patch("os.listdir")
#     def test_recursive_format_dir(self, mock_listdir, mock_recursive_format_dir):
#         """Test recursive_format_dir(path, max_perf_chunk_size) -> None"""
#         from scripts.format_dir import recursive_format_dir

#         mock_listdir.return_value = ["test_file"]
#         path = "test1"
#         max_perf_chunk_size = 100
#         recursive_format_dir(path, max_perf_chunk_size)
#         mock_recursive_format_dir.assert_called_once()

#     @patch("format_dir.load_config")
#     def test_main(self, mock_load_config):
#         """Test main() -> bool"""
#         from scripts.format_dir import main

#         mock_load_config.return_value = {"max_perf_chunk_size": 1024}
#         path = "test1"
#         result = main()
#         assert result is True


class TestFormatHandler(unittest.TestCase):
    def test_strip_whitespace(self):
        """Test strip_whitespace(line) -> str"""
        from scripts.format_handler import strip_whitespace

        line = "test"
        result = strip_whitespace(line)
        assert result == "test"

    def test_remove_trailing_whitespace_and_newlines(self):
        """Test remove_trailing_whitespace_and_newlines(line) -> str"""
        from scripts.format_handler import remove_trailing_whitespace_and_newlines

        line = "test"
        result = remove_trailing_whitespace_and_newlines(line)
        assert result == "test"

    # @patch("os.path.split")
    # def test_display_file_parts(self, mock_os_path_split):
    #     """Test display_file_parts(final_file, new_file) -> None"""
    #     from scripts.format_handler import display_file_parts

    #     final_file = "test1"
    #     new_file = "test2"
    #     display_file_parts(final_file, new_file)
    #     mock_os_path_split.assert_called_once()

    def test_duplicate_line_check(self):
        """Test duplicate_line_check(temp_merged_mod_file, new_tmp_merged_mod_lines, perf_chunk, final_perf_chunk_sizes) -> list"""
        from scripts.format_handler import duplicate_line_check

        temp_merged_mod_file = "test1"
        new_tmp_merged_mod_lines = ["test2", "test3"]
        perf_chunk = 1
        final_perf_chunk_sizes = [100, 200]
        result = duplicate_line_check(
            temp_merged_mod_file,
            new_tmp_merged_mod_lines,
            perf_chunk,
            final_perf_chunk_sizes,
        )
        assert result == ["test2", "test3"]

    # def test_config_file_formatter(self):
    #     """Test config_file_formatter(unformatted_lines, tab_level) -> list"""
    #     from scripts.format_handler import config_file_formatter

    #     unformatted_lines = ["test1", "test2"]
    #     tab_level = 1
    #     result = config_file_formatter(unformatted_lines, tab_level)
    #     assert result == ["test1", "test2"]

    # def test_format_file(self):
    #     """Test format_file(file_path, performance_chunk_size) -> bool"""
    #     from scripts.format_handler import format_file

    #     file_path = "test1"
    #     performance_chunk_size = 100
    #     result = format_file(file_path, performance_chunk_size)
    #     assert result is True


class TestMergeTool(unittest.TestCase):
    """Functional tests for pak_merge_tool -> merge_tool.py"""

    def test_reload_temp_merged_mod_file(self):
        """Test reload_temp_merged_mod_file(tmp_merged_mod_file) -> int"""
        from scripts.merge_tool import reload_temp_merged_mod_file

        tmp_merged_mod_file = "test"
        result = reload_temp_merged_mod_file(tmp_merged_mod_file)
        assert result == 0

    # @patch("os.path.getsize")
    # @patch("merge_tool.reload_temp_merged_mod_file")
    # @patch("builtins.open", new_callable=mock_open)
    # @patch("json.loads")
    # @patch("merge_tool.strip_whitespace")
    # @patch("merge_tool.choice_handler")
    # @patch("shutil.move")
    # @patch("os.path.exists")
    # @patch("os.remove")
    # def test_merge_files(
    #     self,
    #     mock_remove,
    #     mock_exists,
    #     mock_move,
    #     mock_choice_handler,
    #     mock_strip_whitespace,
    #     mock_json_loads,
    #     mock_builtin_open,
    #     mock_reload_temp_merged_mod_file,
    #     mock_getsize,
    # ):
    #     """Test merge_files(new_mods_file, final_merged_mod_file) -> str"""
    #     from scripts.merge_tool import merge_files

    #     new_mods_file = "test1"
    #     final_merged_mod_file = "test2"
    #     valid_requirements = {"code": True, "less": True}

    #     mock_getsize.return_value = 0
    #     mock_reload_temp_merged_mod_file.return_value = 0
    #     mock_strip_whitespace.return_value = ["test"]
    #     mock_choice_handler.return_value = {
    #         "status": "continue",
    #         "processed_lines": ["test"],
    #     }
    #     mock_json_loads.return_value = {"test": "test"}
    #     mock_exists.return_value = True
    #     mock_move.return_value = None

    #     result = merge_files(new_mods_file, final_merged_mod_file, valid_requirements)
    #     assert result == "continue"

    # @patch("os.path.join", side_effect=os.path.join)
    # @patch("os.path.isdir")
    # @patch("os.listdir")
    # @patch("shutil.copy2")
    # @patch("os.makedirs")
    # @patch("os.path.exists")
    # @patch("merge_tool.merge_files")
    # @patch("merge_tool.merge_directories")
    # def test_merge_directories(
    #     self,
    #     mock_merge_directories,
    #     mock_merge_files,
    #     mock_exists,
    #     mock_makedirs,
    #     mock_copy2,
    #     mock_list_dir,
    #     mock_is_dir,
    #     mock_path_join,
    # ):
    #     """Test merge_directories(new_mods_dir, final_merged_mod_dir) -> str"""
    #     from scripts.merge_tool import merge_directories

    #     new_mods_dir = "test1"
    #     final_merged_mod_dir = "test2"
    #     valid_requirements = {"code": True, "less": True}

    #     mock_copy2.return_value = None
    #     mock_exists.return_value = False
    #     mock_is_dir.return_value = True
    #     mock_list_dir.return_value = ["file1", "file2"]
    #     mock_makedirs.return_value = None
    #     mock_merge_files.return_value = "continue"
    #     mock_merge_directories.return_value = "continue"

    #     result = merge_directories(
    #         new_mods_dir, final_merged_mod_dir, valid_requirements, {"max_perf_chunk_size": 1024}
    #     )
    #     assert result == "continue"

    # @patch("merge_tool.merge_directories")
    # @patch("argparse.ArgumentParser.parse_args")
    # @patch("os.listdir")
    # @patch("os.path.isdir")
    # @patch("os.path.join", side_effect=os.path.join)
    # @patch("merge_tool.validate_requirements")
    # def test_main(
    #     self,
    #     mock_validate_requirements,
    #     mock_path_join,
    #     mock_is_dir,
    #     mock_list_dir,
    #     mock_parse_args,
    #     mock_merge_directories,
    # ):
    #     """Test main() -> bool"""
    #     from scripts.merge_tool import main

    #     mock_validate_requirements.return_value = {"code": True, "less": True}
    #     mock_parse_args.return_value = argparse.Namespace(
    #         new_mods_dir="test1",
    #         final_merged_mod_dir="test2",
    #         verbose=False,
    #         confirm=False,
    #         unpak=False,
    #         unpak_only=False,
    #         org_comp=False
    #     )
    #     mock_merge_directories.return_value = "quit"
    #     mock_list_dir.return_value = ["file1", "file2"]
    #     mock_is_dir.return_value = True

    #     result = main()
    #     assert result is False


class TestRepakAndMerge(unittest.TestCase):
    # def test_sanitize_mod_name(self):
    #     """Test sanitize_mod_name(pak_file_name) -> dict"""
    #     from scripts.repak_and_merge import sanitize_mod_name

    #     pak_file_name = "test1"
    #     result = sanitize_mod_name(pak_file_name)
    #     assert result == {"clean_name": pak_file_name, "version": "1"}

    def test_update_mod_version(self):
        """Test update_mod_version(history, pak_file_clean_name, new_pak_file_version) -> dict"""
        from scripts.repak_and_merge import update_mod_version

        history = {"test1": {"version": ["1"]}}
        pak_file_clean_name = "test1"
        new_pak_file_version = "2"

        result = update_mod_version(history, pak_file_clean_name, new_pak_file_version)
        assert result == {"version": ["1", "2"]}

    # @patch("subprocess.run")
    # @patch("os.path.exists")
    # @patch("os.path.join")
    # @patch("os.listdir")
    # @patch("builtins.open", new_callable=mock_open)
    # @patch("scripts.repak_and_merge.load_history")  # Add this if needed
    # def test_unpack_files(
    #     self,
    #     mock_load_history,
    #     mock_open_file,
    #     mock_list_dir,
    #     mock_path_join,
    #     mock_exists,
    #     mock_subprocess_run,
    # ):
    #     """Test unpack_files(repak_path, pak_dir, extract_dir, resume) -> bool"""
    #     from scripts.repak_and_merge import unpack_files

    #     # Mock the config file
    #     mock_json_data = '{"repak_path": "path/to/repak.exe"}'
    #     mock_file_handle = mock_open_file.return_value
    #     mock_file_handle.read.return_value = mock_json_data

    #     # Mock path exists to return True for repak.exe
    #     mock_exists.return_value = True

    #     # Mock subprocess.run to return success
    #     mock_subprocess_run.return_value = subprocess.CompletedProcess(
    #         args=["test1", "test2", "test3"], returncode=0
    #     )

    #     # Mock load_history if needed
    #     mock_load_history.return_value = {}
    #     mock_list_dir.return_value = ["test1.pak"]

    #     repak_path = "path/to/repak.exe"
    #     pak_dir = "test2"
    #     extract_dir = "test3"
    #     resume = False

    #     result = unpack_files(repak_path, pak_dir, extract_dir, resume)
    #     assert result is True

    #     # Verify both read and write operations on the config file
    #     mock_open_file.assert_has_calls(
    #         [
    #             call("config.json", "r", encoding="utf-8"),
    #             call().read(),
    #         ],
    #         any_order=True,
    #     )

    # def test_save_history(self):
    #     """Test save_history(history) -> bool"""
    #     from scripts.repak_and_merge import save_history

    #     history = {"test1": {"version": ["1"]}}

    #     result = save_history(history)
    #     assert result is True

    # def test_load_history(self):
    #     """Test load_history() -> dict"""
    #     from scripts.repak_and_merge import load_history

    #     result = load_history()
    #     assert result == {"test1": {"version": ["1"]}}

    # def test_merge_mods(self):
    #     """Test merge_mods(sorted_new_mods_dir_list, new_mods_dir, final_merged_mod_dir, verbose, confirm, org_comp, resume) -> bool"""
    #     from scripts.repak_and_merge import merge_mods

    #     sorted_new_mods_dir_list = ["test1", "test2"]
    #     new_mods_dir = "test3"
    #     final_merged_mod_dir = "test4"
    #     verbose = False
    #     confirm = False
    #     org_comp = False
    #     resume = False

    #     result = merge_mods(
    #         sorted_new_mods_dir_list,
    #         new_mods_dir,
    #         final_merged_mod_dir,
    #         verbose,
    #         confirm,
    #         org_comp,
    #         resume,
    #     )
    #     assert result is True

    # @patch("argparse.ArgumentParser.parse_args")
    # @patch("os.listdir")
    # @patch("os.path.isdir")
    # @patch("os.path.join", side_effect=os.path.join)
    # @patch("repak_and_merge.merge_mods")
    # def test_main(
    #     self,
    #     mock_merge_mods,
    #     mock_path_join,
    #     mock_is_dir,
    #     mock_list_dir,
    #     mock_parse_args,
    # ):
    #     """Test main() -> bool"""
    #     from scripts.repak_and_merge import main

    #     mock_parse_args.return_value = argparse.Namespace(
    #         new_mods_dir="test1",
    #         final_merged_mod_dir="test2",
    #         verbose=False,
    #         confirm=False,
    #         unpak=False,
    #         unpak_only=False,
    #         org_comp=False
    #     )
    #     mock_merge_mods.return_value = True
    #     mock_list_dir.return_value = ["file1", "file2"]
    #     mock_is_dir.return_value = True

    #     result = main()
    #     assert result is True


# class TestRequirementsHandler(unittest.TestCase):
#     # FIXME: Breaks on GitHub Actions
#     # @patch("subprocess.run")
#     # def test_version_check(self, mock_subprocess_run):
#     #     """Test version_check(command) -> bool"""
#     #     from scripts.requirements_handler import version_check

#     #     command = "test1"
#     #     mock_subprocess_run.return_value = subprocess.CompletedProcess(
#     #         args=command, returncode=0
#     #     )
#     #     result = version_check(command)
#     #     assert result is True

#     def test_validate_requirements(self):
#         """Test validate_requirements() -> dict"""
#         from scripts.requirements_handler import validate_requirements

#         result = validate_requirements()
#         assert result == {"code": True, "less": True}

#     @patch("builtins.open", new_callable=mock_open)
#     def test_load_config(self, mock_open_file):
#         """Test load_config(config_name) -> dict"""
#         from scripts.requirements_handler import load_config

#         mock_json_data = '{"test1": "test2"}'
#         mock_file_handle = mock_open_file.return_value
#         mock_file_handle.read.return_value = mock_json_data

#         config_name = "test1"
#         result = load_config(config_name)
#         assert result == {"test1": "test2"}

#     # @patch("builtins.open", new_callable=mock_open)
#     # def test_save_config(self, mock_open_file):
#     #     """Test save_config(config) -> None"""
#     #     from scripts.requirements_handler import save_config

#     #     config = {"test1": "test2"}
#     #     save_config(config)
#     #     mock_open_file.assert_called_once_with("config.json", "w", encoding="utf-8")
#     #     mock_open_file.return_value.write.assert_called_once_with(
#     #         json.dumps(config, indent=4)
#     #     )

# pak_merge_tool
Tool to merge Stalker 2 mod pak files into a single pak file.
    Most of the files in the pak files are text files, so the tool
    will merge the text files and remove duplicates.

Usage for merge_tool.py: python merge_tool.py --new_mods_dir="<directory>" --final_merged_mod_dir="<directory>"
Options:
    --verbose --> Make logging more verbose
    --confirm --> Extra confirmation for choices when merging files
    --new_mods_dir --> Directory containing unpacked new mods
    --final_merged_mod_dir --> Directory containing unpacked current mods

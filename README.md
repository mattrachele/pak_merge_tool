# pak_merge_tool
Tool to merge pak files into a single pak file.

# Repak and Merge Script
Allows you to unpak pak files using repak.exe, and then runs merge_tool.py
to merge the new_mods_dir into the final_merged_mod_dir.

NOTE: repak.exe only unpaks the .pak data files, which contain some config files
and scripts but not the actual game assets. Use FModel to extract the game assets.

## Usage
```bash
python repak_and_merge.py --new_mods_dir="<directory>" --final_merged_mod_dir="<directory>"
```

## Options
* --verbose | Make logging more verbose
* --confirm | Extra confirmation for choices when merging files
* --new_mods_dir | Directory containing unpacked new mods
* --final_merged_mod_dir | Directory containing unpacked current mods

# Merge Script
Merges directories into the final_merged_mod_dir by giving the user options
to skip, overwrite, or merge lines based on a single display diff, a performance chunk,
or the whole file. The script will auto-add new files and directories that don't exist
in the final_merged_mod_dir.

## Usage
```bash
python merge_tool.py --new_mods_dir="<directory>" --final_merged_mod_dir="<directory>"
```

## Options
* --verbose | Make logging more verbose
* --confirm | Extra confirmation for choices when merging files
* --new_mods_dir | Directory containing unpacked new mods
* --final_merged_mod_dir | Directory containing unpacked current mods

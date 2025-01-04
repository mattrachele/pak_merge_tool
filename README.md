# pak_merge_tool
Tool to merge pak files into a single pak file.

# Repak and Merge Script
Allows you to unpak pak files using repak.exe, and then runs merge_tool.py
to merge the new_mods_dir into the final_merged_mod_dir.

NOTE: repak.exe only unpaks the .pak data files, which contain some config files
and scripts but not the actual game assets. Use FModel to extract the game assets.

## Usage:
```bash
python repak_and_merge.py [-h] [--verbose] [--confirm] [--repak_path REPAK_PATH] [--unpak] [--unpak_only] [--org_comp] --new_mods_dir NEW_MODS_DIR [--resume RESUME] --final_merged_mod_dir FINAL_MERGED_MOD_DIR
```

## Options:
*  -h, --help | show this help message and exit
*  --verbose | Enable verbose output
*  --confirm | Disable user confirmation
*  --repak_path REPAK_PATH | The path to the repak executable
*  --unpak | Unpack the mods
*  --unpak_only | Only unpack the mods
*  --org_comp | Compare the original base game files
*  --new_mods_dir NEW_MODS_DIR | The directory containing the new mods
*  --resume RESUME | Resume merging the mods
*  --final_merged_mod_dir FINAL_MERGED_MOD_DIR | The directory containing the final merged mods

# Merge Script
Merges directories into the final_merged_mod_dir by giving the user options
to skip, overwrite, or merge lines based on a single display diff, a performance chunk,
or the whole file. The script will auto-add new files and directories that don't exist
in the final_merged_mod_dir.

## Usage
```bash
python merge_tool.py [-h] [--verbose] [--confirm] --new_mods_dir NEW_MODS_DIR --final_merged_mod_dir FINAL_MERGED_MOD_DIR
```

## Options
*    -h, --help | show this help message and exit
*    --verbose  | Enable verbose output
*    --confirm  | Disable user confirmation
*    --new_mods_dir NEW_MODS_DIR | The directory containing the new mods
*    --final_merged_mod_dir FINAL_MERGED_MOD_DIR | The directory containing the final merged mods

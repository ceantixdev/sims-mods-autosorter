import os
import zipfile
import re
import json
import shutil
from pathlib import Path

# Define filenames
CONFIG_FILE = 'config.json'

def load_config():
    """Loads the configuration file."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        print(f"Error: {CONFIG_FILE} not found. Please ensure it exists located next to this script.")
        input("Press Enter to exit...")
        exit()
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {CONFIG_FILE} is not valid JSON. Please check the formatting.")
        input("Press Enter to exit...")
        exit()

def get_sims_mods_path(config):
    """Determines the actual Sims 4 Mods directory path."""
    override = config.get("sims_mods_path_override", "")
    if override:
        path = Path(override)
    else:
        # Auto-detect standard Windows Documents installation
        path = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"
    
    if not path.exists():
        print(f"CRITICAL ERROR: Could not locate Sims 4 directory at: {path}")
        print("Please check your config.json or ensure The Sims 4 is installed correctly.")
        input("Press Enter to exit...")
        exit()
    return path

def process_zips(config, mods_path):
    """Main logic to loop through zips and sort files."""
    source_path = Path(config.get("source_zips_folder", "./PUT_ZIPS_HERE"))
    unsorted_name = config.get("unsorted_folder_name", "_unsorted")
    rules = config.get("rules", {})

    # Ensure source directory exists
    if not source_path.exists():
        source_path.mkdir(parents=True)
        print(f"Created source folder: {source_path.absolute()}")
        print("Please put your .zip files into that folder and run the script again.")
        input("Press Enter to exit...")
        exit()

    zip_files = list(source_path.glob("*.zip"))
    if not zip_files:
        print(f"No .zip files found in {source_path.absolute()}")
        input("Press Enter to exit...")
        return

    print(f"Found {len(zip_files)} zip files to process...")
    count_moved = 0
    count_unsorted = 0

    for zip_path in zip_files:
        print(f"\nProcessing archive: {zip_path.name}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    # IGNORE RULE: Only process .package files, ignore directories
                    if not file_info.filename.lower().endswith('.package') or file_info.is_dir():
                        continue

                    # We extract the actual filename, ignoring folders inside the zip
                    # (flattening the structure)
                    base_filename = os.path.basename(file_info.filename)
                    if not base_filename: continue # Skip if it was just a directory path

                    target_folder_name = unsorted_name
                    
                    # REGEX SEARCH LOGIC
                    found_match = False
                    for folder_key, pattern_str in rules.items():
                        # Use IGNORECASE so "Hair" matches "hair"
                        if re.search(pattern_str, base_filename, re.IGNORECASE):
                            target_folder_name = folder_key
                            found_match = True
                            break
                    
                    # Determine final paths
                    dest_dir = mods_path / target_folder_name
                    # Ensure destination subfolder exists (e.g., create 'hair' if missing)
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    dest_file_path = dest_dir / base_filename

                    # Check if file already exists to prevent overwriting accidentally
                    if dest_file_path.exists():
                         print(f"  [SKIP] File exists: {target_folder_name}/{base_filename}")
                         continue

                    # Extract the file directly to the target, flattening zip paths
                    print(f"  [EXTRACT] Found '{base_filename}' -> Sorting to '{target_folder_name}'")
                    with open(dest_file_path, 'wb') as f:
                        f.write(zip_ref.read(file_info.filename))
                    
                    if found_match:
                        count_moved += 1
                    else:
                        count_unsorted += 1

            # Optional: Move processed zip to an 'archive' folder so you don't re-process it
            processed_dir = source_path / "processed_archive"
            processed_dir.mkdir(exist_ok=True)
            shutil.move(str(zip_path), str(processed_dir / zip_path.name))
            print(f"Finished {zip_path.name}, moved zip to archive folder.")

        except zipfile.BadZipFile:
             print(f"ERROR: {zip_path.name} is corrupted and cannot be read.")
        except Exception as e:
             print(f"An unexpected error occurred with {zip_path.name}: {e}")

    print("\n" + "="*30)
    print(f"DONE! Sorted {count_moved} files. Placed {count_unsorted} files into '{unsorted_name}'.")
    print("="*30)
    input("Press Enter to close.")

if __name__ == "__main__":
    print("Sims 4 Mod Auto-Sorter starting...")
    loaded_config = load_config()
    sims_path = get_sims_mods_path(loaded_config)
    print(f"Target Mods Directory: {sims_path}")
    process_zips(loaded_config, sims_path)
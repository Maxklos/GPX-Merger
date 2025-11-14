from fit2gpx import Converter
import os
import glob
from datetime import datetime, timedelta
import shutil
import subprocess
import re
from collections import Counter
import argparse
from tqdm import tqdm


def create_folders(fit_folder, gpx_folder, merged_folder):
    if not os.path.exists(fit_folder):
        os.makedirs(fit_folder)
        print("Created input_folder:", fit_folder)
        print("Please place .fit files in the input folder")
        exit()

    if not os.path.exists(gpx_folder):
        os.makedirs(gpx_folder)
        if DEBUG:
            print("Created gpx_folder:", gpx_folder)

    if not os.path.exists(merged_folder):
        os.makedirs(merged_folder)
        if DEBUG:
            print("Created merged_folder:", merged_folder)

def rename_gpx_files(gpx_folder, merged_folder):
    gpx_files = glob.glob(os.path.join(gpx_folder, '*.gpx'))
    
    if not gpx_files:
        return
    
    suffix = 1
    sorted_files = sorted(gpx_files, key=lambda x: get_earliest_timestamp(x))
    
    for gpx_file in tqdm(sorted_files, desc="Renaming files", unit="file", ncols=80):
        timestamp_str = get_earliest_timestamp(gpx_file)
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                tqdm.write(f"Incorrect timestamp format for file: {gpx_file}")
                continue
            new_filename = timestamp.strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
            suffix += 1

            if len(glob.glob(os.path.join(gpx_folder, f"{timestamp.strftime('%Y-%m-%d')}*.gpx"))) == 1:
                # Only one file for this day, rename and move directly to the output folder
                new_filename = timestamp.strftime('%Y-%m-%d') + '-single.gpx'
                new_filepath = os.path.join(merged_folder, new_filename)
                shutil.move(gpx_file, new_filepath)
                if DEBUG:
                    tqdm.write(f"Moved single file: {gpx_file} to {new_filepath}")
                continue

            new_filepath = os.path.join(gpx_folder, new_filename)

            while os.path.exists(new_filepath):
                new_filename = timestamp.strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
                new_filepath = os.path.join(gpx_folder, new_filename)
                suffix += 1

            # Move the file to a folder with the first 10 characters of the filename
            folder_name = new_filename[:10]
            folder_path = os.path.join(gpx_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            destination_path = os.path.join(folder_path, new_filename)
            shutil.move(gpx_file, destination_path)
            if DEBUG:
                tqdm.write(f"Moved file: {gpx_file} to {destination_path}")
        else:
            tqdm.write(f"No timestamp found in file: {gpx_file}")


def get_earliest_timestamp(gpx_file):
    with open(gpx_file, 'r') as f:
        lines = f.readlines()
        timestamp_str = next((line.strip().replace('<time>', '').replace('</time>', '') for line in lines if '<time>' in line), None)
    return timestamp_str

def merge_gpx_files(gpx_folder, merged_folder):
    all_subfolders = []
    while True:
        subfolders = [f for f in os.listdir(gpx_folder) if os.path.isdir(os.path.join(gpx_folder, f))]
        if not subfolders:
            break
        all_subfolders.extend(subfolders)
        
        for subfolder in tqdm(subfolders, desc="Merging files", unit="merge", ncols=80):
            subfolder_path = os.path.join(gpx_folder, subfolder)
            merge_files_in_folder(subfolder_path, merged_folder)
            shutil.rmtree(subfolder_path)

def merge_files_in_folder(folder_path, merged_folder):
    gpx_files = sorted(glob.glob(os.path.join(folder_path, '*.gpx')))
    if len(gpx_files) < 2:
        return

    output_file = os.path.join(folder_path, f"{os.path.basename(folder_path)}-complete.gpx")
    gpxmerge_command = f'gpxmerge {" ".join(gpx_files)} -o {output_file}'
    subprocess.run(gpxmerge_command, shell=True, cwd="./", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if DEBUG:
        tqdm.write(f"Merged files in folder: {folder_path}")

    merged_filepath = os.path.join(merged_folder, os.path.basename(output_file))
    shutil.move(output_file, merged_filepath)
    if DEBUG:
        tqdm.write(f"Moved merged file to: {merged_filepath}")


# ==================== 2006-FIX FUNCTIONS ====================

def get_latest_date_from_file(gpx_file, debug_verbose=False):
    """Finds the latest date in a GPX file (ignores outlier years)"""
    if DEBUG and debug_verbose:
        print(f"[DEBUG] Scanning file: {gpx_file}")
    
    all_dates = []
    
    with open(gpx_file, 'r', encoding='utf-8') as f:
        content = f.read()
        time_tags = re.findall(r'<time>(.*?)</time>', content)
        
        if DEBUG and debug_verbose:
            print(f"[DEBUG] Found {len(time_tags)} timestamps in {os.path.basename(gpx_file)}")
        
        for time_str in time_tags:
            try:
                timestamp = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
                all_dates.append(timestamp)
            except ValueError:
                if DEBUG:
                    print(f"[WARNING] Could not parse timestamp: {time_str}")
        
        if not all_dates:
            return None
        
        year_counts = Counter(d.year for d in all_dates)
        most_common_year = year_counts.most_common(1)[0][0]
        
        if DEBUG and (debug_verbose or len(year_counts) > 1):
            print(f"[DEBUG] === Year analysis ===")
            for year, count in sorted(year_counts.items()):
                percentage = (count / len(all_dates)) * 100
                marker = " (DOMINANT)" if year == most_common_year else " (OUTLIER - IGNORED)"
                print(f"[DEBUG]   Year {year}: {count} timestamps ({percentage:.1f}%){marker}")
        
        filtered_dates = [d for d in all_dates if d.year == most_common_year]
        latest_date = max(filtered_dates)
        
        if DEBUG and debug_verbose:
            print(f"[DEBUG] === First 10 raw timestamps (all years) ===")
            for i, time_str in enumerate(time_tags[:10]):
                print(f"[DEBUG]   [{i+1}] RAW: {time_str}")
            
            print(f"[DEBUG] === Filtered results (year {most_common_year} only) ===")
            print(f"[DEBUG]   Earliest: {min(filtered_dates).strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"[DEBUG]   Latest: {max(filtered_dates).strftime('%d/%m/%Y %H:%M:%S')}")
    
    if DEBUG and debug_verbose:
        print(f"[DEBUG] Latest date in {os.path.basename(gpx_file)}: {latest_date.strftime('%d/%m/%Y %H:%M:%S')} (from {len(filtered_dates)} valid timestamps)")
    
    return latest_date


def get_earliest_date_from_file(gpx_file):
    """Finds the earliest date in a GPX file (ignores outlier years) - for filenames"""
    all_dates = []
    
    with open(gpx_file, 'r', encoding='utf-8') as f:
        content = f.read()
        time_tags = re.findall(r'<time>(.*?)</time>', content)
        
        for time_str in time_tags:
            try:
                timestamp = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
                all_dates.append(timestamp)
            except ValueError:
                pass
        
        if not all_dates:
            return None
        
        year_counts = Counter(d.year for d in all_dates)
        most_common_year = year_counts.most_common(1)[0][0]
        
        filtered_dates = [d for d in all_dates if d.year == most_common_year]
        earliest_date = min(filtered_dates)
    
    return earliest_date


def check_if_fix_needed(output_folder):
    """Checks if timestamps are older than 1 year and if fix is needed"""
    gpx_files = glob.glob(os.path.join(output_folder, '*.gpx'))
    
    if not gpx_files:
        return False
    
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=365)
    
    for gpx_file in gpx_files:
        latest_date = get_latest_date_from_file(gpx_file, debug_verbose=False)
        if latest_date and latest_date < one_year_ago:
            if DEBUG:
                print(f"[DEBUG] Found old timestamp: {latest_date.strftime('%d/%m/%Y')} (older than 1 year)")
            return True
    
    return False


def find_newest_file(output_folder):
    """Finds the file with the latest date"""
    if DEBUG:
        print("\n[DEBUG] === Starting search for newest file ===")
    
    gpx_files = glob.glob(os.path.join(output_folder, '*.gpx'))
    
    if not gpx_files:
        print("[ERROR] No GPX files found in output folder!")
        return None, None
    
    if DEBUG:
        print(f"[DEBUG] Found {len(gpx_files)} GPX files to scan")
    
    newest_file = None
    newest_date = None
    
    for gpx_file in gpx_files:
        is_first = (newest_file is None)
        latest_date = get_latest_date_from_file(gpx_file, debug_verbose=(DEBUG and is_first))
        if latest_date and (newest_date is None or latest_date > newest_date):
            newest_date = latest_date
            newest_file = gpx_file
    
    if newest_file and DEBUG:
        print(f"\n[DEBUG] === Newest file found: {os.path.basename(newest_file)} ===")
        print(f"[DEBUG] === Date: {newest_date.strftime('%d/%m/%Y %H:%M:%S')} ===")
        
        print(f"\n[DEBUG] === DETAILED ANALYSIS of newest file ===")
        get_latest_date_from_file(newest_file, debug_verbose=True)
        print()
    
    return newest_file, newest_date


def fix_timestamps_in_file(input_file, output_file, date_offset_days):
    """Corrects all timestamps in a file"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    time_tags = re.findall(r'<time>(.*?)</time>', content)
    timestamps_fixed = 0
    
    for old_time_str in time_tags:
        try:
            old_timestamp = datetime.strptime(old_time_str, '%Y-%m-%dT%H:%M:%SZ')
            new_timestamp = old_timestamp + timedelta(days=date_offset_days)
            new_time_str = new_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            content = content.replace(f'<time>{old_time_str}</time>', f'<time>{new_time_str}</time>', 1)
            timestamps_fixed += 1
        
        except ValueError:
            if DEBUG:
                tqdm.write(f"[WARNING] Could not parse timestamp: {old_time_str}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return timestamps_fixed


def rename_fixed_file(fixed_file, fixed_folder):
    """Renames a corrected file based on its new date"""
    earliest_date = get_earliest_date_from_file(fixed_file)
    
    if not earliest_date:
        if DEBUG:
            tqdm.write(f"[WARNING] Could not extract date from {os.path.basename(fixed_file)}, keeping original name")
        return fixed_file
    
    old_filename = os.path.basename(fixed_file)
    if '-complete.gpx' in old_filename:
        suffix = '-complete.gpx'
    elif '-single.gpx' in old_filename:
        suffix = '-single.gpx'
    else:
        suffix = '.gpx'
    
    new_filename = earliest_date.strftime('%Y-%m-%d') + suffix
    new_filepath = os.path.join(fixed_folder, new_filename)
    
    if fixed_file != new_filepath:
        os.rename(fixed_file, new_filepath)
        return new_filepath
    
    return fixed_file


def apply_2006_fix(output_folder):
    """Main function for the 2006-Fix"""
    print("\n" + "="*60)
    print("=== 2006-FIX MODE ===")
    print("="*60)
    
    newest_file, newest_date = find_newest_file(output_folder)
    
    if not newest_file or not newest_date:
        print("[ERROR] Could not find any valid GPX files with timestamps!")
        return
    
    print(f"\nNewest file: {os.path.basename(newest_file)}")
    print(f"Date in file: {newest_date.strftime('%d/%m/%Y')}")
    print(f"Time in file: {newest_date.strftime('%H:%M:%S')}")
    
    while True:
        correct_date_str = input("\nOn which date was this file recorded? (Format: DD/MM/YYYY): ").strip()
        try:
            correct_date = datetime.strptime(correct_date_str, '%d/%m/%Y')
            correct_datetime = correct_date.replace(hour=newest_date.hour, minute=newest_date.minute, second=newest_date.second)
            break
        except ValueError:
            print("[ERROR] Invalid date format! Please use DD/MM/YYYY (e.g., 13/11/2025)")
    
    date_offset = (correct_datetime.date() - newest_date.date()).days
    
    if DEBUG:
        print(f"\n[DEBUG] Calculated date offset: {date_offset} days")
        print(f"[DEBUG] Old date: {newest_date.strftime('%d/%m/%Y')}")
        print(f"[DEBUG] New date: {correct_datetime.strftime('%d/%m/%Y')}")
    
    fixed_folder = "./output_fixed/"
    if not os.path.exists(fixed_folder):
        os.makedirs(fixed_folder)
        if DEBUG:
            print(f"\n[DEBUG] Created folder: {fixed_folder}")
    
    gpx_files = glob.glob(os.path.join(output_folder, '*.gpx'))
    
    print(f"\nProcessing {len(gpx_files)} files...\n")
    
    total_timestamps = 0
    
    for gpx_file in tqdm(gpx_files, desc="Fixing timestamps", unit="file", ncols=80):
        filename = os.path.basename(gpx_file)
        temp_output_file = os.path.join(fixed_folder, filename)
        
        old_date = get_latest_date_from_file(gpx_file, debug_verbose=False)
        
        fixed_count = fix_timestamps_in_file(gpx_file, temp_output_file, date_offset)
        total_timestamps += fixed_count
        
        final_file = rename_fixed_file(temp_output_file, fixed_folder)
        
        if old_date:
            new_date = old_date + timedelta(days=date_offset)
            tqdm.write(f"  ✓ {filename}: {old_date.strftime('%d/%m/%Y')} -> {new_date.strftime('%d/%m/%Y')}")
    
    print("\n" + "="*60)
    print(f"✓ 2006-Fix complete!")
    print(f"✓ Processed {len(gpx_files)} files")
    print(f"✓ Fixed {total_timestamps} total timestamps")
    print(f"✓ Fixed files saved to: {fixed_folder}")
    print("="*60 + "\n")


# ==================== MAIN SCRIPT ====================

parser = argparse.ArgumentParser(description='FIT to GPX Converter and Merger')
parser.add_argument('--debug', '--d', action='store_true', help='Enable debug output')
args = parser.parse_args()

DEBUG = args.debug

if DEBUG:
    print("[DEBUG MODE ENABLED]\n")

conv = Converter()
fit_folder = "./input/"
gpx_folder = "./tmp/"
merged_folder = "./output/"

create_folders(fit_folder, gpx_folder, merged_folder)

fit_files = glob.glob(os.path.join(fit_folder, '*.fit'))
print(f"Converting {len(fit_files)} FIT files to GPX...")

for fit_file in tqdm(fit_files, desc="Converting", unit="file", ncols=80):
    try:
        base_name = os.path.splitext(os.path.basename(fit_file))[0]
        output_file = os.path.join(gpx_folder, f"{base_name}.gpx")
        conv.fit_to_gpx(f_in=fit_file, f_out=output_file)
    except Exception as e:
        if DEBUG:
            tqdm.write(f"[ERROR] Failed to convert {os.path.basename(fit_file)}: {e}")

print("✓ FIT to GPX conversion DONE\n")

rename_gpx_files(gpx_folder, merged_folder)
print("✓ File naming DONE")

merge_gpx_files(gpx_folder, merged_folder)
print("✓ File combining DONE")

if check_if_fix_needed(merged_folder):
    print("\n" + "="*60)
    print("⚠️  Old timestamps detected (older than 1 year)")
    apply_fix = input("Do you want to apply the 2006-Fix? (y/n): ").strip().lower()
    
    if apply_fix in ['y', 'yes']:
        apply_2006_fix(merged_folder)
    else:
        print("2006-Fix skipped.")
        print("="*60 + "\n")
else:
    if DEBUG:
        print("\n[DEBUG] No old timestamps detected. 2006-Fix not needed.")
    print("\n✓ All done! No date fixes needed.\n")

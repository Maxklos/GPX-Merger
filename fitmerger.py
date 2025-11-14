from fit2gpx import Converter
import os
import glob
from datetime import datetime, timedelta
import shutil
import subprocess
import re


def create_folders(fit_folder, gpx_folder, merged_folder):
    # Überprüfen und Erstellen des fit_folder
    if not os.path.exists(fit_folder):
        os.makedirs(fit_folder)
        print("Created input_folder:", fit_folder)
        print("Please place .fit files in the input folder")
        exit()

    # Überprüfen und Erstellen des gpx_folder
    if not os.path.exists(gpx_folder):
        os.makedirs(gpx_folder)
        print("Created gpx_folder:", gpx_folder)

    # Überprüfen und Erstellen des merged_folder
    if not os.path.exists(merged_folder):
        os.makedirs(merged_folder)
        print("Created merged_folder:", merged_folder)

def rename_gpx_files(gpx_folder, merged_folder):
    gpx_files = glob.glob(os.path.join(gpx_folder, '*.gpx'))
    suffix = 1
    sorted_files = sorted(gpx_files, key=lambda x: get_earliest_timestamp(x))  # Sort files by earliest timestamp
    for gpx_file in sorted_files:
        timestamp_str = get_earliest_timestamp(gpx_file)
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                print("Incorrect timestamp format for file:", gpx_file)
                continue
            new_filename = timestamp.strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
            suffix += 1

            if len(glob.glob(os.path.join(gpx_folder, f"{timestamp.strftime('%Y-%m-%d')}*.gpx"))) == 1:
                # Only one file for this day, rename and move directly to the output folder
                new_filename = timestamp.strftime('%Y-%m-%d') + '-single.gpx'
                new_filepath = os.path.join(merged_folder, new_filename)
                shutil.move(gpx_file, new_filepath)
                print("Moved single file:", gpx_file, "to", new_filepath)
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
            print("Moved file:", gpx_file, "to", destination_path)
        else:
            print("No timestamp found in file:", gpx_file)


def get_earliest_timestamp(gpx_file):
    with open(gpx_file, 'r') as f:
        lines = f.readlines()
        timestamp_str = next((line.strip().replace('<time>', '').replace('</time>', '') for line in lines if '<time>' in line), None)
    return timestamp_str

def merge_gpx_files(gpx_folder, merged_folder):
    while True:
        subfolders = [f for f in os.listdir(gpx_folder) if os.path.isdir(os.path.join(gpx_folder, f))]
        if not subfolders:
            break

        for subfolder in subfolders:
            subfolder_path = os.path.join(gpx_folder, subfolder)
            merge_files_in_folder(subfolder_path, merged_folder)
            shutil.rmtree(subfolder_path)  # Löschen des ursprünglichen Ordners nach dem Zusammenführen und Verschieben

def merge_files_in_folder(folder_path, merged_folder):
    gpx_files = sorted(glob.glob(os.path.join(folder_path, '*.gpx')))  # Sort GPX files in alphabetical order
    if len(gpx_files) < 2:
        return

    output_file = os.path.join(folder_path, f"{os.path.basename(folder_path)}-complete.gpx")
    gpxmerge_command = f'gpxmerge {" ".join(gpx_files)} -o {output_file}'
    subprocess.run(gpxmerge_command, shell=True, cwd="./")
    print("Merged files in folder:", folder_path)

    # Verschieben der zusammengeführten Datei in den merged_folder
    merged_filepath = os.path.join(merged_folder, os.path.basename(output_file))
    shutil.move(output_file, merged_filepath)
    print("Moved merged file to:", merged_filepath)


# ==================== 2006-FIX FUNCTIONS ====================

def get_latest_date_from_file(gpx_file, debug_verbose=False):
    """Findet das späteste Datum in einer GPX-Datei"""
    print(f"[DEBUG] Scanning file: {gpx_file}")
    latest_date = None
    all_dates = []
    
    with open(gpx_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Finde alle <time> Tags
        time_tags = re.findall(r'<time>(.*?)</time>', content)
        
        print(f"[DEBUG] Found {len(time_tags)} timestamps in {os.path.basename(gpx_file)}")
        
        # EXTENDED DEBUG: Zeige die ersten 10 Timestamps
        if debug_verbose and len(time_tags) > 0:
            print(f"[DEBUG] === First 10 raw timestamps found in file ===")
            for i, time_str in enumerate(time_tags[:10]):
                print(f"[DEBUG]   [{i+1}] RAW: {time_str}")
        
        for time_str in time_tags:
            try:
                timestamp = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
                all_dates.append(timestamp)
                if latest_date is None or timestamp > latest_date:
                    latest_date = timestamp
            except ValueError:
                print(f"[WARNING] Could not parse timestamp: {time_str}")
        
        # EXTENDED DEBUG: Zeige alle gefundenen Jahre
        if debug_verbose and all_dates:
            years = set(d.year for d in all_dates)
            print(f"[DEBUG] === Years found in file: {sorted(years)} ===")
            print(f"[DEBUG] === Earliest timestamp: {min(all_dates).strftime('%d/%m/%Y %H:%M:%S')} ===")
            print(f"[DEBUG] === Latest timestamp: {max(all_dates).strftime('%d/%m/%Y %H:%M:%S')} ===")
    
    if latest_date:
        print(f"[DEBUG] Latest date in {os.path.basename(gpx_file)}: {latest_date.strftime('%d/%m/%Y %H:%M:%S')}")
    
    return latest_date


def find_newest_file(output_folder):
    """Findet die Datei mit dem spätesten Datum"""
    print("\n[DEBUG] === Starting search for newest file ===")
    gpx_files = glob.glob(os.path.join(output_folder, '*.gpx'))
    
    if not gpx_files:
        print("[ERROR] No GPX files found in output folder!")
        return None, None
    
    print(f"[DEBUG] Found {len(gpx_files)} GPX files to scan")
    
    newest_file = None
    newest_date = None
    
    for gpx_file in gpx_files:
        # Aktiviere verbose debugging nur für die erste Datei
        is_first = (newest_file is None)
        latest_date = get_latest_date_from_file(gpx_file, debug_verbose=is_first)
        if latest_date and (newest_date is None or latest_date > newest_date):
            newest_date = latest_date
            newest_file = gpx_file
    
    if newest_file:
        print(f"\n[DEBUG] === Newest file found: {os.path.basename(newest_file)} ===")
        print(f"[DEBUG] === Date: {newest_date.strftime('%d/%m/%Y %H:%M:%S')} ===")
        
        # SUPER DETAILED DEBUG für die neueste Datei
        print(f"\n[DEBUG] === DETAILED ANALYSIS of newest file ===")
        get_latest_date_from_file(newest_file, debug_verbose=True)
        print()
    
    return newest_file, newest_date


def fix_timestamps_in_file(input_file, output_file, date_offset_days):
    """Korrigiert alle Timestamps in einer Datei"""
    print(f"[DEBUG] Processing file: {os.path.basename(input_file)}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Finde alle <time> Tags und ersetze sie
    time_tags = re.findall(r'<time>(.*?)</time>', content)
    timestamps_fixed = 0
    
    for old_time_str in time_tags:
        try:
            old_timestamp = datetime.strptime(old_time_str, '%Y-%m-%dT%H:%M:%SZ')
            # Nur Datum ändern, Uhrzeit bleibt gleich
            new_timestamp = old_timestamp + timedelta(days=date_offset_days)
            new_time_str = new_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            content = content.replace(f'<time>{old_time_str}</time>', f'<time>{new_time_str}</time>', 1)
            timestamps_fixed += 1
            
            if timestamps_fixed == 1:  # Nur den ersten Timestamp loggen
                print(f"[DEBUG]   First timestamp: {old_timestamp.strftime('%d/%m/%Y %H:%M:%S')} -> {new_timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        
        except ValueError:
            print(f"[WARNING] Could not parse timestamp: {old_time_str}")
    
    # Schreibe die korrigierte Datei
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[DEBUG]   Fixed {timestamps_fixed} timestamps")
    return timestamps_fixed


def apply_2006_fix(output_folder):
    """Hauptfunktion für den 2006-Fix"""
    print("\n" + "="*60)
    print("=== 2006-FIX MODE ===")
    print("="*60)
    
    # Finde die neueste Datei
    newest_file, newest_date = find_newest_file(output_folder)
    
    if not newest_file or not newest_date:
        print("[ERROR] Could not find any valid GPX files with timestamps!")
        return
    
    # Zeige dem User das neueste Datum
    print(f"\nNeuste Datei: {os.path.basename(newest_file)}")
    print(f"Datum in Datei: {newest_date.strftime('%d/%m/%Y')}")
    print(f"Uhrzeit in Datei: {newest_date.strftime('%H:%M:%S')}")
    
    # Frage nach dem korrekten Datum
    while True:
        correct_date_str = input("\nAn welchem Tag wurde diese Datei aufgezeichnet? (Format: DD/MM/YYYY): ").strip()
        try:
            correct_date = datetime.strptime(correct_date_str, '%d/%m/%Y')
            # Behalte die Uhrzeit vom Original
            correct_datetime = correct_date.replace(hour=newest_date.hour, minute=newest_date.minute, second=newest_date.second)
            break
        except ValueError:
            print("[ERROR] Ungültiges Datumsformat! Bitte verwende DD/MM/YYYY (z.B. 13/11/2025)")
    
    # Berechne die Differenz in Tagen
    date_offset = (correct_datetime.date() - newest_date.date()).days
    print(f"\n[DEBUG] Calculated date offset: {date_offset} days")
    print(f"[DEBUG] Old date: {newest_date.strftime('%d/%m/%Y')}")
    print(f"[DEBUG] New date: {correct_datetime.strftime('%d/%m/%Y')}")
    
    # Erstelle output_fixed Ordner
    fixed_folder = "./output_fixed/"
    if not os.path.exists(fixed_folder):
        os.makedirs(fixed_folder)
        print(f"\n[DEBUG] Created folder: {fixed_folder}")
    
    # Verarbeite alle GPX-Dateien
    gpx_files = glob.glob(os.path.join(output_folder, '*.gpx'))
    print(f"\n[DEBUG] Processing {len(gpx_files)} files...")
    print("\n" + "-"*60)
    
    total_timestamps = 0
    for gpx_file in gpx_files:
        filename = os.path.basename(gpx_file)
        output_file = os.path.join(fixed_folder, filename)
        
        # Hole das alte Datum für den Log
        old_date = get_latest_date_from_file(gpx_file)
        
        # Fixe die Timestamps
        fixed_count = fix_timestamps_in_file(gpx_file, output_file, date_offset)
        total_timestamps += fixed_count
        
        if old_date:
            new_date = old_date + timedelta(days=date_offset)
            print(f"✓ {filename}: {old_date.strftime('%d/%m/%Y')} -> {new_date.strftime('%d/%m/%Y')}")
        else:
            print(f"✓ {filename}: processed")
    
    print("-"*60)
    print(f"\n[SUCCESS] 2006-Fix complete!")
    print(f"[SUCCESS] Processed {len(gpx_files)} files")
    print(f"[SUCCESS] Fixed {total_timestamps} total timestamps")
    print(f"[SUCCESS] Fixed files saved to: {fixed_folder}")
    print("="*60 + "\n")


# ==================== MAIN SCRIPT ====================

conv = Converter()
fit_folder = "./input/"
gpx_folder = "./tmp/"
merged_folder = "./output/"

create_folders(fit_folder, gpx_folder, merged_folder)
gpx = conv.fit_to_gpx_bulk(dir_in=fit_folder, dir_out=gpx_folder)
print(".fit to .gpx DONE")

rename_gpx_files(gpx_folder, merged_folder)
print("Naming DONE")

merge_gpx_files(gpx_folder, merged_folder)
print("Combining DONE")

# Frage ob 2006-Fix angewendet werden soll
print("\n" + "="*60)
apply_fix = input("Möchtest du den 2006-Fix anwenden? (j/n): ").strip().lower()

if apply_fix in ['j', 'ja', 'y', 'yes']:
    apply_2006_fix(merged_folder)
else:
    print("2006-Fix übersprungen.")
    print("="*60 + "\n")

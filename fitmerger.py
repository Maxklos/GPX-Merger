from fit2gpx import Converter
import os
import glob
from datetime import datetime
import shutil
import subprocess


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

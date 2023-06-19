from fit2gpx import Converter
import os
import glob
from datetime import datetime
import subprocess

def rename_gpx_files(gpx_folder):
    gpx_files = glob.glob(os.path.join(gpx_folder, '*.gpx'))
    suffix = 1
    for gpx_file in gpx_files:
        with open(gpx_file, 'r') as f:
            lines = f.readlines()
            timestamp_str = next((line.strip().replace('<time>', '').replace('</time>', '') for line in lines if '<time>' in line), None)
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                print("Incorrect timestamp format for file:", gpx_file)
                continue
            new_filename = timestamp.strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
            suffix += 1
            new_filepath = os.path.join(gpx_folder, new_filename)
            while os.path.exists(new_filepath):
                new_filename = timestamp.strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
                new_filepath = os.path.join(gpx_folder, new_filename)
                suffix += 1
            os.rename(gpx_file, new_filepath)
            print("Renamed file:", gpx_file, "to", new_filepath)
        else:
            print("No timestamp found in file:", gpx_file)

def merge_gpx_files(gpx_folder):
    gpx_files = [file for file in os.listdir(gpx_folder) if file.endswith(".gpx")]
    if gpx_files:
        first_file = gpx_files[0]
        max_length = 10
        shortened_name = first_file[:max_length]
        output_file = f"{shortened_name}-merged.gpx"
        print("Output file:", output_file)
    else:
        print("No GPX files found.")
        return

    print("GPX files:", " ".join(gpx_files))
    command = f'gpxmerge {" ".join(gpx_files)} -o {output_file}'
    subprocess.run(command, shell=True, cwd=gpx_folder)
    print("Merge DONE")
    command = f'mv {output_file} ..'
    subprocess.run(command, shell=True, cwd=gpx_folder)
    print("Move DONE")
    command = f'rm {" ".join(gpx_files)}'
    subprocess.run(command, shell=True, cwd=gpx_folder)
    print("Delete DONE")

conv = Converter()
fit_folder = "./input/"
gpx_folder = "./tmp/"

gpx = conv.fit_to_gpx_bulk(dir_in=fit_folder, dir_out=gpx_folder)
print(".fit to .gpx DONE")
rename_gpx_files(gpx_folder)
print("Naming DONE")
merge_gpx_files(gpx_folder)
print("Combining DONE")

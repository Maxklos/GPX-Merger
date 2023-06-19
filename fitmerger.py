from fit2gpx import Converter
import os
import glob
from datetime import datetime
import subprocess

def rename_gpx_files(gpx_folder):
    # Get all .gpx files in the specified folder
    gpx_files = glob.glob(os.path.join(gpx_folder, '*.gpx'))
    suffix = 1
    for gpx_file in gpx_files:
        # Open the .gpx file and extract the first timestamp
        with open(gpx_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if '<time>' in line:
                    timestamp_str = line.strip().replace('<time>', '').replace('</time>', '')
                    break
            else:
                print("no timestamp found")
                continue  # Skip to the next file if no timestamp found

        # Convert the timestamp string to a datetime object
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            print("timestamp format is incorrect")
            continue  # Skip to the next file if the timestamp format is incorrect

        # Generate the new filename based on the date of the first timestamp
        
        new_filename = timestamp.strftime('%Y-%m-%d')+ '-' + str(suffix) + '.gpx'
        suffix += 1
        new_filepath = os.path.join(gpx_folder, new_filename)

        # Check if a file with the same name already exists
        if os.path.exists(new_filepath):
            # Find the next available filename by adding a suffix
            suffix = 1
            while True:
                new_filename = strftime('%Y-%m-%d') + '-' + str(suffix) + '.gpx'
                new_filepath = os.path.join(gpx_folder, new_filename)
                if not os.path.exists(new_filepath):
                    break
                suffix += 1

        # Rename the file to the new filename
        os.rename(gpx_file, new_filepath)
        print("Renamed file:", gpx_file, "to", new_filepath)

def merge_gpx_files(gpx_folder):
    #This function searches for GPX files in the folder, extracts the first file's name, shortens it to a maximum length of 10 characters, and creates an output file name by combining the shortened name with "-merged.gpx". It then executes commands using the subprocess module to merge the selected GPX files into the output file and delete the merged files. The function provides feedback on the output file name and completion of the merge and delete operations.

    gpx_files = ""
    for file in os.listdir(gpx_folder):
        if file.endswith(".gpx"):
            gpx_files += file + " "

    gpx_files_list = gpx_files.split()
    if gpx_files_list:
        first_file = gpx_files_list[0]
        max_length = 10
        shortened_name = first_file[:max_length]

        output_file = f"{shortened_name}-merged.gpx"
        print("Output file:", output_file)

    print("GPX files:", gpx_files)

    command = f'gpxmerge {gpx_files} -o {output_file}'
    subprocess.run(command, shell=True, cwd=gpx_folder)
    print("Merge DONE")
    command = f'mv {output_file} ..'
    subprocess.run(command, shell=True, cwd=gpx_folder)
    print("Move DONE")
    command = f'rm {gpx_files}'
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
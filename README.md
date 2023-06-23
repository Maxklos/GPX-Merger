# GPX-Merger

Programm to convert .fit files to .gpx and the combining them to one file.

## How to Use

Place your .fit files in the input folder. If you don't have the necesary folder, the script will generate them for you.

Run the script fitmerger.py using the following command:

        python3 fitmerger.py

The script will perform the following actions:

- Convert the .fit files in the input folder to .gpx files in the tmp folder.
- Rename the .gpx files based on their timestamps and move them to subfolders in the tmp folder.
- Merge the .gpx files in each subfolder and move the merged file to the output folder.

## Installation

Clone the repository to your local machine:

        git clone https://github.com/Maxklos/GPX-Merger

Change into the project directory:

        cd GPX-Merger

Install the dependencies:

        pip install fit2gpx
        pip install gpx-cmd-tools

Run the script as described in the "How to Use" section.

## Note

Make sure you have the gpxmerge command available in your system's PATH. You can check by running gpxmerge --version in the terminal. If the command is not found, you may need to install it or provide the full path to the gpxmerge executable in the script.

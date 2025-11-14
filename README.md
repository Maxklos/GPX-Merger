# GPX-Merger

A Python tool to convert .fit files to .gpx format and intelligently merge them by date. Includes an automatic timestamp correction feature for devices with the 2006 year bug.

## Features

- 🔄 **Batch FIT to GPX conversion** with progress tracking
- 📅 **Automatic date-based grouping** and merging of activities
- 🔧 **2006 Year Bug Fix** - Automatically detects and corrects timestamp errors
- 🎯 **Smart outlier detection** - Ignores corrupted timestamps
- 📊 **Clean progress bars** for all operations
- 🐛 **Debug mode** for troubleshooting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Maxklos/GPX-Merger
cd GPX-Merger
```

2. Install dependencies:
```bash
pip install fit2gpx tqdm --break-system-packages
pip install gpx-cmd-tools --break-system-packages
```

**Note:** Make sure `gpxmerge` is available in your PATH. Test with `gpxmerge --version`.

## How to Use

### Basic Usage

1. Place your .fit files in the `input/` folder (will be created automatically if missing)
2. Run the script:
```bash
python3 fitmerger.py
```

The script will:
- ✅ Convert all .fit files to .gpx format
- ✅ Rename and organize files by date
- ✅ Merge activities from the same day
- ✅ Automatically detect if timestamp correction is needed

### Debug Mode

For detailed output and troubleshooting, use the debug flag:
```bash
python3 fitmerger.py --debug
# or short form:
python3 fitmerger.py --d
```

This will show:
- Detailed timestamp analysis
- Year distribution in files
- Outlier detection information
- File operation details

## 2006 Year Bug Fix

### What is it?

Some GPS devices (like Lezyne Y10, Super GPS, Micro C GPS, and Micro C Watch GPS) have a known firmware bug that causes recordings to be timestamped with dates from 2006 instead of the correct year.

**Read more:** [Lezyne Support Article - 2006 Year Issue](https://support.lezyne.com/hc/en-us/articles/40301799398811-2006-Year-Issue-for-Y10-Super-GPS-Micro-C-GPS-and-Micro-C-Watch-GPS)

### How the Fix Works

1. **Automatic Detection**: The script automatically checks if any timestamps are older than 1 year
2. **Smart Analysis**: Identifies the most recent file and ignores outlier timestamps
3. **User Correction**: Asks you to provide the correct date for the newest activity
4. **Batch Processing**: Automatically calculates the offset and fixes all files
5. **Renamed Output**: Creates corrected files with proper dates in `output_fixed/`

### Example

```
⚠️  Old timestamps detected (older than 1 year)
Möchtest du den 2006-Fix anwenden? (j/n): j

Neuste Datei: 2006-03-30-complete.gpx
Datum in Datei: 30/03/2006
Uhrzeit in Datei: 15:17:56

An welchem Tag wurde diese Datei aufgezeichnet? (Format: DD/MM/YYYY): 13/11/2025

Processing 31 files...
Fixing timestamps: [████████████████] 100% 31/31

✓ 2006-Fix complete!
✓ Fixed files saved to: ./output_fixed/
```

## Output Structure

```
GPX-Merger/
├── input/              # Place your .fit files here
├── tmp/                # Temporary conversion files (auto-deleted)
├── output/             # Merged GPX files by date
└── output_fixed/       # Timestamp-corrected files (if 2006-fix was used)
```

### Output Filenames

- `YYYY-MM-DD-complete.gpx` - Multiple activities merged from the same day
- `YYYY-MM-DD-single.gpx` - Single activity for that day

## Changelog

### v2.0 (November 2024)
- ✨ **NEW:** Added automatic 2006 timestamp bug detection and correction
- ✨ **NEW:** Smart outlier detection for corrupted timestamps
- ✨ **NEW:** Progress bars for all operations (converting, renaming, merging, fixing)
- ✨ **NEW:** `--debug` / `--d` flag for detailed output
- 🎨 Improved visual feedback with clean, modern progress indicators
- 🎨 Cleaner output - debug messages only shown when requested
- 🔧 Fixed filename handling for timestamp-corrected files
- 📝 Improved error messages and user guidance

### v1.0 (Initial Release)
- Basic FIT to GPX conversion
- Date-based file merging
- Simple console output

## Troubleshooting

**Problem:** "Output file must be a .gpx file" error
- **Solution:** Make sure you're using the latest version of the script

**Problem:** Progress bar shows 100% instantly but nothing happens
- **Solution:** Check with `--debug` flag to see detailed error messages

**Problem:** Files not merging correctly
- **Solution:** Ensure `gpxmerge` is installed: `pip install gpx-cmd-tools --break-system-packages`

**Problem:** Timestamps still wrong after fix
- **Solution:** Check that you entered the correct date in DD/MM/YYYY format

## Requirements

- Python 3.6+
- fit2gpx
- gpx-cmd-tools (provides `gpxmerge`)
- tqdm (for progress bars)

## License

MIT License - see LICENSE file for details

## Contributing

Issues and pull requests are welcome! Please feel free to contribute improvements.

---

**Made with ❤️ for cyclists and outdoor enthusiasts dealing with GPS device quirks**

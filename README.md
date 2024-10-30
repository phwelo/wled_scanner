# WLED Scanner

A Python-based tool to discover WLED devices on the network and bookmark them directly into Firefox for easy access. This tool leverages mDNS to locate WLED devices and automatically saves their URLs as bookmarks in Firefox's `places.sqlite` file.

## Features

- **WLED Device Discovery**: Uses Zeroconf/mDNS to scan and locate WLED devices on the network.
- **Firefox Bookmarking**: Automatically bookmarks found devices into Firefox under a designated folder.
- **Interactive Profile Selection**: If multiple Firefox profiles are detected, lets you choose the profile for bookmarking.
- **Automated Backup and Restore**: Creates a backup of Firefox’s `places.sqlite` before modifying it, with options to restore the added bookmarks.

## Requirements

- Python 3.6+
- Firefox
- `fzf` for interactive profile selection (optional but recommended)

### Python Packages

Install required Python packages:

```bash
pip install zeroconf halo colorama
```

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone git@github.com:phwelo/wled_scanner.git
cd wled_scanner
```

## Usage

### Scanning and Bookmarking WLED Devices

To scan for WLED devices on the network and bookmark them in Firefox:

```bash
python3 bookmark.py --duration 30
```

This command will:

1. Scan for 30 seconds for devices.
2. Search for the Firefox profile’s `places.sqlite` file.
   - If multiple profiles are found, you'll be prompted to select one using `fzf`.
3. Add bookmarks under the folder `LED Strips` in Firefox.

### Options

- `--restore`: Restores previously added bookmarks by removing them from Firefox.
- `--duration`: Sets the scan duration (in seconds).
- `--output`: Specifies the output JSON file for discovered services (default: `discovered_services.json`).
- `--profile-path`: Manually specify the path to `places.sqlite` instead of using automatic detection.

Example with custom options:

```bash
python3 bookmark.py --duration 60 --output custom_discovered_services.json
```

### Restoring Bookmarks

To remove the bookmarks added by this tool, use the `--restore` flag:

```bash
python3 bookmark.py --restore
```

## Configuration

The scanner is configured to ignore certain paths, such as:

- `.thunderbird`
- `Old` (for backup or older profile data)
- `.wine`
- `TorBrowser`

This helps focus on current Firefox profiles. You can adjust these exclusions by modifying `EXCLUDED_PATH_KEYWORDS` in `bookmark.py`.

## Troubleshooting

1. **No `places.sqlite` Found**: Ensure that Firefox is installed and that profiles are available in `~/.mozilla/firefox`.
2. **Permission Issues**: Run the script with appropriate permissions to access the Firefox profile directories.
3. **Profile Not Detected**: Use `--profile-path` to manually specify the profile path if automatic detection fails.

## License

This project is licensed under the MIT License.

#!/usr/bin/env python3

import os
import sys
import shutil
import json
import sqlite3
import argparse
from datetime import datetime
from subprocess import Popen, PIPE

# Import the perform_scan function from scan.py
from scan import perform_scan

# Constants
BOOKMARKS_RECORD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookmarks_added.json')

# Initialize colorama
from colorama import init, Fore, Style
init(autoreset=True)

EXCLUDED_PATH_KEYWORDS = ["Old", ".thunderbird", ".wine", "TorBrowser"]

def find_places_sqlite():
    """
    Search for places.sqlite files in Firefox profile directory, 
    filtering out unwanted paths. If multiple are found, use fzf to let the user select one.
    """
    search_dir = os.path.expanduser("~/")
    places_paths = []

    # Walk through the Firefox profiles directory and look for places.sqlite
    for root, _, files in os.walk(search_dir):
        if "places.sqlite" in files:
            path = os.path.join(root, "places.sqlite")
            # Exclude paths containing any keywords from EXCLUDED_PATH_KEYWORDS
            if any(keyword in path for keyword in EXCLUDED_PATH_KEYWORDS):
                continue
            places_paths.append(path)

    # No places.sqlite found
    if not places_paths:
        print(f"{Fore.RED}{Style.BRIGHT}No valid places.sqlite file found in '{search_dir}'.{Style.RESET_ALL}")
        sys.exit(1)

    # If only one profile is found, use it
    if len(places_paths) == 1:
        print(f"{Fore.GREEN}{Style.BRIGHT}Found places.sqlite at '{places_paths[0]}'{Style.RESET_ALL}")
        return places_paths[0]

    # If multiple profiles are found, use fzf to select one
    print(f"{Fore.YELLOW}{Style.BRIGHT}Multiple Firefox profiles found.{Style.RESET_ALL}")
    print("Use fzf to select the appropriate profile.")
    fzf = Popen(['fzf'], stdin=PIPE, stdout=PIPE)
    fzf_input = "\n".join(places_paths).encode("utf-8")
    selected, _ = fzf.communicate(input=fzf_input)

    if fzf.returncode != 0:
        print(f"{Fore.RED}{Style.BRIGHT}No selection made. Exiting.{Style.RESET_ALL}")
        sys.exit(1)

    selected_path = selected.decode("utf-8").strip()
    print(f"{Fore.GREEN}{Style.BRIGHT}Selected places.sqlite: {selected_path}{Style.RESET_ALL}")
    return selected_path

def backup_places_db(places_db_path):
    """
    Backup the places.sqlite database.
    """
    backup_db = os.path.join(os.path.dirname(places_db_path), 'places_backup.sqlite')
    if not os.path.exists(backup_db):
        try:
            shutil.copy2(places_db_path, backup_db)
            print(f"{Fore.GREEN}{Style.BRIGHT}Backup created at '{backup_db}'.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Failed to create backup: {e}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"{Fore.YELLOW}{Style.BRIGHT}Backup already exists at '{backup_db}'.{Style.RESET_ALL}")

def get_parent_folder_id(cursor, parent_title="LED Strips"):
    """
    Retrieve the parent folder's ID based on its title.
    Create the folder if it doesn't exist.
    """
    try:
        # Attempt to find the parent folder
        cursor.execute("""
            SELECT moz_bookmarks.id FROM moz_bookmarks
            JOIN moz_bookmarks_roots ON moz_bookmarks.id = moz_bookmarks_roots.folder_id
            WHERE moz_bookmarks.title = ?
        """, (parent_title,))
        parent = cursor.fetchone()
        if parent:
            return parent[0]
        else:
            # If parent folder not found, create it under Bookmarks Menu (id=1)
            cursor.execute("""
                INSERT INTO moz_bookmarks (type, fk, parent, position, title, dateAdded, lastModified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                2,          # type: 2 signifies a folder
                None,       # fk: null for folders
                1,          # parent: Bookmarks Menu ID (usually 1)
                0,          # position
                parent_title,
                int(datetime.utcnow().timestamp() * 1000000),
                int(datetime.utcnow().timestamp() * 1000000)
            ))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error accessing parent folder: {e}{Style.RESET_ALL}")
        sys.exit(1)

def add_bookmark(db_path, title, url, parent_id):
    """
    Add a bookmark to Firefox's places.sqlite database.

    Returns:
        A dictionary with bookmark details if added successfully, else None.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    bookmark_details = None

    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION;')

        # Check if the URL already exists in moz_places
        cursor.execute("SELECT id FROM moz_places WHERE url = ?", (url,))
        place = cursor.fetchone()
        if place:
            place_id = place[0]
        else:
            # Insert into moz_places
            cursor.execute("""
                INSERT INTO moz_places (url, title, rev_host)
                VALUES (?, ?, ?)
            """, (url, title, url.split("://")[-1]))
            place_id = cursor.lastrowid

        # Determine the position for the new bookmark
        cursor.execute("""
            SELECT MAX(position) FROM moz_bookmarks
            WHERE parent = ?
        """, (parent_id,))
        max_position = cursor.fetchone()[0]
        position = (max_position + 1) if max_position is not None else 0

        # Get the current timestamp in microseconds since epoch
        timestamp = int(datetime.utcnow().timestamp() * 1000000)

        # Insert into moz_bookmarks
        cursor.execute("""
            INSERT INTO moz_bookmarks (type, fk, parent, position, title, dateAdded, lastModified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            1,          # type: 1 signifies a bookmark
            place_id,   # fk: foreign key to moz_places.id
            parent_id,  # parent folder's id
            position,   # position within the parent folder
            title,      # title of the bookmark
            timestamp,  # dateAdded
            timestamp   # lastModified
        ))

        bookmark_id = cursor.lastrowid

        # Commit transaction
        conn.commit()
        print(f"{Fore.GREEN}{Style.BRIGHT}Bookmark '{title}' added successfully.{Style.RESET_ALL}")

        bookmark_details = {
            'id': bookmark_id,
            'title': title,
            'url': url,
            'parent_id': parent_id,
            'dateAdded': timestamp,
            'lastModified': timestamp
        }

    except sqlite3.Error as e:
        # Rollback in case of any error
        conn.rollback()
        print(f"{Fore.RED}{Style.BRIGHT}An error occurred while adding bookmark '{title}': {e}{Style.RESET_ALL}")
    finally:
        conn.close()

    return bookmark_details

def main():
    parser = argparse.ArgumentParser(description="Bookmark LED Strips discovered by scan.py in Firefox.")
    parser.add_argument('--restore', action='store_true', help='Restore bookmarks by removing those added by this script.')
    parser.add_argument('--duration', type=int, default=30, help='Discovery duration in seconds.')
    parser.add_argument('--output', type=str, default='discovered_services.json', help='Output JSON file from scan.py')
    parser.add_argument('--profile-path', type=str, help='Path to Firefox places.sqlite')
    args = parser.parse_args()

    # Determine the places.sqlite path
    places_db = args.profile_path or find_places_sqlite()

    # Backup the database
    backup_places_db(places_db)

    # Perform service discovery using scan.py's perform_scan
    print(f"{Fore.CYAN}{Style.BRIGHT}Starting LED strips discovery for {args.duration} seconds...{Style.RESET_ALL}")
    services = perform_scan(args.duration, args.output)

    if not services:
        print(f"{Fore.YELLOW}{Style.BRIGHT}No LED strips found during discovery.{Style.RESET_ALL}")
        sys.exit(0)

    # Output JSON
    output = {
        'discovered_services': services
    }
    json_output = json.dumps(output, indent=2)
    print(f"{Fore.BLUE}{Style.BRIGHT}\nFinal JSON Output:{Style.RESET_ALL}")
    print(json_output)

    # Save JSON to a file
    json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    try:
        with open(json_file, 'w') as f:
            f.write(json_output)
        print(f"{Fore.GREEN}{Style.BRIGHT}Discovered services saved to '{json_file}'.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Failed to save discovered services: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Duplicate File Finder and Remover

This script is organized as follows:

1. Argument Parsing: Parses user input from the command line.
2. File Utilities: Functions for file operations (e.g., recursive file listing, checksum calculation).
3. Checksum Management:
   - Loading and saving checksums to files.
   - Calculating checksums for directories.
4. Duplicate Analysis: Identifies duplicate files between directories or within a single directory.
5. Output Handling: Displays or saves duplicate summaries as tables.
6. Duplicate Deletion: Manages the deletion process for identified duplicate files.
7. Main Orchestration: Executes script functionality based on user commands.

Modules are designed for clarity and reusability, making it easy to extend functionality.
"""

import argparse
import fnmatch
import os
import time
from collections import defaultdict

import xxhash
from termcolor import colored
from texttable import Texttable


def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="🔍 Duplicate File Finder and Remover")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--base-dir", required=True, help="Base directory containing files to process"
    )
    common_parser.add_argument(
        "--max-width",
        type=int,
        default=128,
        help="Set maximum width for table columns. Default: 128",
    )
    common_parser.add_argument(
        "--checksum-file",
        default="checksums.txt",
        help="Checksum info file to read from or write to. Default: checksums.txt",
    )

    # Mutually exclusive group for --skip-existing
    skip_group = common_parser.add_mutually_exclusive_group()
    skip_group.add_argument(
        "--skip-existing",
        action="store_true",
        dest="skip_existing",
        default=False,
        help="Skip checksum calculation for files already in the checksum file. Default: False.",
    )
    skip_group.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Do not skip checksum calculation for existing files.",
    )

    # Mutually exclusive group for --verbose
    verbose_group = common_parser.add_mutually_exclusive_group()
    verbose_group.add_argument(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Enable verbose output. Default: False.",
    )
    verbose_group.add_argument(
        "--no-verbose",
        action="store_false",
        dest="verbose",
        help="Disable verbose output.",
    )

    # Mutually exclusive group for --print-table
    print_table_group = common_parser.add_mutually_exclusive_group()
    print_table_group.add_argument(
        "--print-table",
        action="store_true",
        dest="print_table",
        default=False,
        help="Print the duplicate files table to console. Default: False.",
    )
    print_table_group.add_argument(
        "--no-print-table",
        action="store_false",
        dest="print_table",
        help="Do not print the duplicate files table to console.",
    )

    common_parser.add_argument(
        "--output-file",
        default="dupfiles.txt",
        help="File to save the duplicate files table. Default: dupfiles.txt",
    )

    common_parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help='Exclude files matching these patterns (e.g., "*.jpg", "a*.png"). Supports multiple patterns.',
    )

    # Subparser for the 'search' command
    search_parser = subparsers.add_parser(
        "search",
        parents=[common_parser],
        help="🔎 Search for duplicate files between two directories without saving checksum information",
    )
    search_parser.add_argument("path", help="Path to search for duplicates")

    # Subparser for the 'checksum' command
    checksum_parser = subparsers.add_parser(
        "checksum",
        parents=[common_parser],
        help="🧮 Calculate checksums, find duplicates between two directories, and save checksum information to a file",
    )
    checksum_parser.add_argument("path", help="Path to scan for duplicates")

    # Mutually exclusive group for --update-checksum-file
    update_group = checksum_parser.add_mutually_exclusive_group()
    update_group.add_argument(
        "--update-checksum-file",
        action="store_true",
        dest="update_checksum_file",
        default=True,
        help="Save checksum information (default)",
    )
    update_group.add_argument(
        "--no-update-checksum-file",
        action="store_false",
        dest="update_checksum_file",
        help="Do not save checksum information",
    )

    # Subparser for the 'delete' command
    delete_parser = subparsers.add_parser(
        "delete",
        parents=[common_parser],
        help="🗑️ Delete duplicate files between two directories based on checksum info file",
    )
    delete_parser.add_argument("path", help="Path to delete duplicates from")
    delete_parser.add_argument(
        "--sleep-time",
        type=float,
        default=1.0,
        help="Time to sleep between deletions (seconds). Default: 1",
    )

    # Mutually exclusive group for --confirm
    confirm_group = delete_parser.add_mutually_exclusive_group()
    confirm_group.add_argument(
        "--confirm",
        action="store_true",
        dest="confirm",
        default=True,
        help="Enable confirmation before deletion (default)",
    )
    confirm_group.add_argument(
        "--no-confirm",
        action="store_false",
        dest="confirm",
        help="Disable confirmation before deletion",
    )

    delete_parser.add_argument(
        "--list-next",
        type=int,
        default=5,
        help="Number of next files to list before confirmation. Default: 5",
    )

    # Subparser for the 'dedup' command
    dedup_parser = subparsers.add_parser(
        "dedup",
        parents=[common_parser],
        help="🔄 Identify and remove duplicates within a single directory",
    )

    # Mutually exclusive group for --update-checksum-file in 'dedup' command
    update_group = dedup_parser.add_mutually_exclusive_group()
    update_group.add_argument(
        "--update-checksum-file",
        action="store_true",
        dest="update_checksum_file",
        default=True,
        help="Save checksum information (default)",
    )
    update_group.add_argument(
        "--no-update-checksum-file",
        action="store_false",
        dest="update_checksum_file",
        help="Do not save checksum information",
    )

    # Mutually exclusive group for --confirm in 'dedup' command
    confirm_group = dedup_parser.add_mutually_exclusive_group()
    confirm_group.add_argument(
        "--confirm",
        action="store_true",
        dest="confirm",
        default=True,
        help="Enable confirmation before deletion (default)",
    )
    confirm_group.add_argument(
        "--no-confirm",
        action="store_false",
        dest="confirm",
        help="Disable confirmation before deletion",
    )

    dedup_parser.add_argument(
        "--sleep-time",
        type=float,
        default=1.0,
        help="Time to sleep between deletions (seconds). Default: 1",
    )
    dedup_parser.add_argument(
        "--list-next",
        type=int,
        default=5,
        help="Number of next files to list before confirmation. Default: 5",
    )

    return parser.parse_args()


def compute_xxhash64(file_path):
    """
    Compute the xxhash64 checksum of a file.
    """
    hasher = xxhash.xxh64()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_all_files(path, exclude_patterns=[]):
    """
    Recursively get all files under the given path, excluding files that match the exclude patterns.
    """
    file_list = []
    for root, _, files in os.walk(path):
        for file in files:
            exclude = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(file, pattern):
                    exclude = True
                    break
            if exclude:
                continue
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list


def load_existing_checksums(checksum_file):
    """
    Load existing checksums from the checksum file.
    Returns a dictionary with structure:
    {
        'BASE': { 'relative_path': 'checksum', ... },
        'OTHER': { 'relative_path': 'checksum', ... }
    }
    """
    existing_checksums = {"BASE": {}, "OTHER": {}}
    with open(checksum_file, "r") as f:
        for line in f:
            category, checksum, path = line.strip().split("\t")
            existing_checksums[category][path] = checksum
    return existing_checksums


def calculate_checksums(
    base_dir, other_dir, checksum_file, skip_existing, verbose, exclude_patterns
):
    """
    Calculate checksums for files in base_dir and other_dir.
    If skip_existing is True, skip files already present in checksum_file.
    """
    base_checksums = {}
    other_checksums = {}
    existing_checksums = {}

    # Load existing checksums if skip_existing is True
    if skip_existing and os.path.exists(checksum_file):
        existing_checksums = load_existing_checksums(checksum_file)

    # Get all files in base_dir
    base_files = get_all_files(base_dir, exclude_patterns)
    total_base_files = len(base_files)
    print(f"📁 Processing files in base directory '{base_dir}': {total_base_files}")

    # Calculate checksums for base_dir files
    for idx, file_path in enumerate(base_files, start=1):
        rel_path = os.path.relpath(file_path, base_dir)
        abs_path = os.path.abspath(file_path)

        if skip_existing and rel_path in existing_checksums.get("BASE", {}):
            checksum = existing_checksums["BASE"][rel_path]
            if verbose:
                print(
                    f"⚡ Skipping checksum calculation for {rel_path}, using existing checksum."
                )
        else:
            if verbose:
                print(f"⏳ Processing base ({idx}/{total_base_files}): {abs_path}")
            checksum = compute_xxhash64(file_path)

        base_checksums[checksum] = {"path": rel_path, "abs_path": abs_path}

    # Get all files in other_dir
    other_files = get_all_files(other_dir, exclude_patterns)
    total_other_files = len(other_files)
    print(
        f"\n📁 Processing files in other directory '{other_dir}': {total_other_files}"
    )

    # Calculate checksums for other_dir files
    for idx, file_path in enumerate(other_files, start=1):
        rel_path = os.path.relpath(file_path, other_dir)
        abs_path = os.path.abspath(file_path)

        if skip_existing and rel_path in existing_checksums.get("OTHER", {}):
            checksum = existing_checksums["OTHER"][rel_path]
            if verbose:
                print(
                    f"⚡ Skipping checksum calculation for {rel_path}, using existing checksum."
                )
        else:
            if verbose:
                print(f"⏳ Processing other ({idx}/{total_other_files}): {abs_path}")
            checksum = compute_xxhash64(file_path)

        # Save checksum for all files in other_dir
        other_checksums[checksum] = {"path": rel_path, "abs_path": abs_path}

    return base_checksums, other_checksums, total_base_files, total_other_files


def save_checksums(base_checksums, other_checksums, checksum_file):
    """
    Save checksum information to a file.
    """
    try:
        with open(checksum_file, "w") as f:
            # Save base checksums
            for checksum, info in base_checksums.items():
                f.write(f"BASE\t{checksum}\t{info['path']}\n")
            # Save other checksums
            for checksum, info in other_checksums.items():
                f.write(f"OTHER\t{checksum}\t{info['path']}\n")
        print(colored(f"✅ Checksums saved to {checksum_file}", "green"))
    except Exception as e:
        print(colored(f"❌ Error saving checksums to {checksum_file}: {e}", "red"))


def load_checksums(checksum_file):
    """
    Load checksum information from a file.
    """
    base_checksums = {}
    other_checksums = defaultdict(list)
    try:
        with open(checksum_file, "r") as f:
            for line in f:
                category, checksum, path = line.strip().split("\t")
                if category == "BASE":
                    base_checksums[checksum] = {"path": path}
                elif category == "OTHER":
                    other_checksums[checksum].append({"path": path})
    except Exception as e:
        print(
            colored(
                f"❌ Error loading checksums from {checksum_file}, have you performed checksum command to generate checksums.txt? \n   {e}.",
                "red",
            )
        )
    return base_checksums, other_checksums


def summarize_duplicates(base_checksums, other_checksums, base_dir, other_dir):
    """
    Summarize duplicate files and count files under each directory.
    """
    duplicates = {}
    for checksum, info_list in other_checksums.items():
        if checksum in base_checksums:
            duplicates[checksum] = {
                "base": base_checksums[checksum],
                "duplicates": info_list,  # info_list is already a list
            }

    # Count total files
    total_base_files = len(base_checksums)
    total_other_files = sum(len(v) for v in other_checksums.values())

    return duplicates, total_base_files, total_other_files


def display_summary(
    duplicates,
    base_dir,
    other_dir,
    total_base_files,
    total_other_files,
    max_width=0,
    output_file=None,
    print_table=False,
):
    """
    Display summary of duplicate files.
    """
    print(
        colored(
            f"\n✅ Total files in base directory '{base_dir}': {total_base_files}",
            "green",
        )
    )
    print(
        colored(
            f"✅ Total files in directory '{other_dir}': {total_other_files}",
            "green",
        )
    )

    total_duplicates = sum(len(info["duplicates"]) for info in duplicates.values())
    print(colored(f"⚠️  Total duplicate files found: {total_duplicates}", "yellow"))

    total_unique_files_in_other_dir = total_other_files - total_duplicates
    print(
        colored(
            f"📁 Total unique files in '{other_dir}': {total_unique_files_in_other_dir}",
            "green",
        )
    )

    # Prepare data for tabular display
    table_data = []
    for info in duplicates.values():
        base_path = info["base"]["path"]
        duplicate_paths = "\n".join([dup["path"] for dup in info["duplicates"]])
        table_data.append([base_path, duplicate_paths])

    if table_data:
        # Use Texttable for better alignment with wide characters
        table = Texttable(max_width=0)
        table.set_deco(Texttable.HEADER | Texttable.VLINES | Texttable.HLINES)
        table.set_cols_align(["l", "l"])
        table.set_cols_valign(["m", "m"])
        table.set_cols_dtype(["t", "t"])

        # Set the max width for columns if specified
        if max_width > 0:
            table.set_cols_width([max_width, max_width])

        table.add_rows([["Base File", "Duplicate Files"]] + table_data)

        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write(table.draw())
                print(
                    colored(f"✅ Duplicate files table saved to {output_file}", "green")
                )
            except Exception as e:
                print(
                    colored(
                        f"❌ Error saving duplicate files table to {output_file}: {e}",
                        "red",
                    )
                )

        if print_table:
            print("\n🗂️ Duplicate Files:")
            print(table.draw())
    else:
        print(colored("🎉 No duplicates identified.", "green"))


def delete_duplicates(duplicates, base_dir, other_dir, sleep_time, confirm, list_next):
    """
    Delete duplicate files from other_dir based on checksum info.
    """
    total_deleted = 0
    files_to_delete = []

    # Collect files to delete
    for info in duplicates.values():
        for file_info in info["duplicates"]:
            files_to_delete.append(
                {"checksum": "", "base": info["base"], "duplicate": file_info}
            )

    total_files = len(files_to_delete)
    print(f"\n🗑️  Total duplicate files to delete: {total_files}")

    # If confirmation is enabled
    if confirm:
        sleep_time = 0  # Omit sleep-time if confirmation is needed
        print(colored("⚠️  Confirmation is enabled. Sleep time is set to 0.", "yellow"))

        skip_count = 0
        idx = 0
        while idx < total_files:
            item = files_to_delete[idx]
            duplicate_info = item["duplicate"]
            base_info = item["base"]
            duplicate_path = os.path.abspath(
                os.path.join(other_dir, duplicate_info["path"])
            )
            base_path = os.path.abspath(os.path.join(base_dir, base_info["path"]))
            files_left = total_files - idx

            # List next files to be deleted
            print("\n📄 Next files to be deleted:")
            for j in range(idx, min(idx + list_next, total_files)):
                next_item = files_to_delete[j]
                print(
                    f"{j+1}. Duplicate: {os.path.abspath(os.path.join(other_dir, next_item['duplicate']['path']))}"
                )
                print(
                    f"   Base File: {os.path.abspath(os.path.join(base_dir, next_item['base']['path']))}"
                )

            # Ask for confirmation
            user_input = (
                input("\nProceed with deletion? (y/n/y<number>/n<number>/yall/nall): ")
                .strip()
                .lower()
            )

            if user_input == "y":
                skip_count = 0
                pass  # Proceed to delete the current file
            elif user_input == "n":
                print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                idx += 1  # Skip current file
                continue
            elif user_input.startswith("y") and user_input[1:].isdigit():
                skip_count = int(user_input[1:]) - 1
            elif user_input.startswith("n") and user_input[1:].isdigit():
                num_to_skip = int(user_input[1:])
                for _ in range(num_to_skip):
                    if idx >= total_files:
                        break
                    item = files_to_delete[idx]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(other_dir, duplicate_info["path"])
                    )
                    print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                    idx += 1
                continue
            elif user_input == "yall":
                skip_count = total_files - idx - 1
            elif user_input == "nall":
                print("Operation cancelled by user.")
                # Print the files being skipped
                for i in range(idx, total_files):
                    item = files_to_delete[i]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(other_dir, duplicate_info["path"])
                    )
                    print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                break
            else:
                print("Invalid input. Please try again.")
                continue

            # Delete the current file
            if os.path.exists(duplicate_path):
                try:
                    os.remove(duplicate_path)
                    print(
                        colored(f"🗑️  Deleted duplicate file: {duplicate_path}", "red")
                    )
                    total_deleted += 1
                except Exception as e:
                    print(
                        colored(f"❌ Error deleting file {duplicate_path}: {e}", "red")
                    )
            else:
                print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))

            idx += 1
            if skip_count > 0:
                for _ in range(skip_count):
                    idx += 1
                    if idx >= total_files:
                        break
                    item = files_to_delete[idx]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(other_dir, duplicate_info["path"])
                    )
                    # Proceed to delete the file without confirmation
                    if os.path.exists(duplicate_path):
                        try:
                            os.remove(duplicate_path)
                            print(
                                colored(
                                    f"🗑️  Deleted duplicate file: {duplicate_path}",
                                    "red",
                                )
                            )
                            total_deleted += 1
                        except Exception as e:
                            print(
                                colored(
                                    f"❌ Error deleting file {duplicate_path}: {e}",
                                    "red",
                                )
                            )
                    else:
                        print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))
                skip_count = 0
    else:
        # If sleep_time is 0, give a warning and wait for confirmation
        if sleep_time == 0:
            print(
                colored(
                    "⚠️  Warning: Sleep time is set to 0. Deletions will occur rapidly!",
                    "red",
                )
            )
            confirm_input = input("Are you sure you want to continue? (yes/no): ")
            if confirm_input.lower() != "yes":
                print("Operation cancelled by user.")
                return

        # Process deletions without confirmation
        for idx, item in enumerate(files_to_delete, start=1):
            duplicate_info = item["duplicate"]
            base_info = item["base"]
            duplicate_path = os.path.abspath(
                os.path.join(other_dir, duplicate_info["path"])
            )
            base_path = os.path.abspath(os.path.join(base_dir, base_info["path"]))
            files_left = total_files - idx

            print(f"\n⏳ Deleting ({idx}/{total_files}): {duplicate_path}")
            print(f"🔗 Base file: {base_path}")
            print(f"📊 Files left to delete: {files_left}")

            if os.path.exists(duplicate_path):
                try:
                    os.remove(duplicate_path)
                    print(
                        colored(f"🗑️  Deleted duplicate file: {duplicate_path}", "red")
                    )
                    total_deleted += 1
                except Exception as e:
                    print(
                        colored(f"❌ Error deleting file {duplicate_path}: {e}", "red")
                    )
            else:
                print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))

            if files_left > 0 and sleep_time > 0:
                time.sleep(sleep_time)

    print(colored(f"\n✅ Total duplicate files deleted: {total_deleted}", "green"))
    print(
        colored(
            "\n🔄 Reminder: Please run the 'checksum' command to generate a checksum file with the latest information.",
            "yellow",
        )
    )


def calculate_checksums_single_dir(
    directory, checksum_file, skip_existing, verbose, exclude_patterns
):
    """
    Calculate checksums for files within a single directory to identify duplicates.
    If skip_existing is True, skip files already present in checksum_file.
    """
    checksums = {}
    existing_checksums = {}

    # Load existing checksums if skip_existing is True
    if skip_existing and os.path.exists(checksum_file):
        existing_checksums = load_existing_checksums_single_dir(checksum_file)

    # Get all files in the directory
    files = get_all_files(directory, exclude_patterns)
    total_files = len(files)
    print(f"📁 Processing files in directory '{directory}': {total_files}")

    # Calculate checksums for files
    for idx, file_path in enumerate(files, start=1):
        rel_path = os.path.relpath(file_path, directory)
        abs_path = os.path.abspath(file_path)

        if skip_existing and rel_path in existing_checksums:
            checksum = existing_checksums[rel_path]
            if verbose:
                print(
                    f"⚡ Skipping checksum calculation for {rel_path}, using existing checksum."
                )
        else:
            if verbose:
                print(f"⏳ Processing ({idx}/{total_files}): {abs_path}")
            checksum = compute_xxhash64(file_path)

        if checksum in checksums:
            checksums[checksum]["duplicates"].append(
                {"path": rel_path, "abs_path": abs_path}
            )
        else:
            checksums[checksum] = {
                "original": {"path": rel_path, "abs_path": abs_path},
                "duplicates": [],
            }

    return checksums, total_files


def load_existing_checksums_single_dir(checksum_file):
    """
    Load existing checksums from the checksum file for single directory deduplication.
    Returns a dictionary with relative_path as key and checksum as value.
    """
    existing_checksums = {}
    with open(checksum_file, "r") as f:
        for line in f:
            checksum, path = line.strip().split("\t")
            existing_checksums[path] = checksum
    return existing_checksums


def save_checksums_single_dir(checksums, checksum_file):
    """
    Save checksum information to a file for single directory deduplication.
    """
    try:
        with open(checksum_file, "w") as f:
            for checksum, info in checksums.items():
                original = info["original"]
                f.write(f"{checksum}\t{original['path']}\n")
                for dup in info["duplicates"]:
                    f.write(f"{checksum}\t{dup['path']}\n")
        print(colored(f"✅ Checksums saved to {checksum_file}", "green"))
    except Exception as e:
        print(colored(f"❌ Error saving checksums to {checksum_file}: {e}", "red"))


def summarize_duplicates_single_dir(checksums):
    """
    Summarize duplicate files within a single directory.
    """
    duplicates = {}
    for checksum, info in checksums.items():
        if info["duplicates"]:
            duplicates[checksum] = info
    total_files = sum(1 + len(info["duplicates"]) for info in checksums.values())
    return duplicates, total_files


def display_summary_single_dir(
    duplicates,
    directory,
    total_files,
    max_width=0,
    output_file=None,
    print_table=False,
):
    """
    Display summary of duplicate files within a single directory.
    """
    print(
        colored(
            f"\n✅ Total files in directory '{directory}': {total_files}",
            "green",
        )
    )

    total_duplicates = sum(len(info["duplicates"]) for info in duplicates.values())
    print(colored(f"⚠️  Total duplicate files found: {total_duplicates}", "yellow"))

    total_unique_files = total_files - total_duplicates
    print(
        colored(
            f"📁 Total unique files in '{directory}': {total_unique_files}",
            "green",
        )
    )

    # Prepare data for tabular display
    table_data = []
    for info in duplicates.values():
        original_path = info["original"]["path"]
        duplicate_paths = "\n".join([dup["path"] for dup in info["duplicates"]])
        table_data.append([original_path, duplicate_paths])

    if table_data:
        # Use Texttable for better alignment with wide characters
        table = Texttable(max_width=0)
        table.set_deco(Texttable.HEADER | Texttable.VLINES | Texttable.HLINES)
        table.set_cols_align(["l", "l"])
        table.set_cols_valign(["m", "m"])
        table.set_cols_dtype(["t", "t"])

        # Set the max width for columns if specified
        if max_width > 0:
            table.set_cols_width([max_width, max_width])

        table.add_rows([["Original File", "Duplicate Files"]] + table_data)

        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write(table.draw())
                print(
                    colored(f"✅ Duplicate files table saved to {output_file}", "green")
                )
            except Exception as e:
                print(
                    colored(
                        f"❌ Error saving duplicate files table to {output_file}: {e}",
                        "red",
                    )
                )

        if print_table:
            print("\n🗂️ Duplicate Files:")
            print(table.draw())
    else:
        print(colored("🎉 No duplicates identified.", "green"))


def delete_duplicates_single_dir(duplicates, directory, sleep_time, confirm, list_next):
    """
    Delete duplicate files within a single directory based on checksum info.
    """
    total_deleted = 0
    files_to_delete = []

    # Collect files to delete
    for checksum_info in duplicates.values():
        for file_info in checksum_info["duplicates"]:
            files_to_delete.append(
                {"original": checksum_info["original"], "duplicate": file_info}
            )

    total_files = len(files_to_delete)
    print(f"\n🗑️  Total duplicate files to delete: {total_files}")

    # If confirmation is enabled
    if confirm:
        sleep_time = 0  # Omit sleep-time if confirmation is needed
        print(colored("⚠️  Confirmation is enabled. Sleep time is set to 0.", "yellow"))

        skip_count = 0
        idx = 0
        while idx < total_files:
            item = files_to_delete[idx]
            duplicate_info = item["duplicate"]
            original_info = item["original"]
            duplicate_path = os.path.abspath(
                os.path.join(directory, duplicate_info["path"])
            )
            original_path = os.path.abspath(
                os.path.join(directory, original_info["path"])
            )
            files_left = total_files - idx

            # List next files to be deleted
            print("\n📄 Next files to be deleted:")
            for j in range(idx, min(idx + list_next, total_files)):
                next_item = files_to_delete[j]
                dup_path = os.path.abspath(
                    os.path.join(directory, next_item["duplicate"]["path"])
                )
                orig_path = os.path.abspath(
                    os.path.join(directory, next_item["original"]["path"])
                )
                print(f"{j+1}. Duplicate: {dup_path}")
                print(f"   Original File: {orig_path}")

            # Ask for confirmation
            user_input = (
                input("\nProceed with deletion? (y/n/y<number>/n<number>/yall/nall): ")
                .strip()
                .lower()
            )

            if user_input == "y":
                skip_count = 0
                pass  # Proceed to delete the current file
            elif user_input == "n":
                print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                idx += 1  # Skip current file
                continue
            elif user_input.startswith("y") and user_input[1:].isdigit():
                skip_count = int(user_input[1:]) - 1
            elif user_input.startswith("n") and user_input[1:].isdigit():
                num_to_skip = int(user_input[1:])
                for _ in range(num_to_skip):
                    if idx >= total_files:
                        break
                    item = files_to_delete[idx]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(directory, duplicate_info["path"])
                    )
                    print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                    idx += 1
                continue
            elif user_input == "yall":
                skip_count = total_files - idx - 1
            elif user_input == "nall":
                print("Operation cancelled by user.")
                # Print the files being skipped
                for i in range(idx, total_files):
                    item = files_to_delete[i]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(directory, duplicate_info["path"])
                    )
                    print(colored(f"🚫 Skipping file: {duplicate_path}", "yellow"))
                break
            else:
                print("Invalid input. Please try again.")
                continue

            # Delete the current file
            if os.path.exists(duplicate_path):
                try:
                    os.remove(duplicate_path)
                    print(
                        colored(f"🗑️  Deleted duplicate file: {duplicate_path}", "red")
                    )
                    total_deleted += 1
                except Exception as e:
                    print(
                        colored(f"❌ Error deleting file {duplicate_path}: {e}", "red")
                    )
            else:
                print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))

            idx += 1
            if skip_count > 0:
                for _ in range(skip_count):
                    idx += 1
                    if idx >= total_files:
                        break
                    item = files_to_delete[idx]
                    duplicate_info = item["duplicate"]
                    duplicate_path = os.path.abspath(
                        os.path.join(directory, duplicate_info["path"])
                    )
                    # Proceed to delete the file without confirmation
                    if os.path.exists(duplicate_path):
                        try:
                            os.remove(duplicate_path)
                            print(
                                colored(
                                    f"🗑️  Deleted duplicate file: {duplicate_path}",
                                    "red",
                                )
                            )
                            total_deleted += 1
                        except Exception as e:
                            print(
                                colored(
                                    f"❌ Error deleting file {duplicate_path}: {e}",
                                    "red",
                                )
                            )
                    else:
                        print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))
                skip_count = 0
    else:
        # If sleep_time is 0, give a warning and wait for confirmation
        if sleep_time == 0:
            print(
                colored(
                    "⚠️  Warning: Sleep time is set to 0. Deletions will occur rapidly!",
                    "red",
                )
            )
            confirm_input = input("Are you sure you want to continue? (yes/no): ")
            if confirm_input.lower() != "yes":
                print("Operation cancelled by user.")
                return

        # Process deletions without confirmation
        for idx, item in enumerate(files_to_delete, start=1):
            duplicate_info = item["duplicate"]
            original_info = item["original"]
            duplicate_path = os.path.abspath(
                os.path.join(directory, duplicate_info["path"])
            )
            original_path = os.path.abspath(
                os.path.join(directory, original_info["path"])
            )
            files_left = total_files - idx

            print(f"\n⏳ Deleting ({idx}/{total_files}): {duplicate_path}")
            print(f"🔗 Original file: {original_path}")
            print(f"📊 Files left to delete: {files_left}")

            if os.path.exists(duplicate_path):
                try:
                    os.remove(duplicate_path)
                    print(
                        colored(f"🗑️  Deleted duplicate file: {duplicate_path}", "red")
                    )
                    total_deleted += 1
                except Exception as e:
                    print(
                        colored(f"❌ Error deleting file {duplicate_path}: {e}", "red")
                    )
            else:
                print(colored(f"⚠️  File not found: {duplicate_path}", "yellow"))

            if files_left > 0 and sleep_time > 0:
                time.sleep(sleep_time)

    print(colored(f"\n✅ Total duplicate files deleted: {total_deleted}", "green"))
    print(
        colored(
            "\n🔄 Reminder: Please run the 'dedup' command with '--update-checksum-file' to generate a checksum file with the latest information.",
            "yellow",
        )
    )


def main():
    """
    Main function to orchestrate the script's functionality.
    """
    args = parse_arguments()
    base_dir = os.path.abspath(args.base_dir)

    if args.command == "search" or args.command == "checksum":
        target_dir = os.path.abspath(args.path)
        # Calculate checksums and find duplicates
        base_checksums, other_checksums, total_base_files, total_other_files = (
            calculate_checksums(
                base_dir,
                target_dir,
                args.checksum_file,
                args.skip_existing,
                args.verbose,
                args.exclude,
            )
        )

        duplicates, _, _ = summarize_duplicates(
            base_checksums, other_checksums, base_dir, target_dir
        )

        if args.command == "checksum":
            if args.update_checksum_file:
                # Save checksums to file
                save_checksums(base_checksums, other_checksums, args.checksum_file)
            else:
                print(
                    colored(
                        "\n⚠️  Note: Checksums are not saved because '--no-update-checksum-file' was specified.",
                        "yellow",
                    )
                )
        else:
            print(
                colored(
                    "\n⚠️  Note: Checksums are not saved because '--update-checksum-file' only available under 'checksum' command.",
                    "yellow",
                )
            )

        # Display summary
        display_summary(
            duplicates,
            base_dir,
            target_dir,
            total_base_files,
            total_other_files,
            args.max_width,
            args.output_file,
            args.print_table,
        )

    elif args.command == "delete":
        target_dir = os.path.abspath(args.path)
        # Load checksums from file
        base_checksums, other_checksums = load_checksums(args.checksum_file)
        duplicates, _, _ = summarize_duplicates(
            base_checksums, other_checksums, base_dir, target_dir
        )

        # Delete duplicates
        delete_duplicates(
            duplicates,
            base_dir,
            target_dir,
            args.sleep_time,
            args.confirm,
            args.list_next,
        )

    elif args.command == "dedup":
        # Calculate checksums and find duplicates within base_dir
        checksums, total_files = calculate_checksums_single_dir(
            base_dir,
            args.checksum_file,
            args.skip_existing,
            args.verbose,
            args.exclude,
        )

        duplicates, _ = summarize_duplicates_single_dir(checksums)

        if args.update_checksum_file:
            # Save checksums to file
            save_checksums_single_dir(checksums, args.checksum_file)
        else:
            print(
                colored(
                    "\n⚠️  Note: Checksums are not saved because '--no-update-checksum-file' was specified.",
                    "yellow",
                )
            )

        # Display summary
        display_summary_single_dir(
            duplicates,
            base_dir,
            total_files,
            args.max_width,
            args.output_file,
            args.print_table,
        )

        # Delete duplicates if any
        if duplicates:
            delete_duplicates_single_dir(
                duplicates,
                base_dir,
                args.sleep_time,
                args.confirm,
                args.list_next,
            )
    else:
        print(colored("❌ Please provide a valid command. Use -h for help.", "red"))


if __name__ == "__main__":
    main()

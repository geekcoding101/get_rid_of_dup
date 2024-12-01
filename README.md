# 🗂️ get_rid_of_dup.py: Eliminate Duplicate Files with Ease!

`get_rid_of_dup.py` is a command-line tool designed to find and remove duplicate files efficiently using checksum comparisons. Whether you're searching, managing, or deleting duplicate files, this script has got you covered! 💾

---

## 🚀 Features
- **`search`**: Locate duplicate files without saving checksum information.
- **`checksum`**: Everything in `search`, plus saving checksums into file.
- **`delete`**: Remove duplicate files based on checksum data.

---

## 📜 Commands and Usage

### 🔍 `search` Command
Search for duplicate files by comparing against a base directory.

**Usage:**

```
python get_rid_of_dup.py search [options] <path>
```

**Options:**
- `<path>`: Path to search for duplicates (positional argument).
- `--base-dir`: Base directory containing original files (required).
- See [Common Arguments](#-common-arguments) below.

**Example:**

```
python get_rid_of_dup.py search --base-dir /path/to/base_dir /path/to/other_dir
```

---

### 🔑 `checksum` Command
Calculate checksums and optionally save them to a file while identifying duplicates.

**Usage:**

```
python get_rid_of_dup.py checksum [options] <path>
```

**Options:**
- `<path>`: Path to scan for duplicates (positional argument).
- `--update-checksum-file`: Update the checksum file with new entries.
- `--base-dir`: Base directory containing original files (required).
- See [Common Arguments](#-common-arguments) below.

**Example:**

```
python get_rid_of_dup.py checksum --base-dir /path/to/base_dir --update-checksum-file /path/to/other_dir
```

---

### 🗑️ `delete` Command
Delete duplicate files using checksum information.

**Usage:**

```
python get_rid_of_dup.py delete [options] <path>
```

**Options:**
- `<path>`: Path to delete duplicates from (positional argument).
- `--sleep-time`: Time to wait between deletions (default: 1.0 seconds).
- `--confirm`: Enable confirmation before deletion.
- `--list-next`: Number of files to preview before confirmation (default: 5).
- See [Common Arguments](#-common-arguments) below.

**Example:**

```
python get_rid_of_dup.py delete --base-dir /path/to/base_dir --checksum-file checksums.txt --confirm /path/to/other_dir
```

---

## ⚙️ Common Arguments
These arguments apply to all commands:

- `--base-dir`: **(Required)** Base directory containing original files.
- `--checksum-file`: File to save or read checksum data (default: `checksums.txt`).
- `--skip-existing`: Skip checksum calculations for already-processed files. (default: False).
- `--max-width`: Maximum column width for displaying results (default: 128).
- `--verbose`: Enable verbose output (default: False).
- `--output-file`: Save duplicate files table to a file (default: output.txt).
- `--print-table`: Print the duplicate files table to the console (default: False).

## Command-Specific Options:
- `checksum`: 
  - `--update-checksum-file`: Add new entries to checksum file.
- `delete`: 
  - `--sleep-time`: Set delay between deletions (default: 1).
  - `--confirm`: Enable confirmation prompts (default: True).
  - `--list-next`: Set number of files to preview before confirmation (default: 5).

---

## 💡 Examples
### Search for Duplicates Without Saving Checksums

```
python get_rid_of_dup.py search --base-dir /path/to/base_dir /path/to/other_dir
```

### Calculate and Save Checksums

```
python get_rid_of_dup.py checksum --base-dir /path/to/base_dir --update-checksum-file /path/to/other_dir
```

### Delete Duplicates with Confirmation

```python get_rid_of_dup.py delete --base-dir /path/to/base_dir --confirm --list-next 10 /path/to/other_dir```

### Save Duplicate Files Table to a File

```python get_rid_of_dup.py search --base-dir /path/to/base_dir --output-file duplicates_table.txt /path/to/other_dir```

### Skip Existing Checksums with Verbose Output

```python get_rid_of_dup.py checksum --base-dir /path/to/base_dir --skip-existing --verbose /path/to/other_dir```

---

## 📝 Notes
- Always **back up your data** before deleting files.
- Use `--confirm` with `delete` to review files before removal.
- The `--skip-existing` option speeds up processing for large datasets.
- Enable `--verbose` for detailed progress logs.

---

## ❤️ Contribution & Support
Feel free to fork, contribute, or raise issues on GitHub! Suggestions, bug reports, and stars 🌟 are always welcome. Together, let's declutter your file system!

---

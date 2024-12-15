# 🗂️ get_rid_of_dup.py: Eliminate Duplicate Files with Ease!

`get_rid_of_dup.py` is a command-line tool designed to find and remove duplicate files efficiently using checksum comparisons. Whether you're searching, managing, or deleting duplicate files, this script has got you covered! 💾

This script has three modes:

**Mode 1: Single Directory Duplicate Deletion**

This is only available in `dedup` command.

In this mode, it will identify all duplicates within the same folder and ask confirmation to delete.

One command is enough:

```
python get_rid_of_dup.py dedup --base-dir ./comp --max-width 50 --verbose --exclude "*.DS_Store"
```

**Mode 2: Cross-Directory Duplicate Detection and Deletion**

As the name suggested, it takes two folders as input. Use one as the base directory, means all duplicates will come out from the other directory.

Two steps required:

1. Generate checksums.txt for files from `base-dir` and `./comp` (relative path of the other folder, you can specify your folder path) by using `checksum` option, `./comp ` is the folder duplicates will be addressed and deleted:

```
python get_rid_of_dup.py checksum --base-dir ./base ./comp --max-width 50   --verbose --exclude "*.DS_Store"
```

This command will also generate a file specified by `--output-file` (if not specified, name is `dupfiles.txt`). This is not needed in later step, it's just for your references.

1. Based on `checksums.txt` (in current folder) which generated from above, guide you to delete duplicates:

```
python get_rid_of_dup.py delete --base-dir ./base ./comp --max-width 50   --verbose --exclude "*.DS_Store"
```

**Mode 3: Detecting duplicates by giving checksum of base directory**

The use case is for this scenario:

My laptop has 300GB free space, I want to download 280GB photos which will be used as base directory and 230GB photos where I think it will have duplicates. The free space is not enough to hold all of them.

So I can just download 280GB and use the script to generate checksums.txt, then delete the 280GB files, then download the 230GB files, then script can take the given checksum file at `--base-checksum-file`, and generate a complete checksums.txt based on it and 230GB files.

1. Generate checksum file `./checksums-for-test-12132024-211933.txt`:

```
python get_rid_of_dup.py checksum --generate-checksum-only --base-dir ./test
```

2. I can delete files in ./test now, then run below command to generate `checksums.txt` which have all checksums:

```
python get_rid_of_dup.py checksum --base-checksum-file ./checksums-for-test-12132024-211933.txt ./others
```

3. Now we can use *Mode 2* commands to delete duplicates. Needs to have a folder exists and give it to `--base-dir`, no files needes under the folder:

```
python get_rid_of_dup.py delete  --base-dir ./test ./others --no-confirm --sleep-time 5
```

---

## 🚀 Features

Essentially, both modes are doing the same thing as below:

- **`search`**: Locate duplicate files *WITHOUT* saving checksum information. This is usually for quick test.
- **`checksum`**: Everything in `search`, plus saving checksums into file. This is the first step in **Mode 2: Cross-Directory Duplicate Detection**.
- **`delete`**: Remove duplicate files based on checksum data (Default reading from checksums.txt). This is the second step in **Mode 2: Cross-Directory Duplicate Detection**.
- **`dedup`**: Remove duplicate files from the single directory. This is the **Mode 1: Single Directory Duplicate Deletion**.

---

## 📦 Installation
I am using `Python 3.12.6`, it should work for all `Python 3+` as long as the additional packages installed successfully.

Run the following command to install the dependencies:

```
pip install xxhash termcolor texttable
```

## Considerations

### Determine which file as the original file

In **Mode 1: Single Directory Duplicate Detection**, when hit duplicates, the script will use the file whose file name is shorter as the original file and mark others as the target to be deleted.

The reason why I designed it like this is that, I found usually the duplicates have names like "IMG_5808 (2).JPG". So only the original file has "IMG_5808.JPG" as file name which is shorter.

No need to have such logic in **Mode 2: Cross-Directory Duplicate Detection** because it is designed to use files in `--base-dir` as the original files.

### Performance

The most time consuming is checksum command.

But with `xxhash`, it's fast enough from my perspectiev.

I have around 30k files to scan, including many larger than 20MB images, it took just less than 1min to finish!

Another good thing of this script is that it supports to read checksums.txt file if specified `--skip-existing`.

Let's say you have scanned 10k files and saved in checksums.txt.

Then you added another 10k files, as long as you're in the same path, it will skip calculating whatever already in checksums.txt.

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
python get_rid_of_dup.py search --base-dir ./test ./others --max-width 50
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
python get_rid_of_dup.py checksum --no-update-checksum-file  --base-dir ./test  --max-width 50  ./others
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
python get_rid_of_dup.py delete  --base-dir ./test ./others
```

---

## ⚙️ Common Arguments
These arguments apply to all commands:

- `--checksum-file`: File to save or read checksum data from (default: `checksums.txt`).
- `--verbose`: Enable verbose output (default: False).
- `--no-verbose`: The opposite of `--verbose`.

## Command-Specific Options:
- `checksum`:
  - `--base-checksum-file`: Use a pre-generated checksum file instead of scanning the base directory again.
  - `--generate-checksum-only`: Generate checksums for a base directory without needing a target directory.

- `delete`:

- `delete` and `dedup`:
  - `--list-next`: Set number of files to preview before confirmation (default: 5).
  - `--sleep-time`: Set delay between deletions (default: 1).
  - `--confirm`: Enable confirmation prompts (default: True).
  - `--no-confirm`: The opposite of `--confirm`

- `checksum` and `dedup`:
  - `--update-checksum-file`: Instruct to generate checksums file. Default filename is `checksums.txt`.
  - `--no-update-checksum-file`: The opposite of `--update-checksum-file`.

- `search`, `checksum` and `dedup` because they invoked either `display_summary_single_dir` or `display_summary` and either `calculate_checksums` or `calculate_checksums_single_dir`:

  - `--base-dir`: **(Required)** Base directory containing original files.
  - `--exclude [EXCLUDE ...]`: Exclude files matching these patterns (e.g., "*.jpg", "a*.png"). Supports multiple patterns.
  - `--max-width`: Maximum column width for displaying results (default: 128).
  - `--print-table`: Print the duplicate files table to the console (default: False).
  - `--no-print-table`: The opposite of `--print-table`.
  - `--skip-existing`: Skip checksum calculations for already-processed files. (default: False).
  - `--no-skip-existing`: The opposite of `--skip-existing`.
  - `--output-file OUTPUT_FILE`: Save duplicate files table to a file (default: dupfiles.txt).

---

## 💡 Examples
### *Mode 2:* Search for Duplicates Without Saving Checksums into File

```
python get_rid_of_dup.py search --base-dir ./test ./others --max-width 50
```

![search-basic-usage](asset/img/search-01.webp)

The duplicate files table:

![dupfiles.txt.webp](asset/img/dupfiles.txt.webp)

```
python get_rid_of_dup.py search --base-dir ./test ./others --max-width 50 --verbose
```

![search-basic-usage](asset/img/search-02-with-verbose.webp)

### *Mode 2:* Search for Duplicates and Save Checksum into File

```
python get_rid_of_dup.py checksum --base-dir ./test ./others --max-width 50
```

![checksum-01-save-checksum-default-behavior](asset/img/checksum-01-save-checksum-default-behavior.webp)


```
python get_rid_of_dup.py checksum --no-update-checksum-file --base-dir ./test ./others --max-width 50
```

![checksum-02-not-save-checksum-same-as-search-command](asset/img/checksum-02-not-save-checksum-same-as-search-command.webp)


### *Mode 2:* Delete Duplicates with Confirmation

```
python get_rid_of_dup.py delete  --base-dir ./test ./others
```

![delete-01](asset/img/delete-01.webp)

When missing checksums.txt:

```
python get_rid_of_dup.py delete  --base-dir ./test ./others
```

![delete-02](asset/img/delete-02.webp)


### *Mode 2:* Skip Existing Checksums with Verbose Output

```
python get_rid_of_dup.py checksum --base-dir /path/to/base_dir --skip-existing --verbose /path/to/other_dir
```

### *Mode 1:* Delete Duplicates identified from Single Directory

```
python get_rid_of_dup.py dedup --base-dir ./upload_to_apple_photo  --max-width 125 --verbose --exclude "*.DS_Store"
```

---

## 📝 Notes
- Always **back up your data** before deleting files.
- Use `--confirm` with `delete` to review files before removal.
- The `--skip-existing` option speeds up processing for large datasets.
- Enable `--verbose` for detailed progress logs.

## 📋 TODO

Under `checksum` command: 
- `--base-dir` should not be needed when having `--base-checksum-file`.
- `--exclude` is only being used in `search`, `checksum` and `dedup`. Because they invoked either `calculate_checksums` or `calculate_checksums_single_dir`

---

## ❤️ Contribution & Support
Feel free to fork, contribute, or raise issues on GitHub! Suggestions, bug reports, and stars 🌟 are always welcome. Together, let's declutter your file system!

---

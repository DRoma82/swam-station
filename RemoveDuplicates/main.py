import os
import hashlib
import json
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO)


def hash_file(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing file {filepath}: {e}")
        sys.exit(1)


def process_directory_a(directory):
    hash_dict = {}
    dict_file = os.path.join(directory, 'file_hashes.json')

    # Load existing data if available
    if os.path.exists(dict_file):
        with open(dict_file, 'r') as f:
            hash_dict = json.load(f)

    # Reverse the dictionary for quick lookup
    path_to_hash = {v: k for k, v in hash_dict.items()}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith('.mkv'):
                continue

            file_path = os.path.join(root, file)

            # Skip hashing if the file path is already in the dictionary
            if file_path in path_to_hash:
                continue

            file_hash = hash_file(file_path)
            hash_dict[file_hash] = file_path
            logging.info(f"Hashed {file_path}")

    # Save updated dictionary
    with open(dict_file, 'w') as f:
        json.dump(hash_dict, f)

    return hash_dict


def process_directory_b(directory, hash_dict):
    checked_files_file = os.path.join(directory, 'checked_files.json')
    checked_files = set()

    # Load existing data if available
    if os.path.exists(checked_files_file):
        with open(checked_files_file, 'r') as f:
            checked_files = set(json.load(f))

    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith('.mkv'):
                continue

            file_path = os.path.join(root, file)

            # Check if the file is a hard link
            if os.stat(file_path).st_nlink > 1:
                #logging.info(f"File {file_path} was already a link.")
                continue

            # Skip if the file is already checked and doesn't need a hard link
            if file_path in checked_files:
                #logging.info(f"File {file_path} already checked before. Skipping...")
                continue

            logging.info(f"Hashing file {file_path}")
            file_hash = hash_file(file_path)

            if file_hash and file_hash in hash_dict:
                target_path = hash_dict[file_hash]

                try:
                    os.remove(file_path)
                    os.link(target_path, file_path)
                    logging.info(f"New link created for file {file_path}.")
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {e}")
                    sys.exit(1)
            else:
                # Add the file to checked files list
                logging.info(f"File {file_path} can't be linked")
                checked_files.add(file_path)

    with open(checked_files_file, 'w') as f:
        json.dump(list(checked_files), f)

def main():
    parser = argparse.ArgumentParser(description="Process directories for file deduplication.")
    parser.add_argument("dir_a", type=str, help="Path to directory A")
    parser.add_argument("dir_b", type=str, help="Path to directory B")

    args = parser.parse_args()

    if not os.path.isdir(args.dir_a):
        print(f"Error: {args.dir_a} is not a valid directory.")
        sys.exit(1)

    if not os.path.isdir(args.dir_b):
        print(f"Error: {args.dir_b} is not a valid directory.")
        sys.exit(1)

    hash_dict_a = process_directory_a(args.dir_a)
    process_directory_b(args.dir_b, hash_dict_a)


if __name__ == "__main__":
    main()

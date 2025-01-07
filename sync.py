#!/usr/bin/env python3

import subprocess
import os
import json
import argparse
import sys
import time
from datetime import datetime
import shlex

ORIGINAL_AUDIO = "_Original Audio"
LOG_PATH = "nessie.log"

def check_filename_length(local_dir, remote_dir, max_length=255):
    """Check if the total path length of files within the directory exceeds max_length when combined with remote_dir."""
    find_command = ["find", os.path.normpath(local_dir), "-type", "f"]
    process = subprocess.Popen(find_command, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
    too_long_files = []

    for local_path in process.stdout:
        local_path = local_path.strip()
        normalized_local_path = os.path.normpath(local_path)
        relative_path = os.path.relpath(normalized_local_path, start=os.path.normpath(local_dir))
        full_remote_path = os.path.normpath(os.path.join(remote_dir, relative_path))

        # Convert path to bytes and check the length
        if len(full_remote_path.encode('utf-8')) > max_length:
            too_long_files.append((normalized_local_path, full_remote_path))

    if too_long_files:
        print(f"Error: Found files where total path length exceeds {max_length} bytes on the remote system:")
        for local_path, _ in too_long_files:
            print(local_path)
        return False
    return True

def copy_file_metadata(source_path, target_path):
    stat_info = os.stat(source_path)
    mod_time = stat_info.st_mtime
    acc_time = stat_info.st_atime
    os.utime(target_path, (acc_time, mod_time))
    creation_time = time.strftime('%Y%m%d%H%M.%S', time.localtime(stat_info.st_birthtime))
    subprocess.run(['touch', '-t', creation_time, target_path])

def run_or_simulate(command, dry_run):
    quoted_command = ' '.join(shlex.quote(part) for part in command)
    print(f"{'[DRYRUN] ' if dry_run else '[RUN] '}{quoted_command}")

    if dry_run:
        return True
    else:
        with open(LOG_PATH, 'ab') as log_file:
            process = subprocess.Popen(command, stdout=log_file, stderr=log_file)
            process.communicate()
            return process.returncode == 0

def check_dependencies():
    for dep in ['ffmpeg', 'rsync']:
        if subprocess.call(['command', '-v', dep], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            sys.exit(f"Error: {dep} is not installed.")

def get_sample_rate(filepath):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=sample_rate',
        '-of', 'json',
        filepath
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)
    sample_rate = int(info['streams'][0]['sample_rate'])
    return sample_rate

def compress_top_level_audio(source_dir, dry_run):
    source_dir = os.path.normpath(source_dir)
    new_dir_name = ORIGINAL_AUDIO
    original_wavs_dir = os.path.join(source_dir, new_dir_name)

    if not dry_run:
        os.makedirs(original_wavs_dir, exist_ok=True)

    print("Starting conversion of audio...")
    files_processed = 0
    for file in os.listdir(source_dir):
        filepath = os.path.join(source_dir, file)
        if file.lower().endswith(('.wav', '.aiff', '.m4a')):
            basename = os.path.splitext(file)[0]
            output_path = os.path.join(source_dir, f"{basename}.aac")

            ffmpeg_command = [
                'ffmpeg',
                '-y', # overwrite without prompting
                '-i', filepath,
                '-c:a', 'aac', '-b:a', '320k',
                '-ac', '2',  # Use only the first two channels - MixPre writes 4-ch multiwavs
            ]

            input_sample_rate = get_sample_rate(filepath)

            if input_sample_rate > 48000:
                ffmpeg_command.extend(['-ar', '48000'])

            ffmpeg_command.extend([output_path])

            mv_command = ['mv', filepath, original_wavs_dir]

            if not run_or_simulate(ffmpeg_command, dry_run):
                print(f"Error: ffmpeg failed for file {filepath}")
                return False

            if not dry_run:
                copy_file_metadata(filepath, output_path)

            if not run_or_simulate(mv_command, dry_run):
                print(f"Error: Moving original file failed for {filepath}")
                return False

            files_processed += 1

    if files_processed > 0 or dry_run:
        print(f"Conversion process completed: {files_processed} audio files")
    return True

def rsync_files(remote_rsync_path, source_dir, dest_dir, checksum, dry_run):
    rsync_command = [
        'rsync',
        '-e',
        "ssh -i /Users/bkazez/.ssh/id_ed25519 -o ServerAliveInterval=10",
        '--verbose',
        '--itemize-changes', # Lists changes made during the sync in a detailed format.
        '--update', # Skips files that are newer on the destination.
        f"--rsync-path={remote_rsync_path}", # Specifies the path to the `rsync` executable on the remote system.
        '--archive', # Enables archive mode, preserving symbolic links, permissions, timestamps, etc.
        '--human-readable',
        '--update',
        '--progress', # Displays progress for each file being transferred.
        '--partial', # Allows partially transferred files to be resumed instead of restarting.
        # exclusions
        '--exclude', '.DS_Store',
        '--exclude', 'DS_Store', # erroneously created by hard drive recovery
        '--exclude=*.pkf',
        '--exclude=*.reapeaks',
        '--exclude=' + os.path.join(ORIGINAL_AUDIO) + '/',
        source_dir,
        dest_dir
    ]

    if checksum:
        rsync_command.append('--checksum')
    if dry_run:
        rsync_command.insert(1, '--dry-run')

    return run_or_simulate(rsync_command, False)

def main():
    parser = argparse.ArgumentParser(description="Archive files to NAS")
    parser.add_argument('--dry-run', action='store_true', help="Only print the commands that would be executed")
    args = parser.parse_args()

    check_dependencies()

    config_path = 'config.json'
    if not os.path.exists(config_path):
        sys.exit(f"Configuration file {config_path} not found.")

    with open(config_path) as config_file:
        config = json.load(config_file)

    with open(LOG_PATH, "a") as log_file:
        log_file.write(f"==== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====\n")

    for settings in config.values():
        if settings.get('skip'):
            continue
        local_dir = settings['local']
        remote_dir = settings['remote']

        if not check_filename_length(local_dir, remote_dir):
            sys.exit("Filename length check failed. Exiting.")

        if settings.get('compress_top_level_audio') and not compress_top_level_audio(local_dir, args.dry_run):
            sys.exit(f"Error occurred during audio compression for {local_dir}.")

        # Ensure local_dir has a trailing slash
        # Adding a trailing slash ensures that rsync copies only the contents of the directory
        # instead of copying the directory itself into the destination.
        if not local_dir.endswith('/'):
            local_dir += '/'

        # First, write the files without checksumming.
        # Then, make sure that the above write worked by checksumming.
        for checksum in [False, True]:
            if not rsync_files(settings.get('remote_rsync_path'), local_dir, remote_dir, checksum=checksum, dry_run=args.dry_run):
                sys.exit(f"Error occurred during rsync for {local_dir} to {remote_dir} with checksum={checksum}.")


    print("Archive process completed successfully.")

if __name__ == "__main__":
    main()

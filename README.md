# Nessie Archive Script

## Overview
Script for archiving and converting audio files. Handles "Recordings", "Lessons", and "Misc" directories,
based on config.yml.

## Usage
- Run `./archive_to_nessie.rb` for actual execution.
- Use `./archive_to_nessie.rb --dry-run` for a dry run (no actual changes).

## Features
- Syncs directories to Nessie using rsync.
- Provides progress updates.
- Optionally converts any audio files to MP3 (320kbps, 44.1kHz), leaving originals intact.

## Config
- Edit `config.yml` for directory paths.
- Format: 
  ```
  ArchiveName:
    local: local_path
    remote: remote_path
    convert_to_mp3: [true/false]
  ```
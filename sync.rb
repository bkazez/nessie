#!/usr/bin/env ruby

require 'yaml'
require 'fileutils'

def check_dependencies
  puts "Checking for required dependencies..."
  ['ffmpeg', 'rsync'].each do |dep|
    unless system('command', '-v', dep, out: '/dev/null', err: '/dev/null')
      puts "Error: #{dep} is not installed."
      exit 1
    end
  end
  puts "All dependencies are installed."
end

def convert_lesson_recordings(source_dir, dry_run)
  count = 0
  puts "Starting conversion of lesson recordings..."
  Dir.glob(File.join(source_dir, '*.wav')).each do |file|
    basename = File.basename(file, ".*")
    ffmpeg_command = [
      'ffmpeg',
      '-i', file,
      '-acodec', 'libmp3lame',
      '-ab', '320k',
      '-ar', '44100',
      "#{source_dir}/#{basename}.mp3"
    ]

    if dry_run
      puts "Dry run: Would execute: #{ffmpeg_command.join(' ')}"
    else
      system(*ffmpeg_command)
      puts "Converted: #{file}"
      count += 1
    end
  end
  puts "Conversion process completed. #{count} files converted." if count > 0
  count
end

def rsync_files(source_dir, dest_dir, dry_run)
  puts "Starting rsync for: #{source_dir}"
  rsync_command = [
    'rsync',
    dry_run,
    '--archive',
    '--verbose',
    '--human-readable',
    '--checksum',
    '--progress',
    '--partial',
    source_dir,
    dest_dir
  ]
  system(*rsync_command)
  puts "Rsync completed for: #{source_dir}"
end

# Main script
check_dependencies

config = YAML.load_file('config.yml')
dry_run = ARGV.include?('--dry-run') ? '--dry-run' : ''
total_converted = 0

config.each do |section, settings|
  local_dir = settings['local']
  remote_dir = settings['remote']

  if settings['convert_to_mp3']
    total_converted += convert_lesson_recordings(local_dir, dry_run != '')
  end

  rsync_files(local_dir, remote_dir, dry_run) unless dry_run != ''
end

puts "#{total_converted} files were converted to MP3. Please review and clean up the Lessons/Originals directory." if total_converted > 0
puts "Archive process completed."

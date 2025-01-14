# New process
Fixed IP of Nessie is 192.168.7.50. You can ssh in:

ssh 192.168.7.50

config.json shows which local volumes should be archived where.

You should be able to:

1. Navigate to http://192.168.7.50:5000 or https://finds.synology.com/.
   Get the password with `pass show nessie`.
2. Control Panel > Shared Folder
3. Encryption > Mount > Import Encryption Key > "keys/archives.key"
4. python3 sync.py

# Troubleshooting

If that doesn't work, make sure that Nessie and the Mac are on the same subnet.
Consumer wifi routers will have to be in bridge mode to avoid messing with
this. Or you can plug a switch into the router so that everything is under the
umbrella of the router.

# Nessie backup to S3

See "Cloud Sync" in the DiskStation.

There is a task set to backup to the S3 bucket, backup-nessie.
It is set not to delete files in the dest when they are deleted from the source.
Eventually we can fix that.

# Principles

- When I'm bored, I could indeed take my oldest files and get Logic Pro and render out masters for preservation. But that is a tradeoff of my life vs money, and I should just accept the money spent for now.

- If I've had to move some files to external drives to make room on my Mac,
when I come home I should rsync those files (see command below) back to storage.
To check consistency, I should run this rsync command first without --checksum
and then with. After that, I shouldn't delete the files from external media
but rather should rename the folders with comments like "already transferred
to Nessie."

# Potentially helpful maintenance commands

## Fix erroneously missing trailing slash on source directory

rsync -av --itemize-changes --update \
    --checksum \
    --exclude='/*.m4a' \
    --exclude='@eaDir/**' \
    --exclude='.DS_Store' \
    --exclude='DS_Store' \
    --exclude='*.pkf' \
    --exclude='*.reapeaks' \
    --exclude='_Original Audio/' \
    /volume1/Archives/Recordings/_RecordingsErroneousRsync/ \
    /volume1/Archives/Recordings/

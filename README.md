# New process
Fixed IP of Nessie is 192.168.7.50.

config.json shows which local volumes should be archived where.

`pass show nessie`

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

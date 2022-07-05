# Terminal

## SSH
Recipes for [ssh](https://linux.die.net/man/1/ssh).

### Port forwarding
```bash
ssh -o StrictHostKeyChecking=no -4fNL from-port:target:to-port user@remote-machine
```
Redirect PostegreSQL requests to localhost:5433 to port 5432 on a remote machine.
```bash
ssh -o StrictHostKeyChecking=no -4fNL 5433:localhost:5432 postgres@db-server.net
```

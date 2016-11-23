This fabfile and associated files are for setting up a file/log parser application I put together.

You need to already have pip and Fabric installed on your deployment machine or laptop.  You also need pip installed on your remote hosts since part of the application deployment depends on installing Python package dependencies.

The fabfile is made up of a series of tasks to:
- Clone application repo
- Archive previous application versions
- Install and configure supervisord
- Configure the application to be managed by supervisord
- Run the application

This is still a work in progress and mainly just some place for me to play around.

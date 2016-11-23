#!/usr/bin/python
"""
Test
"""
from fabric.api import *
from fabric.colors import green
from fabric.contrib.files import append
from fabric.contrib.files import contains
from fabric.contrib.files import upload_template
from fabric.context_managers import cd, lcd
from fabtools.user import create, exists
from fabtools import require
from fabtools.python import is_installed, virtualenv, virtualenv_exists
#from fabtools.service import *
from fabtools.files import is_link
from fabtools.files import is_file, is_dir
from fabtools.cron import add_task
from fabtools.supervisor import start_process
from fabtools.supervisor import stop_process
from fabtools.supervisor import reload_config
#import boto3
#import os
#import sys
import time


env.roledefs = {
    "dev" :["192.168.1.48"]
}

# Globals
now = time.strftime("%d%m%Y-%H:%M:%S", time.localtime(time.time()))
app = "router_log_parser"
app_dir = "/opt"
user="logparser"


@task
def clone_repo(gitrepo="https://github.com/hawk1278/router_log_parser.git"):
    """
    clone git repo set most recent pull as current.
    """
    with cd(app_dir):
        sudo("git clone {0}".format(gitrepo))


@task
def setup_app():
    """
    Setup the application
    """
    if not exists(user):
        puts(green("Creating user: {0}".format(user)))
        create(user, comment="logparser applicaiton user", system=True, shell="/sbin/nologin")
    if not is_dir("/var/log/{0}".format(app)):
        with cd("/var/log"):
            require.files.directory(app, owner=user, group=user, use_sudo=True)
    with cd("{0}/{1}".format(app_dir, app)):
        if not virtualenv_exists("{0}_env".format(app)):
            sudo("virtualenv {0}_env".format(app))
        if virtualenv_exists("{0}_env".format(app)):
            with virtualenv("{0}_env".format(app)):
                sudo("pip install -r requirements.txt",)

@task
def config_app(file_to_parse="/var/log/router.log"):
    """
    Config our application
    """
    app_venv = "{0}/{1}/{2}_env/bin/python".format(app_dir, app, app)
    app_bin = "{0}/{1}/{2}.py".format(app_dir, app, app)
    app_command = "{0} {1} -f {2}".format(app_venv, app_bin, file_to_parse)
    logparser_context = {
		      "logpath": "/var/log/router_log_parser/error.log",
		      "errorlogpath": "/var/log/router_log_parser/parser.log",
		      "file_to_parse": file_to_parse,
              "app": app,
              "command": app_command
		      }
    with cd("/etc/supervisor.d"):
        if not is_file("router_log_parser.conf"):
            upload_template("templates/router_log_parser.conf", \
    "/etc/supervisor.d/router_log_parser.conf", \
    context=logparser_context, mode=0700, use_sudo=True)
            sudo("chown supervisor:root router_log_parser.conf")

# Supervisor tasks
@task
def setupsupervisor():
    """
    Setup supervisor on remote host.
    """
    if not is_installed("supervisor"):
        puts(green("Installing supervisor."))
        sudo("pip install supervisor")
    if not exists("supervisor"):
        puts(green("Creating supervisor user"))
        create("supervisor", comment="supervisord user", system=True)
    supervisor_context = {"logpath": "/var/log/supervisord.log"}
    puts(green("Uploading supervisord.conf"))
    upload_template("templates/supervisord.conf", "/etc/supervisord.conf", \
    context=supervisor_context, mode=0700, use_sudo=True)
    texts = ["[include]", "files=/etc/supervisor.d/*.conf"]
    for text in texts:
        if not contains("/etc/supervisord.conf", text, use_sudo=True):
            append("/etc/supervisord.conf", text, use_sudo=True)
    with cd("/etc"):
        if not is_dir("supervisor.d"):
            puts(green("Making supervisor.d configuration directory"))
            sudo("mkdir supervisor.d")
            sudo("chown supervisor:root supervisor.d")
            sudo("chown supervisor:root supervisord.conf")
        with cd("init.d"):
            if not is_file("supervisord"):
                puts(green("Uploading supervisord startup script"))
                put(local_path="files/supervisord", remote_path="/etc/init.d/supervisord", \
                mode=0700, use_sudo=True)
        puts(green("Starting supervisord service"))
        sudo("chkconfig --add supervisord")
        sudo("chkconfig --level 3 supervisord on")
        sudo("service supervisord start")
    with cd("/var/log"):
        if not is_file("supervisord.log"):
            puts(green("Creating supervisor log file"))
            sudo("touch supervisord.log && chown supervisor:root supervisord.log")


@task
def reload_conf():
    """
    Reload supervisor config
    """
    reload_config()


@task
def run_process(process):
    """
    Start supervisor controlled process
    """
    start_process(process)


@task
def end_process(process):
    """
    End supervisor controlled process.
    """
    stop_process(process)


@task
def deploy(repo="https://github.com/hawk1278/router_log_parser.git", \
file_to_parse="/var/log/router.log"):
    """
    Main task to deploy and configure application
    """
    clone_repo(repo)
    setupsupervisor()
    setup_app()
    config_app()
    #run_app()


#!/usr/bin/python
from fabric.api import *
from fabric.colors import red, green, yellow
from fabric.contrib.console import confirm
from fabric.contrib.files import append
from fabtools.user import *
from fabtools.disk import mkfs, mount
from fabtools import require
from fabtools.service import *
from fabtools.files import is_link
from fabtools.cron import add_task
from cuisine import *
import boto3 
import os
import sys
import time

env.roledefs = {
      "dev":["192.168.1.48"]
}

# Globals
now = time.strftime("%d%m%Y-%H:%M:%S", time.localtime(time.time()))
user = "logparser"
app="router_log_parser"
app_dir="/opt"

# User tasks
@task
def add_user():
    puts(green("Creating user: {0}".format(user)))
    user_create(user)
    sudo("passwd {0}".format(user))


# Supervisor tasks
@task
def setupsupervisor():
    require.python.package("supervisor", use_sudo=True)
    if not exists("/etc/supervisor.d"):
        with cd("/etc"):
            require.files.directory("supervisor.d", owner="", group="")
    supervisor_context = { "logpath": "/var/log/supervisord.log" }
    upload_template("templates/supervisor.conf", "/etc/supervisor.conf", context=supervisor_context, mode=0700, use_sudo=True)
    texts=["[include]", "files=/etc/supervisor.d/*.conf"]
    for text in texts:
        if not contains("/etc/supervisor.conf", text, use_sudo=True):
            append("/etc/supervisor.conf", text, use_sudo=True)
    add_task("/usr/bin/supervisord -c /etc/supervisord.conf","@reboot","supervisor")


@task
def setup_app():
    logparser_context = {
		    "logpath": "/var/log/router_log_parser/error.log",
		    "errorlogpath": "/var/log/router_log_parser/parser.log",
		    "file_to_parse": file_to_parse
		    } 
    if not exists("/var/log/{0}".format(app)):
        with cd("/var/log"):
	    require.files.directory(app, owner=user, group=user, use_sudo=True)
    upload_template("templates/router_log_parser.conf","/etc/supervisor.d/router_log_parser.conf", context=logparser(env), mode=0700, use_sudo=True)
    require.python.virtualenv("{0}/{1}/{2}_env".format(app_dir, app, app))
    with virtualenv("{0}/{1}/{2}_env".format(app_dir, app, app)):
        require.python.requirements("{0}/{1}/requirements.txt".format(app_dir, app))


@task
def run_process(p):
    supervisor.start_process(p)

@task
def end_process(p):
    supervisor.stop_process(p)

# Application deployment tasks
@task
def deploy_config(local_config_dir, config_dir, config):
  """
Part of REST API deployment to upload specific supervisor configs
    """
  if exists("{0}/{1}".format(config_dir, config)) is False:
     with lcd(local_config_dir):
       with cd(config_dir):
          put("./{0}".format(config), "./{0}".format(config), use_sudo=True)
          supervisor.reload()

@task 
def clone_repo(gitrepo):
    """
clone git repo set most recent pull as current. 
    """
    with cd(app_dir):
        sudo("git clone {0} {1}".format(gitrepo, now))
	if is_link('current'):
	  sudo("rm -f current")
	  sudo("ln -s {0} current".format(now))
	else:
	  sudo("ln -s {0} current".format(now))
        sudo("chown -R {0} current".format(user))


@task
def deploy():
	add_user()
	clone_repo(repo)
	setupsupervisor()

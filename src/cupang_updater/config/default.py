# flake8: noqa


default_config = """\
#
# *  ██████╗██╗   ██╗██████╗  █████╗ ███╗   ██╗ ██████╗
# * ██╔════╝██║   ██║██╔══██╗██╔══██╗████╗  ██║██╔════╝
# * ██║     ██║   ██║██████╔╝███████║██╔██╗ ██║██║  ███╗
# * ██║     ██║   ██║██╔═══╝ ██╔══██║██║╚██╗██║██║   ██║
# * ╚██████╗╚██████╔╝██║     ██║  ██║██║ ╚████║╚██████╔╝
# *  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝
# *
# * ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗██████╗
# * ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
# * ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  ██████╔╝
# * ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  ██╔══██╗
# * ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗██║  ██║
# *  ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
#
#

last_update:

settings:
  server_folder:
  update_cooldown: 12 # in hour
  keep_removed: true # set to false if you want to remove "removed" plugins in config
  update_order: # top to bottom
updater_settings:
  # If updater have common configuration (i.e. a token) it will be shown here
  server:
  plugin:
server:
  enable: false # true if you want to auto update the server
  file: server.jar
  type: bungee
  version: 1.19.4 # a version number like 1.20.4
  build_number: # if you change server.version, empty this
  custom_url: # only when server.type is set to custom 
  hashes:
    md5:
    sha1:
    sha256:
    sha512:
plugins:
"""


default_plugin = """\
exclude: false # exclude plugin from update checker
file:
version:
authors:
hashes: # auto generated
  md5:
  sha1:
  sha256:
  sha512:
"""

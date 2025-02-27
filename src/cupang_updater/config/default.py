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
  # server_folder can be determinted by one of the following types:
  #
  # - Local:  Use a local file path, e.g., /home/user/minecraft_server
  # - SFTP:   Use an SFTP URL in the format sftp://username:password@example.com:port/home/user/minecraft_server
  #           where 'username' is your SFTP username, 'password' is your SFTP password, 'example.com' is the host,
  #           and 'port' is the connection port (default to 22).
  # - FTP:    Use an FTP URL in the format ftp://username:password@example.com:port/home/user/minecraft_server
  #           where 'username' is your FTP username, 'password' is your FTP password, 'example.com' is the host,
  #           and 'port' is the connection port (default to 21).
  # - SMB:    Use an SMB URL in the format smb://username:password@example.com:port/share/minecraft_server
  #           where 'username' is your SMB username (for Microsoft account use "MicrosoftAccount\\user%40email.com"),
  #           'password' is your SMB password, 'example.com' is the host, and 'port' is the connection port (default to 445).
  #           Note: %40 in the username will be converted to @.
  #                 (e.g., "MicrosoftAccount\\user%40email.com" will be converted to "MicrosoftAccount\\user@email.com")
  # - Webdav: Use an Webdav URL in the format webdav://username:password@example.com:port/home/user/minecraft_server
  #           where 'username' is your Webdav username, 'password' is your Webdav password, 'example.com' is the host,
  #           and 'port' is the connection port (default to 80 for webdav and 443 for webdavs).
  #           Note: There are two schemes: webdav:// (for http) and webdavs:// (for https).
  #           Note 2: The reason for not using http:// or https:// is to make it more explicit.
  server_folder: 
  sftp_key: # path to your SSH private key file (e.g., ~/.ssh/id_rsa), required for SFTP connection
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

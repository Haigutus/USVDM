#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     20.11.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


# OPDM server conf

username = "kvilgo"
server_adress = '10.1.21.50'
key_file_dir = "H:\PROJECTS\OPDE\private_key_12102018_1017.pem"

#read keyfile
private_key = paramiko.RSAKey.from_private_key_file(key_file_dir)

#Set up SSH and SFTP connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(server_adress, username=username, pkey=private_key)
sftp = ssh.open_sftp()
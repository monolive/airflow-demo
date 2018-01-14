#!/usr/bin/env python3

import logging
import paramiko
import hashlib
import datetime
import configparser
import sys
import os

conf_file = '/mnt/conf/sftp.conf'
#conf_file = '/home/orenault/Developments/airflow-demo/docker-files/connect-sftp/sftp-local.conf'

def read_conf(confFile):
    sftpConf = {}
    try:
        with open(confFile, 'r') as conf:
            config = configparser.ConfigParser()
            config.readfp(conf)
            for section_name in config.sections():
                for name, value in config.items(section_name):
                    sftpConf[name] = value
            print
    except IOError:
        print ("ERROR: Can't read conf file!")
        sys.exit(0)
    return sftpConf


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()

def main():
    conf = read_conf(conf_file)
    # initialize paramiko client
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(conf['known_hosts_file'])
    with open(conf['dest_path'] + '/sha256', "a+") as f:
        # initiate connection
        try:
            ssh.connect(conf['hostname'], username=conf['username'], key_filename=conf['ssh_key'], compress=True, look_for_keys=False)
            sftp = ssh.open_sftp()
            sftp.chdir(conf['src_path'])
            for filename in sftp.listdir():
                try:
                    local_file_size = os.stat(conf['dest_path'] + "/" + filename).st_size
                    if local_file_size != sftp.stat(filename).st_size:
                        raise IOError
                except IOError:
                    sftp.get(filename, conf['dest_path'] + "/" + filename)
                    f.write(filename + " " + sha256_checksum(conf['dest_path'] + '/' + filename) + " " + str(datetime.datetime.now()).split('.')[0] + "\n")
                    print(filename)
            ssh.close()
            print('DONE')
        except paramiko.SSHException:
            print('Connection Error')

if __name__ == "__main__":
    main()

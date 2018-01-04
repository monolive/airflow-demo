#!/usr/bin/env python3

import paramiko
import hashlib
import datetime
import ConfigParser

def read_conf(confFile):
  sftpConf = {}
  try:
    with open(confFile, 'r') as conf:
      config = ConfigParser.ConfigParser()
      config.readfp(conf)
      for section_name in config.sections():
        for name, value in config.items(section_name):
          sftpConf[name] = value
    print
  except IOError:
		print ("Can't read conf file!")
  return sftpConf


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()

def main():
    conf = read_conf('/mnt/conf/sftp.conf')
    # initialize paramiko client
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(conf['known_hosts_file'])

    with open(conf['dest_path'] + '/sha256', "a+") as f:
        # initiate connection
        try:
            ssh.connect(conf['hostname'], username=conf['username'], key_filename=conf['ssh_key'], compress=True, look_for_keys=False)
            sftp = ssh.open_sftp()
            sftp.chdir(conf['src_path'])
            #filelist = sftp.listdir()
            for filename in sftp.listdir():
                try:
                    print(sftp.stat(conf['dest_path'] + "/" + filename))
                    print('file exists')
                except IOError:
                    print('copying file')
                    sftp.get(filename, conf['dest_path'] + "/" + filename)
                    f.write(filename + " " + sha256_checksum(conf['dest_path'] + '/' + filename) + " " + str(datetime.datetime.now()).split('.')[0] + "\n")
            ssh.close()
        except paramiko.SSHException:
            print('Connection Error')

if __name__ == "__main__":
    main()

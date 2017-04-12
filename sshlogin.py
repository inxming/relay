#!/usr/bin/env python

import base64
from binascii import hexlify
import os
import socket
import sys
import traceback
import struct, fcntl, signal,termios
import paramiko
from connect import SshTty


install_path=''


def set_win_size(self):
    """
    This function use to set the window size of the terminal!
    """
    try:
        win_size = self.get_win_size()
        self.channel.resize_pty(height=win_size[0], width=win_size[1])
    except Exception:
        pass


class sshlogin(object):

    def __init__(self,ip,port,ldap_user,ssh_user,ssh_pass,login_type):
        self.t=None
        self.ip=ip
        self.port=port
        self.ldap_user=ldap_user
        self.ssh_user=ssh_user
        self.ssh_pass=ssh_pass
        self.login_type=login_type

    @staticmethod
    def get_win_size():
        """
        This function use to get the size of the windows!
        """
        if 'TIOCGWINSZ' in dir(termios):
            TIOCGWINSZ = termios.TIOCGWINSZ
        else:
            TIOCGWINSZ = 1074295912L
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s)
        return struct.unpack('HHHH', x)[0:2]

    def agent_auth(transport, username):
        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        if len(agent_keys) == 0:
            return

        for key in agent_keys:
            print 'Trying ssh-agent key %s' % hexlify(key.get_fingerprint()),
            try:
                transport.auth_publickey(username, key)
                print '... success!'
                return
            except paramiko.SSHException:
                print '... nope.'

    def key_auth(self,t,username, ip, port):
        #key_file = '/data/service/relay/etc/private_key/%s/id_dsa' % (username)
        key_file = install_path+'etc/private_key/%s/id_dsa' % (username)
        key = paramiko.DSSKey.from_private_key_file(key_file)
        # t.load_system_host_keys()
        t.auth_publickey(username, key)

    def ssh_connect(self):
        paramiko.util.log_to_file(install_path+'demo.log')
        # now connect
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.ip,self.port))
        except Exception, e:
            print '*** Connect failed: ' + str(e)
            traceback.print_exc()
            sys.exit(1)

        try:
            t = paramiko.Transport(sock)

            try:
                t.start_client()
            except paramiko.SSHException:
                print '*** SSH negotiation failed.'
                sys.exit(1)

            if self.login_type==0:
                self.key_auth(t,self.ssh_user,self.ip,self.port)
                print ""
            if self.login_type==1:
                t.auth_password(self.ssh_user,self.ssh_pass)
                print ""
            win_size = self.get_win_size()
            ##
            t.set_keepalive(30)
            t.use_compression(True)
            chan = t.open_session()
            chan.get_pty(term='xterm', height=win_size[0], width=win_size[1])
            chan.invoke_shell()
            try:
                signal.signal(signal.SIGWINCH, set_win_size)
            except:
                pass

            print '*** Here we go!'
            print
            ssh = SshTty(chan, self.ip, self.ssh_user, self.ldap_user)
            ssh.input_log('login success|'+ssh.f_log_path)
            ssh.posix_shell()
            ssh.input_log('login exit')
            chan.close()
            t.close()
        except Exception, e:
            print '*** Caught exception: ' + str(e.__class__) + ': ' + str(e)
            traceback.print_exc()
            try:
                t.close()
            except:
                pass
            #sys.exit(1)

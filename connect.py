#!/usr/bin/env python
# coding: utf-8

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import re
import time
import datetime
import MySQLdb
import errno
import pyte
import subprocess
import operator
import struct, fcntl, signal, socket, select


install_path=''

try:
    remote_ip = os.environ.get('SSH_CLIENT').split()[0]
except (IndexError, AttributeError):
    remote_ip = os.popen("who -m | awk '{ print $NF }'").read().strip('()\n')

try:
    import termios
    import tty
except ImportError:
    print '\033[1;31m仅支持类Unix系统 Only unix like supported.\033[0m'
    time.sleep(3)
    sys.exit()


# def color_print(msg, color='red', exits=False):
#     """
#     Print colorful string.
#     颜色打印字符或者退出
#     """
#     color_msg = {'blue': '\033[1;36m%s\033[0m',
#                  'green': '\033[1;32m%s\033[0m',
#                  'yellow': '\033[1;33m%s\033[0m',
#                  'red': '\033[1;31m%s\033[0m',
#                  'title': '\033[30;42m%s\033[0m',
#                  'info': '\033[32m%s\033[0m'}
#     msg = color_msg.get(color, 'red') % msg
#     print msg
#     if exits:
#         time.sleep(2)
#         sys.exit()
#     return msg

class SshTty(object):
    """
    A virtual tty class
    一个虚拟终端类，实现连接ssh和记录日志
    """

    def __init__(self,chan, rip,user,b_user, login_type='ssh'):
        self.ldap_user = b_user
        self.channel = chan
        self.ssh_user = user
        self.server_ip = rip
        self.login_type = login_type
        self.vim_flag = False
        self.vim_end_pattern = re.compile(r'\x1b\[\?1049', re.X)
        self.vim_data = ''
        self.stream = None
        self.screen = None
        self.f_log=None
        self.f_log_path=""
        self.__init_screen_stream()
        self.con = None
        self.__init_db()
        self.__init_logfile()


    def __del__(self):
        self.f_log.close()
        self.con.close()

    def __init_db(self):
        try:
            self.con = MySQLdb.connect(host='127.0.0.1', db='testdb', user='testuser', passwd='testpass', port=3306,
                                       charset="utf8")
            self.con.autocommit(1)
        except Exception, e:
            print "mysql connect error!\n"
            return False
        return True


    def bash(self,cmd):
        return subprocess.call(cmd, shell=True)

    def mkdir(self,dir_name, username='', mode=755):
        cmd = '[ ! -d %s ] && mkdir -p %s && chmod %s %s' % (dir_name, dir_name, mode, dir_name)
        self.bash(cmd)
        if username:
            chown(dir_name, username)

    def __init_logfile(self):
        log_date_dir=install_path+'logs/%s'%(datetime.datetime.now().strftime('%Y-%m-%d'))
        if not os.path.exists(log_date_dir):
            self.mkdir(log_date_dir,mode=777)

        log_dir=log_date_dir+'/%s/'%(self.ldap_user)
        if not os.path.exists(log_dir):
            self.mkdir(log_dir,mode=777)
        log_file='%s.log'%(datetime.datetime.now())
        self.f_log_path=log_dir+log_file
        self.f_log = file(self.f_log_path, 'a+')

    def __init_screen_stream(self):
        """
        初始化虚拟屏幕和字符流
        """
        self.stream = pyte.ByteStream()
        self.screen = pyte.Screen(80, 24)
        self.stream.attach(self.screen)

    @staticmethod
    def is_output(strings):
        newline_char = ['\n', '\r', '\r\n']
        for char in newline_char:
            if char in strings:
                return True
        return False

    @staticmethod
    def command_parser(command):
        """
        处理命令中如果有ps1或者mysql的特殊情况,极端情况下会有ps1和mysql
        :param command:要处理的字符传
        :return:返回去除PS1或者mysql字符串的结果
        """
        result = None
        match = re.compile('\[?.*@.*\]?[\$#]\s').split(command)
        if match:
            # 只需要最后的一个PS1后面的字符串
            result = match[-1].strip()
        else:
            # PS1没找到,查找mysql
            match = re.split('mysql>\s', command)
            if match:
                # 只需要最后一个mysql后面的字符串
                result = match[-1].strip()
        return result

    def deal_command(self, data):
        """
        处理截获的命令
        :param data: 要处理的命令
        :return:返回最后的处理结果
        """
        command = ''
        try:
            self.stream.feed(data)
            # 从虚拟屏幕中获取处理后的数据
            for line in reversed(self.screen.buffer):
                line_data = "".join(map(operator.attrgetter("data"), line)).strip()
                if len(line_data) > 0:
                    parser_result = self.command_parser(line_data)
                    if parser_result is not None:
                        # 2个条件写一起会有错误的数据
                        if len(parser_result) > 0:
                            command = parser_result
                    else:
                        command = line_data
                    break
        except Exception:
            pass
        # 虚拟屏幕清空
        self.screen.reset()
        return command

    @staticmethod
    def get_win_size():
        """
        This function use to get the size of the windows!
        获得terminal窗口大小
        """
        if 'TIOCGWINSZ' in dir(termios):
            TIOCGWINSZ = termios.TIOCGWINSZ
        else:
            TIOCGWINSZ = 1074295912L
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s)
        return struct.unpack('HHHH', x)[0:2]

    def set_win_size(self, sig, data):
        """
        This function use to set the window size of the terminal!
        设置terminal窗口大小
        """
        try:
            win_size = self.get_win_size()
            self.channel.resize_pty(height=win_size[0], width=win_size[1])
        except Exception:
            pass

    def tty_log(self,record):
        self.f_log.write(record)
        self.f_log.flush()

    def input_log(self,record):
        try:
            self.con.ping()
        except Exception,e:
            if not self.__init_db():
                return
        cur = self.con.cursor()
        sql = "insert into inlog(client_ip,server_ip,ldap_user,os_user,datas) VALUES(%s,%s,%s,%s,%s)"
        param=  (remote_ip,self.server_ip,self.ldap_user,self.ssh_user,record)
        try:
            cur.execute(sql,param)
        except Exception,e:
            print e
        cur.close()


    def posix_shell(self):
        """
        Use paramiko channel connect server interactive.
        使用paramiko模块的channel，连接后端，进入交互式
        """
        old_tty = termios.tcgetattr(sys.stdin)
        data = ''
        input_mode = False

        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.channel.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([self.channel, sys.stdin], [], [])
                    flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL, 0)
                    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flag|os.O_NONBLOCK)
                except Exception:
                    pass

                if self.channel in r:
                    try:
                        x = self.channel.recv(10240)
                        if len(x) == 0:
                            break

                        index = 0
                        len_x = len(x)
                        while index < len_x:
                            try:
                                n = os.write(sys.stdout.fileno(), x[index:])
                                sys.stdout.flush()
                                index += n
                            except OSError as msg:
                                if msg.errno == errno.EAGAIN:
                                    continue
                        now_timestamp = time.time()
                        self.tty_log(x)
                        #f.write(x)
                        #f.flush()
                        #termlog.write(x)
                        #termlog.recoder = False
                        #log_time_f.write('%s %s\n' % (round(now_timestamp-pre_timestamp, 4), len(x)))
                        #log_time_f.flush()
                        #log_file_f.write(x)
                        #log_file_f.flush()
                        #pre_timestamp = now_timestamp
                        #log_file_f.flush()

                        self.vim_data += x
                        if input_mode:
                            data += x

                    except socket.timeout:
                        pass

                if sys.stdin in r:
                    try:
                        x = os.read(sys.stdin.fileno(), 4096)
                    except OSError:
                        pass
                    #termlog.recoder = True
                    input_mode = True
                    if self.is_output(str(x)):
                        # 如果len(str(x)) > 1 说明是复制输入的
                        if len(str(x)) > 1:
                            data = x
                        match = self.vim_end_pattern.findall(self.vim_data)
                        if match:
                            if self.vim_flag or len(match) == 2:
                                self.vim_flag = False
                            else:
                                self.vim_flag = True
                        elif not self.vim_flag:
                            self.vim_flag = False
                            data = self.deal_command(data)[0:200]
                            if data is not None:
                                self.input_log(data)
                                #log = "\n%s | %s | %s | %s\n" % (self.remote_ip, date, self.ldap_user, data)
                                #f.write(log)
                                #f.flush()
                                #TtyLog(log=log, datetime=datetime.datetime.now(), cmd=data).save()
                        data = ''
                        self.vim_data = ''
                        input_mode = False

                    if len(x) == 0:
                        break
                    self.channel.send(x)
        finally:

            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            #f.close()
            #os.close(sys.stdin.fileno())
            #log_file_f.write('End time is %s' % datetime.datetime.now())
            #log_file_f.close()
            #log_time_f.close()
            #termlog.save()
            #log.filename = termlog.filename
            #log.is_finished = True
            #log.end_time = datetime.datetime.now()
            #log.save()



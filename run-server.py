#!/usr/bin/env python
# coding: utf-8

import sys,os,textwrap,datetime,ConfigParser,getpass,re,socket
from sshlogin import sshlogin
import requests
from check_ldapuser import LDAPTool
from passwd_complex import recent_passwd
from dns import resolver,reversename


install_path='/var/relay/'
login_user = getpass.getuser()


try:
    remote_ip = os.environ.get('SSH_CLIENT').split()[0]
except (IndexError, AttributeError):
    remote_ip = os.popen("who -m | awk '{ print $NF }'").read().strip('()\n')

class nav(object):
    def __init__(self):
        self.ssh_user=""
        self.connect_hostname=""
        self.lp = LDAPTool()
        if self.lp.check_modify() == None:
            self.last_change_pw = int(1)
        else:
            self.last_change_pw = self.lp.check_modify()

    def getIp(self,domain):
        import socket
        try:
            myaddr = socket.getaddrinfo(domain, 'http')[0][4][0]
        except:
            print domain+"主机名无法解析\n"
        return myaddr


    def try_connect(self):
        config = ConfigParser.ConfigParser()
        config.read(install_path+'conf/access.ini')
        users = config.get(login_user,self.connect_hostname)
        users_list=users.split(',')
        if len(users_list)==1:
            self.ssh_user=users
        else:
            os.system('clear')
            nav.print_nav()
            print "\033[32m[ID] 系统用户\033[0m"
            for index, name in enumerate(users_list):
                print "[%-1s] %s" % (index, name)
            print '授权系统用户超过1个，请输入ID or USER, q退出'
            try:
                role_index = raw_input("\033[1;32mID>:\033[0m ").strip()
                if role_index == 'q':
                    return
                elif role_index in users_list:
                    self.ssh_user=role_index
                else:
                    self.ssh_user = users_list[int(role_index)]
            except Exception:
                print('\033[1;31m错误: 请输入正确ID or USER\033[0m')
                return
        os.system('clear')
        ssh=sshlogin(self.getIp(self.connect_hostname),22,login_user,self.ssh_user,"",0)
        ssh.ssh_connect()

    def print_nav(self):
        msg="""\n\033[5;36m                  Welcome to Guazi relay server \033[0m\n
----------------------------------------------------------------
\033[1;34mDATE: %s                     USER: %s\033[0m
----------------------------------------------------------------
0) 输入 \033[32mHost\033[0m 直接登录 或 输入\033[32m部分主机名\033[0m 进行搜索登录(如果唯一).
1) 输入 \033[32mP/p\033[0m 显示您有权限的主机.
2) 输入 \033[32mC/c\033[0m 更改密码(%s天后过期).
3) 输入 \033[32mH/h\033[0m 显示帮助信息.
4) 输入 \033[32mQ/q\033[0m 退出.
        """%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),login_user,self.expire_passwd())
        print textwrap.dedent(msg)

    def print_search_result(self,hosts=[]):#*hosts):
        if len(hosts)==1:
            #print hosts
            self.connect_hostname=hosts[0]
            self.try_connect()
            return
        three_lines = ""
        n = 0
        i = 0
       # hosts=list(hosts[0])
        for host in hosts:
            i = i + 1
            if n == 2:
                n = 0
                print three_lines + ' ' * (90 - len(three_lines) - len(host)) + host
                three_lines = ""
            else:
                if n == 0:
                    three_lines = host
                else:
                    three_lines = three_lines + ' ' * (45 - len(three_lines) - len(host)) + host
                if len(hosts) <= i:
                    print three_lines
                n = n + 1

    def isValidIp(self,ip):
        if re.match(r"^\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$", ip): return True
        return False

    def isHostname(self,ip):
        try:
            addr = reversename.from_address(ip)
            ptr_name = resolver.query(addr,'PTR')
            hn = socket.gethostbyaddr(ip)[0]
        except Exception,e:
            os.system('clear')
            nav.print_nav()
            print self.print_dict('invalid_addr')
            return
        config = ConfigParser.ConfigParser()
        config.readfp(open(install_path + 'conf/access.ini'))
        hosts = config.options(login_user)
        if len(ptr_name) >=2:
            HostName_list = []
            reversename_list = [ i for i in ptr_name ]
            for i in range(len(reversename_list)):
                HostName = re.split(' ',str(reversename_list[i]))[0].split('.dns')[0]
                HostName_list.append(HostName)
            intersection = list((set(HostName_list).union(set(hosts)))^(set(HostName_list)^set(hosts)))
            self.connect_hostname=intersection[0]
            self.try_connect()
        else:
            HostName = re.split(' ',str(ptr_name[0]))[0].split('.dns')[0]
            if HostName in hosts:
                self.connect_hostname=HostName
                self.try_connect()
            elif hn == "localhost":
                os.system('clear')
                nav.print_nav()
                print self.print_dict('res_fail') %(ip)
            else:
                os.system('clear')
                nav.print_nav()
                print result
                print hn.split('.dns')[0]
                print self.print_dict('per_denied') % (ip)


    def search(self,keyword):
        if keyword:
            if self.isValidIp(keyword):
                self.isHostname(keyword)
                return
            config = ConfigParser.ConfigParser()
            config.readfp(open(install_path+'conf/access.ini'))
            try:
                hosts = config.options(login_user)
                tmp=[]
                for host in hosts:
                    if keyword in host:
                        tmp.append(host)
                if len(tmp) == 0:
                    os.system('clear')
                    nav.print_nav()
                print self.print_dict('not_found')
            self.print_search_result(tmp)
            except Exception,e:
                print self.print_dict('parser_fail')
        else:
            config = ConfigParser.ConfigParser()
            config.readfp(open(install_path+'conf/access.ini'))
            hosts=config.options(login_user)
            self.print_search_result(hosts)

    def see_last_passtime(self):
        num = int(0)
        os.system('clear')
        print self.print_dict('last_time') % (self.last_change_pw,int(90) - self.last_change_pw)
        while num < int(3):
            opt = raw_input("请问是否修改密码[\033[1;32mY\033[0m/\033[1;32mN\033[0m]:" ).strip()
            if opt in ["n","N","no","No"]:
                return
            elif opt in ["y","Y","Yes","yes"]:
                self.print_rules()
                self.verify_passwd()
                return
            else:
               print self.print_dict('invalid_opt')
               num +=1
               continue

    def verify_passwd(self):
        for _ in range(3):
            old_pwd = getpass.getpass('\033[1;36m旧密码(q退出):\033[0m ')
            if old_pwd in ["q","Q","quit","exit"]: return
            verify_pwd = self.lp.ldap_get_vaild(login_user,old_pwd)
            if verify_pwd:
                new_pwd = getpass.getpass("\033[1;32m新密码:\033[0m ")
                new_pwd2 = getpass.getpass("\033[1;32m再次输入,新密码:\033[0m ")
                if recent_passwd(login_user,old_pwd,new_pwd,new_pwd2):
                    self.lp.ldap_update_pass(login_user,old_pwd,new_pwd)
                    print self.print_dict('success')
                    sys.exit()
            else:
                continue


    def print_dict(self, word):
        stat = {
            'success': '\033[1;32m成功:\033[0m密码更新成功,连接断开!请重新连接认证.',
            'old_faild': '\033[1;31m错误:\033[0m 旧密码验证失败,请确认!\n',
            'invalid_opt': '\033[1;31m错误:\033[0m 无效的选择,请重新输入!\n',
            'not_found':'\033[1;31m错误:\033[0m 没有查找到相关的主机记录,请重新输入!\n',
            'res_fail':'\033[1;31m错误:\033[0m %s 地址解析异常,请重新输入!\n',
            'invalid_addr':'\033[1;31m错误:\033[0m 无效的地址,请核实!\n',
            'per_denied':'\033[1;31m错误:\033[0m 您没有权限访问 %s,请重新输入!\n',
            'day':'\033[1;31m%d\033[0m',
            'set_pw':'\033[1;31m提示:\033[0m relay账户密码过期,请重新设置密码! 否则将无法使用!\n',
            'parser_fail':'\033[1;31m错误:\033[0m 配置文件解析异常,请确认您是否有主机权限!\n',
            'last_time' :'\n距离上次修改密码时间已经\033[1;32m%d\033[0m天,距离密码过期还有\033[1;31m%d\033[0m天.请及时修改密码,以免影响正常使用!\n',
        }
        return stat[word]

    def print_rules(self):
        rules = "\033[1;31m重置密码原则:\033[0m\n\
  1) 密码的长度需大于等于8位.\n\
  2) 密码可使用90天,过期需要更改密码.\n\
  3) 密码不得和密码历史(最近3次)重复.\n\
  4) 密码需符合复杂性要求至少包含(大写、小写、数字、符号)三种类型以上.\n"
        print rules


    def expire_passwd(self):
        expire_day = int(90) - int(self.last_change_pw)
        if expire_day <= 0:
            print self.print_dict('set_pw')
            while True:
                self.verify_passwd()
        elif expire_day <= 7:
            return self.print_dict('day') % expire_day
        else:
            return int(expire_day)

def main():
    while True:
        try:
            sys.stdin = open('/dev/tty')
            option = raw_input("\n\033[1;32mOpt or Host>:\033[0m ").strip()
        except EOFError:
            os.system('clear')
            sys.exit()
        if option in ['Q', 'q', 'exit','quit']:
            os.system('clear')
            sys.exit()
        elif option in ['H','h','help','?']:
            os.system('clear')
            nav.print_nav()
        elif option in ['P', 'p', 'l']:
            os.system('clear')
            nav.search("")
        elif option in ['c','C']:
            nav.see_last_passtime()
        else:
            os.system('clear')
            nav.print_nav()
            print "\033[1;32mOpt or Host>:\033[0m %s" % option
            nav.search(option)



if __name__== '__main__':
    nav=nav()
    os.system('clear')
    nav.print_nav()
    while True:
        try:
            main()
        except KeyboardInterrupt,e:
            print '\r\n'
            #sys.exit()
            pass
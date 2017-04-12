#!/usr/bin/env python
#-*-coding:utf-8-*-

import re
import pickle
import os
from collections import deque

history_path="/data/service/replay/history/"

class CheckPasswdComplex():
    def __init__(self,pwd,pwd2):
        self.pwd = pwd
        self.pwd2 = pwd2
        self.history = deque([],3)

    def cklen(self):
        return len(self.pwd)>=8
    def ckUpper(self):
        pattern = re.compile('[A-Z]+')
        match = pattern.findall(self.pwd)
        result = True if match else  False
        return result
    def ckNum(self):
        pattern = re.compile('[0-9]+')
        match = pattern.findall(self.pwd)
        result = True if match else  False
        return result
    def ckLower(self):
        pattern = re.compile('[a-z]+')
        match = pattern.findall(self.pwd)
        result = True if match else  False
        return result
    def ckSymbol(self):
        pattern = re.compile('([^a-z0-9A-Z])+')
        match = pattern.findall(self.pwd)
        result = True if match else  False
        return result
    def ckPassword(self):
        #if self.pwd != self.pwd2:
        #    print "\033[1;31m错误:\033[0m 两次密码输入的结果不一致!\n"
        #    return False
        if not self.cklen():
            print "\033[1;31m错误:\033[0m 新密码的长度不能低于8位!\n"
            return False
        if (self.ckUpper() and self.ckLower() and self.ckNum()) or \
                (self.ckUpper() and self.ckLower() and self.ckSymbol())or \
                (self.ckLower() and self.ckNum() and self.ckSymbol()) or \
                (self.ckUpper() and self.ckNum() and self.ckSymbol()):
            return True
        print "\033[1;31m错误:\033[0m 新的密码不符合密码复杂性要求(大写/小写/数字/符号)至少\033[1;32m三种\033[0m类型的组合!"
        return False

def recent_passwd(user,pwd,pwd2):
    history = deque([],3)
    passwd_complex = CheckPasswdComplex(pwd,pwd2).ckPassword()
    history_log = ("%s%s.history") % (history_path,user)
    if passwd_complex:
        if os.path.isfile(history_log):
            history = pickle.load(open(history_log))
        else:
            history.append(old_pwd)
        if pwd in list(history):
            print "\033[1;31m错误:\033[0m 新密码不能和密码历史(最近3次)重复,请您重新修改!"
            return False
        history.append(pwd)
        pickle.dump(history,open(history_log,'w'))
        return True

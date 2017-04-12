#!/usr/bin/env python
# coding: utf-8

import ldap
import os
import commands
import datetime
import sys

LDAP_HOST="127.0.0.1"
USER="testuser"
PASSWORD="testpasswd"
BASE_DN="testdn"

class LDAPTool():
    def __init__(self,ldap_host=None,base_dn=None,user=None,password=None):
        if not ldap_host:
            ldap_host = LDAP_HOST
        if not base_dn:
            self.base_dn = BASE_DN
        if not user:
            user = USER
        if not password:
            password = PASSWORD
        try:
            self.ldapconn = ldap.open(ldap_host)
            self.ldapconn.simple_bind(user,password)
        #except ldap.LDAPError,e:
        except Exception,e:
            print e
    def ldap_search_dn(self,uid=None):
        obj = self.ldapconn
        obj.protocol_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None
        searchFilter = "cn=" + uid

        try:
            ldap_result_id = obj.search(self.base_dn, searchScope, searchFilter, retrieveAttributes)
            result_type, result_data = obj.result(ldap_result_id, 0)
            # 返回数据格式
            # ('cn=django,ou=users,dc=gccmx,dc=cn',
            #    {  'objectClass': ['inetOrgPerson', 'top'],
            #        'userPassword': ['{MD5}lueSGJZetyySpUndWjMBEg=='],
            #        'cn': ['django'], 'sn': ['django']  }  )
            #
            if result_type == ldap.RES_SEARCH_ENTRY:
                return result_data[0][0]
            else:
                return None
        except ldap.LDAPError, e:
            print e

    # 查询用户记录，返回需要的信息
    def ldap_get_user(self, uid=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None
        searchFilter = "cn=" + uid
        try:
            ldap_result_id = obj.search(self.base_dn, searchScope, searchFilter, retrieveAttributes)
            result_type, result_data = obj.result(ldap_result_id, 0)
            if result_type == ldap.RES_SEARCH_ENTRY:
                username = result_data[0][1]['cn'][0]
                email = result_data[0][1]['mail'][0]
                nick = result_data[0][1]['sn'][0]
                result = {'username': username, 'email': email, 'nick': nick}
                return result
            else:
                return None
        except ldap.LDAPError, e:
            print e

    # 用户验证，根据传递来的用户名和密码，搜索LDAP，返回boolean值
    def ldap_get_vaild(self, uid=None, passwd=None):
        obj = self.ldapconn
        target_cn = self.ldap_search_dn(uid)
        try:
            if obj.simple_bind_s(target_cn, passwd):
                return True
            else:
                return False
        except Exception, e:
            print "\033[1;31m错误:\033[0m 旧密码验证失败,请确认!\n\033[1;32m提示: \033[0m忘记密码可以登录网址重置密码: http://relay.guazi-corp.com/chpasswd"

    # 修改用户密码
    def ldap_update_pass(self, uid=None, oldpass=None, newpass=None):
        modify_entry = [(ldap.MOD_REPLACE, 'userpassword', newpass)]
        obj = self.ldapconn
        target_cn = self.ldap_search_dn(uid)
        try:
            obj.simple_bind_s(target_cn, oldpass)
            obj.passwd_s(target_cn, oldpass, newpass)
            return True
        except ldap.LDAPError, e:
            return False

    def check_modify(self):
        try:
            status,date = commands.getstatusoutput('/data/shell_files/check_modify.sh')
            if status == 0:
                now = datetime.datetime.now().strftime('%Y%m%d')
                day = int(now) - int(date)
                return day
            else:
               print "无法连接LDAP服务器"
        except Exception,e:
            #print e
            print "\033[1;31m错误:\033[0m LDAP服务连接异常,请联系SA! 邮件组: js.ts.sa@guazi.com\n"

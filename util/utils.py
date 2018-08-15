#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : utils.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/6
# @Desc     :
import logging
import socket
import subprocess as sp
import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import configs
from fabric.api import env, task, execute, get

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_windows_client_name(ipaddr):
    ''' 通过IP地址查询Windows客户端名称 '''
    try:
        client = socket.gethostbyaddr(ipaddr)
        return client[0]
    except socket.error:
        logger.warning("Client isnot alive!")
        return None

def get_client_alive_ping(ipaddr):
    ''' 判断客户端是否在线 '''
    status, result = sp.getstatusoutput("ping -n 1 " + ipaddr)
    if status == 0:
        return True
    else:
        return False

def is_alive(ipaddr, port, timeout=1):
    ''' 判断客户端是否在线 '''
    session = socket.socket()
    session.settimeout(timeout)
    status = session.connect_ex((ipaddr, port))
    session.close()
    if status == 0:
        return True
    else:
        logger.info("%s not alive,status: %s" %(ipaddr, status))
        return False

def is_client_alive(ipaddr):
    port = configs['tc']['listen_port']
    timeout = configs['tc']['timeout']
    return is_alive(ipaddr, port, timeout)

def get_clients_alive_num(tc_list):
    tc_alive = {}
    for line in tc_list:
        for tc in line:
            logger.info("TC IP: %s" % tc)
            tc_alive[tc] = int(is_client_alive(tc))
    total_alive = sum(list(tc_alive.values()))
    return total_alive

def is_host_alive(port = configs['host']['port']):
    ''' 判断主机是否在线 '''
    host_ip = configs['host']['ip']
    return is_alive(host_ip, port)

@task
def task_get_logs(backup_path, log_src_dir, file_list):
    # 备份日志
    for file in file_list:
        log_file = log_src_dir + '/' + file
        current_file = os.path.join(backup_path, file)
        get(log_file, current_file)

def get_log_file(client_log_path):
    host_ip = configs['host']['ip']
    port = configs['host']['port']
    user = configs['host']['user']
    host = user + '@' + host_ip + ':' + str(port)
    password = configs['host']['password']
    env.passwords[host] = password
    file_list = configs['host']['log_files']
    log_src_dir = configs['host']['log_path']

    # 创建日志备份文件夹
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    backup_path = os.path.join(configs['log']['full_path'], current_time)
    os.makedirs(backup_path)

    execute(task_get_logs, backup_path, log_src_dir, file_list, hosts=host)

    # 备份教师端的日志
    for client_log in configs['log']['client_log']:
        log_file = os.path.join(client_log_path, client_log)
        os.system('copy %s %s' %(log_file, backup_path))


if __name__ == '__main__':
    #client_log_path = r'e:\Projects\TeachingAuto\testsuits'
    #get_log_file(client_log_path)
    print(is_host_alive())
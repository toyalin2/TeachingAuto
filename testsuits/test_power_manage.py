#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : test_power_manage.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/8
# @Desc     :
import pytest
import os
import sys
from time import sleep, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import configs
from model.teachmain import TeachingMain, Launch
from util.utils import get_clients_alive_num, is_host_alive
import logging

# 定义Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def func_timeout_ex(func, args, result, timeout):
    start_time = time()
    while True:
        end_time = time()
        wakeup_time = end_time - start_time
        if not args:
            if func() == result:
                break
        else:
            if func(args) == result:
                break
        if timeout > wakeup_time:
            continue
        else:
            wakeup_time = None
            logger.warning("Wakeup host timeout!")
            break
    return wakeup_time

def setup_function():
    launch = Launch(configs)
    launch.start_teacher_main()

def test_shutdown_tcs():
    ''' 关机终端 '''
    teacher_main = TeachingMain(configs)
    tc_list = teacher_main.get_client_ips()
    teacher_main.click_clients_poweroff()
    sleep(configs['teachermain']['power_manage']['wait_shutdown'])
    assert get_clients_alive_num(tc_list) == 0

def test_wakeup_tcs():
    ''' 唤醒终端 '''
    teacher_main = TeachingMain(configs)
    tc_list = teacher_main.get_client_ips()
    tc_num = len([i for line in tc_list for i in line])
    timeout = configs['teachermain']['power_manage']['wait_wakeup_tc']
    alive_num = get_clients_alive_num(tc_list)
    if alive_num == 0:
        teacher_main.click_clients_wakeup()
        wakeup_time = func_timeout_ex(get_clients_alive_num, tc_list, tc_num, timeout)
        logger.info("%s clients wakeup time: %s" % (alive_num, wakeup_time))
        assert wakeup_time
    else:
        logger.warning("Clients already alive!")

def test_restart_tcs():
    ''' 重启终端 '''
    teacher_main = TeachingMain(configs)
    tc_list = teacher_main.get_client_ips(configs['tc']['pattern'])
    tc_num = len([i for line in tc_list for i in line])
    alive_num = get_clients_alive_num(tc_list)
    if alive_num != tc_num:
        teacher_main.click_clients_wakeup()
        sleep(configs['teachermain']['power_manage']['wait_wakeup_tc'])
    teacher_main.click_clients_restart()
    sleep(configs['teachermain']['power_manage']['wait_shutdown'])
    alive_num = get_clients_alive_num(tc_list)
    assert alive_num == 0
    sleep(configs['teachermain']['power_manage']['wait_wakeup_tc'])
    alive_num = get_clients_alive_num(tc_list)
    assert alive_num == tc_num

def test_wakeup_host():
    ''' 唤醒主机 '''
    if is_host_alive():
        logger.warning("Host already alive!")
    else:
        timeout = configs['teachermain']['power_manage']['wait_wakeup_host']
        teacher_main = TeachingMain(configs)
        teacher_main.click_host_wakeup()
        wakeup_time =  func_timeout_ex(is_host_alive, None, True, timeout)
        logger.info("Host wakeup time: %s" % wakeup_time)
        assert wakeup_time

def test_class_over():
    ''' 放学 '''
    if not is_host_alive():
        logger.warning("Host not alive!")
    else:
        teacher_main = TeachingMain(configs)
        teacher_main.click_class_over()
        #sleep(configs['teachermain']['power_manage']['wait_shutdown_host'])
        timeout = configs['teachermain']['power_manage']['wait_shutdown_host']
        over_time = func_timeout_ex(is_host_alive, 22, False, timeout)
        logger.info("Host shutdown time: %s" % over_time)
        tc_list = teacher_main.get_client_ips(configs['tc']['pattern'])
        alive_num = get_clients_alive_num(tc_list)
        assert alive_num == 0
        assert not is_host_alive()

def test_logon_desktop_time():
    ''' 性能：从唤醒到登录桌面的总时间 '''
    teacher_main = TeachingMain(configs)
    tc_list = teacher_main.get_client_ips()
    tc_num = len([i for line in tc_list for i in line])
    timeout = 150
    alive_num = get_clients_alive_num(tc_list)
    if alive_num == 0:
        teacher_main.click_clients_wakeup()
        wakeup_logon_time = teacher_main.get_logon_time(timeout)
        logger.info("%s clients logon desktop: %s" % (alive_num, wakeup_logon_time))
        assert wakeup_logon_time
    else:
        logger.warning("Clients already alive!")

if __name__ == '__main__':
    pytest.main(["-q", "test_power_manage.py::test_wakeup_host"])
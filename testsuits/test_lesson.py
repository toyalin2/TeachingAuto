#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : test_lesson.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/6
# @Desc     :
import pytest
import os
import sys
from time import sleep
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import configs
from model.teachmain import TeachingMain, Launch
from util.utils import get_log_file, is_client_alive, is_host_alive
import logging

# 定义Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture()
def start_teacher_main():
    launch = Launch(configs)
    launch.start_teacher_main()

@pytest.mark.usefixtures("start_teacher_main")
def test_lesson_stability():
    '''
    上下课稳定性
    :return:
    '''
    teacher_main = TeachingMain(configs)
    loop = configs['teachermain']['stability']['loop']
    error_num = 0
    timeout = configs['teachermain']['lesson']['timeout_stop']
    for i in range(loop):
        logger.info("Stability Testing, No.%s" % i)
        logger.info("Stability Testing: Start lesson.")
        # 上课
        teacher_main.start_lesson(configs['teachermain']['stability']['lesson_name'])

        sleep(configs['teachermain']['stability']['wait'])
        # 上课结果
        logger.info("Stability Testing: Check alive clients.")
        clients = teacher_main.get_total_clients()
        offline = teacher_main.get_offline_clients()
        if offline == 0:
            # 下课
            logger.info("Stability Testing: Stop lesson.")
            teacher_main.stop_lesson()
            stop_time = teacher_main.get_logon_time(timeout, clients)
            logger.info("Time to stop lesson: %s" % stop_time)
        else:
            error_num += 1
            logger.debug("Backup log files after error." )
            get_log_file(os.path.dirname(__file__))
    assert error_num == 0

@pytest.mark.usefixtures("start_teacher_main")
def test_start_lesson():
    '''
    启动课程，如果tc未开机，则自动开机上课
    '''
    teacher_main = TeachingMain(configs)
    timeout = configs['teachermain']['lesson']['timeout_start']
    teacher_main.start_lesson(configs['teachermain']['stability']['lesson_name'])
    start_time = teacher_main.get_logon_time(timeout)
    logger.info("desktop start time: %s" % start_time)
    assert start_time

@pytest.mark.usefixtures("start_teacher_main")
def test_restart_lesson():
    '''
    重启课程桌面
    :return:
    '''
    timeout = configs['teachermain']['lesson']['timeout_stop']
    teacher_main = TeachingMain(configs)
    clients = teacher_main.get_total_clients()
    teacher_main.restart_lesson()
    stop_time = teacher_main.get_logon_time(timeout, clients)
    logger.info("Time to stop lesson: %s" % stop_time)
    assert stop_time
    timeout = configs['teachermain']['lesson']['timeout_start']
    start_time = teacher_main.get_logon_time(timeout)
    logger.info("desktop start time: %s" % start_time)
    assert start_time

@pytest.mark.usefixtures("start_teacher_main")
def test_keep_quiet():
    '''
        安静黑屏
    '''
    teacher_main = TeachingMain(configs)
    clients = teacher_main.get_total_clients()
    logger.info("Total %s desktop." % clients)
    teacher_main.click_black_screen()
    sleep(configs['teachermain']['lesson']['wait_quiet'])
    num = teacher_main.get_quiet_num()
    logger.info("Total %s desktop is quiet." % num)
    assert num == clients

@pytest.mark.usefixtures("start_teacher_main")
def test_cancel_quiet():
    '''
        退出安静黑屏
    '''
    teacher_main = TeachingMain(configs)
    teacher_main.click_cancel_black_screen()
    sleep(configs['teachermain']['lesson']['wait_quiet'])
    num = teacher_main.get_quiet_num()
    logger.info("Total %s desktop is quiet." % num)
    assert num == 0

@pytest.mark.usefixtures("start_teacher_main")
def test_stop_lesson():
    '''
    下课
    '''
    timeout = configs['teachermain']['lesson']['timeout_stop']
    teacher_main = TeachingMain(configs)
    clients = teacher_main.get_total_clients()
    teacher_main.stop_lesson()
    stop_time = teacher_main.get_logon_time(timeout, clients)
    logger.info("Time to stop lesson: %s" % stop_time)
    assert stop_time

@pytest.mark.usefixtures("start_teacher_main")
def test_switch_local_mode():
    '''
        切换为本地考试模式
    '''
    timeout = configs['teachermain']['lesson']['timeout_switch']
    teacher_main = TeachingMain(configs)
    teacher_main.click_switch_local_mode()
    switch_time = teacher_main.get_logon_time(timeout)
    logger.info("Time to switch to local mode: %s" % switch_time)
    assert switch_time

if __name__ == '__main__':
    pytest.main(["-q", "test_lesson.py::test_lesson_stability"])
    #test_lesson_stability()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : test_remote_cmd.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/10
# @Desc     :
import pytest
import os
import sys
from time import sleep
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import configs
from model.teachmain import TeachingMain, Launch
import logging

# 定义Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_function():
    launch = Launch(configs)
    launch.start_teacher_main()

def test_launch_app():
    '''
    基于模式匹配检测远程运行应用程序
    :return:
    '''
    teacher_main = TeachingMain(configs)
    teacher_main.click_launch_app()
    teacher_main.click_remote_app_run(configs['teachermain']['remote_app']['app_name'])
    sleep(configs['teachermain']['remote_app']['run_wait'])
    clients = teacher_main.get_total_clients()
    logger.info("Total %s desktop." % clients)
    apps = teacher_main.get_remote_app_start_num()
    logger.info("Total %s desktop launched the specify app." % clients)
    assert clients == apps

def test_launch_webpage():
    '''
    基于模式匹配检测远程运行应用程序
    :return:
    '''
    teacher_main = TeachingMain(configs)
    teacher_main.click_launch_webpage()
    teacher_main.click_remote_open_webpage(configs['teachermain']['remote_page']['page_name'])
    sleep(configs['teachermain']['remote_page']['run_wait'])
    clients = teacher_main.get_total_clients()
    logger.info("Total %s desktop." % clients)
    pages = teacher_main.get_remote_page_start_num()
    logger.info("Total %s desktop launched the specify app." % clients)
    assert clients == pages

def test_forbidden_net():
    '''
    禁网检测
    :return:
    '''
    teacher_main = TeachingMain(configs)
    teacher_main.click_forbidden_net()
    # 测试【打开网页】

def test_black_list():
    '''
    黑名单检测
    :return:
    '''
    teacher_main = TeachingMain(configs)
    teacher_main.add_white_black_policy(black=True)
    teacher_main.apply_black_policy()
    # 检测黑名单列表
    teacher_main.is_all_blacklist()
    # 检测应用效果
    teacher_main.click_launch_webpage()
    teacher_main.click_remote_open_webpage(configs['teachermain']['remote_page']['page_name'])
    pages = teacher_main.get_remote_page_start_num()
    assert pages == 0

if __name__ == '__main__':
    pytest.main(["-q", "test_clients.py::test_launch_app"])
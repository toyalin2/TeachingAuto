#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : run.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/13
# @Desc     :
#import pytest
from config.config import configs
from model.teachmain import TeachingMain, Launch
import os
import logging
from time import time, sleep, localtime, strftime
from util.utils import get_log_file

# 定义Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

time_str = strftime("%Y_%m_%d_%H_%M_%S", localtime(time()))
logname = 'teachmain' + '_' + time_str + '.log'
file_handler = logging.FileHandler(logname)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if __name__ == '__main__':
    launch = Launch(configs)
    launch.start_teacher_main()
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
            logger.debug("Backup log files after error.")
            get_log_file(os.path.dirname(__file__))
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : test_workspace.py.py
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

def test_enter_workspace():
    teacher_main = TeachingMain(configs)
    teacher_main.click_enter_workspace()

if __name__ == '__main__':
    pytest.main(["-q", "test_workspace.py::test_enter_workspace"])
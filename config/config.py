#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : config.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/6
# @Desc     :
import os
import yaml
import logging

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def merge(user, default):
    ''' 合并配置 '''
    if isinstance(user, dict) and isinstance(default, dict):
        for k,v in default.items():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge(user[k],v)
    return user

def load_config():
    ''' 加载合并后的配置 '''
    # 读取默认配置
    logger.debug("Load default config from default.yaml.")
    default_config = os.path.join(os.path.dirname(__file__), 'default.yaml')
    with open(default_config, 'r', encoding="utf8") as f:
        default = yaml.load(f)

    # 读取用户自定义配置
    logger.debug("Load user config from user.yaml.")
    user_config = os.path.join(os.path.dirname(__file__), 'user.yaml')
    with open(user_config, 'r', encoding="utf8") as f:
        user = yaml.load(f)

    # 整合配置
    logger.debug("Merge default config and user config.")
    if not user:
        configs = default
    else:
        configs = merge(user, default)
    return configs

def get_install_path(path_suffix):
    ''' 检测系统位数，放回完整路径 '''
    if r'PROGRAMFILES(X86)' in os.environ:
        logger.debug("Current Windows: 64bits.")
        exe_path = os.path.join(os.environ['PROGRAMFILES(X86)'], path_suffix)
    else:
        logger.debug("Current Windows: 32bits.")
        exe_path = os.path.join(os.environ['PROGRAMFILES'], path_suffix)
    return exe_path

configs = load_config()

# 设置TeacherMain的全路径
configs['teachermain']['full_path'] = get_install_path(configs['teachermain']['suffix_path'])
configs['main_path'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
configs['log']['full_path'] = os.path.join(configs['main_path'], configs['log']['suffix_path'])

# 设置素材所在路径
configs['img']['full_path'] = os.path.join(configs['main_path'], configs['img']['path'])

if not os.path.exists(configs['log']['full_path']):
    os.makedirs(configs['log']['full_path'])

if __name__ == '__main__':
    print(configs)
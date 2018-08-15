#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File     : teachmain.py.py
# @Author   : Panthe_Bao
# @Software : PyCharm
# @Date     : 2018/8/6
# @Desc     :
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import configs
from util.utils import get_clients_alive_num, is_host_alive
from pywinauto import Desktop
from pywinauto.application import Application
import cv2 as cv
import numpy as np
import pytesseract as ocr
from time import time, sleep, strftime, localtime

# 定义Logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Launch(object):
    def __init__(self, configs):
        self.configs = configs
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def is_visible_main(self, timeout=2):
        main_win = Desktop(backend="uia").window(**self.configs['teachermain']['main']['id'])
        return main_win.exists(timeout=timeout)

    def get_trayicon(self):
        tray_shell = Desktop(backend="uia").window(**self.configs['TaskBar']['id'])
        tray_icon = tray_shell.window(**self.configs['TaskBar']['teacher_icon'])
        return tray_icon

    def start_from_tray(self, tray_icon):
        tray_icon.wrapper_object().click_input()
        tray_icon_menu = Desktop(backend="uia").window(**self.configs['TaskBar']['teacher_menu']['id'])
        tray_icon_menu.wait('visible', timeout=10)
        tray_icon_menu.window(**self.configs['TaskBar']['teacher_menu']['display_win']).wrapper_object().click_input()
        main_win = Desktop(backend="uia").window(**self.configs['teachermain']['main']['id'])
        main_win.exists(timeout=5)

    def logon_process(self):
        ''' 登录处理 '''
        logon_win = Desktop(backend="uia").window(**self.configs['logon_win']['id'])
        if logon_win.exists(timeout=5):
            user = logon_win.window(**self.configs['logon_win']['user']).wrapper_object().get_value()
            self.logger.debug("Logon User: %s" % user)
            if user != self.configs['teachermain']['login']['user']:
                logon_win.window(**self.configs['logon_win']['user']).type_keys(configs['teachermain']['login']['user'])
            logon_win.window(**self.configs['logon_win']['passwd']).type_keys(self.configs['teachermain']['login']['passwd'])
            logon_win.window(**self.configs['logon_win']['logon_btn']).click()
            reg_win = Desktop(backend="uia").window(**self.configs['teachermain']['main']['id'])
            reg_btn = reg_win.window(**self.configs['teachermain']['main']['try_btn'])
            if (reg_btn.exists(2)):
                self.logger.info('Current Version: Try, not registered.')
                reg_btn.click()

    def start_from_exe(self):
        app = Application(backend="uia").start(self.configs['teachermain']['full_path'])
        self.logon_process()

    def start_teacher_main(self):
        if not self.is_visible_main():
            tray_icon = self.get_trayicon()
            if tray_icon.exists():
                self.start_from_tray(tray_icon)
            else:
                self.start_from_exe()
                self.is_visible_main(10)

class TeachingMain(object):
    def __init__(self, configs):
        self.configs = configs
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.logger.setLevel(logging.DEBUG)
        self.main_win = Desktop(backend="uia").window(**self.configs['teachermain']['main']['id'])  # 主窗口

    def capture_dropdown_menu(self):
        '''
        截图：工具栏中各按钮点击后弹出的下拉菜单
        :return:
        '''
        pop_win = self.main_win.window(**self.configs['teachermain']['menu'])
        self.main_win.wait('visible', timeout=5, retry_interval=1)
        # 截图
        self.logger.debug("Capture the dropdown menu.")
        menu_img = pop_win.capture_as_image()  # PIL Image
        # 转换成OpenCV图片
        self.logger.debug("Convert PIL image to OpenCV format.")
        cv_img = cv.cvtColor(np.array(menu_img), cv.COLOR_RGB2BGR)
        return cv_img, pop_win

    def enter_monitor_pane(self):
        '''进入监视视图'''
        self.main_win.window(**self.configs['teachermain']['left_sider']['monitor_view']).click()
        monitor_pane = self.main_win.window(**self.configs['teachermain']['monitor_pane']['id'])
        monitor_pane.wait('visible', timeout=30)
        return monitor_pane

    def capture_monitor_pane(self):
        '''
        截图：客户端桌面的屏幕显示区域
        :return:
        '''
        client_pane = self.main_win.window(**self.configs['teachermain']['monitor_pane']['id'])
        if not client_pane.exists():
            client_pane = self.enter_monitor_pane()
        monitor_region = client_pane.window(**self.configs['teachermain']['monitor_pane']['monitors']).capture_as_image()
        # PIL图片转OpenCV图片
        img_clients = cv.cvtColor(np.array(monitor_region), cv.COLOR_RGB2BGR)
        return img_clients

    def get_total_clients(self):
        '''
        检测界面中所有的客户端数，包括未上线的
        :return:
        '''
        img = self.capture_monitor_pane()
        lower_color = np.array([100, 43, 46])  # 蓝色
        upper_color = np.array([124, 255, 255])
        hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        mask_color = cv.inRange(hsv, lower_color, upper_color)
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
        wait_contours = cv.dilate(mask_color, kernel, iterations=2)
        cnts = cv.findContours(wait_contours, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        count = len(cnts[1])
        return count

    def get_offline_clients(self):
        '''
        通过阈值，统计未上线数量
        :param img: 客户端显示区域的截图
        :return:
        '''
        img = self.capture_monitor_pane()
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        th = cv.threshold(gray, 1, 255, cv.THRESH_BINARY_INV)[1]
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            img_name = '%s.png' % strftime('%Y%m%d%H%M', localtime(time()))
            full_path = os.path.join(configs['log']['full_path'], img_name)
            cv.imwrite(full_path, th)
        cnts = cv.findContours(th, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        count = len(cnts[1])
        self.logger.debug("Calc number of offline clients: %s" % count)
        return count

    def preprocess_ip_image(self):
        '''
        IP识别前的图像预处理
        :param img:
        :return:
        '''
        img = self.capture_monitor_pane()
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            full_path = os.path.join(configs['log']['full_path'], 'capture.png')
            cv.imwrite(full_path, img)
        # 去除背景
        img_no_background = cv.threshold(img, 200, 255, cv.THRESH_BINARY)[1]
        # Otsu's二值化
        gray = cv.cvtColor(img_no_background, cv.COLOR_BGR2GRAY)
        ost = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)[1]
        # laplacian算子
        gray_lap = cv.Laplacian(ost, -1, ksize=3)
        # 寻找轮廓
        cnts = cv.findContours(gray_lap, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        # 将桌面显示区域，以及小点，用白色填充
        for i in range(len(cnts[1])):
            x, y, w, h = cv.boundingRect(cnts[1][i])
            if h > 50:
                gray_lap[y:(y + h), x:(x + w + 10)] = 0
            elif h < 5:
                gray_lap[y:(y + h), x:(x + w)] = 0

        pro_img = cv.threshold(gray_lap, 127, 255, cv.THRESH_BINARY_INV)[1]
        return pro_img

    def string_to_ip(self, text, ip_pattern):
        '''将OCR识别出的字符串，分拆成IP列表'''
        pre_text = ''.join(ip_pattern.split('.')[:3])
        pre_ip = '.'.join(ip_pattern.split('.')[:3])
        ips = text.replace(' ', '').split('\n\n')
        clients = []
        for x in ips:
            self.logger.debug('String: %s' % x)
            digits = ''.join(list(filter(str.isdigit, x))).replace(pre_text, ' ').strip().split(' ')
            ip_array = []
            for client in digits:
                ipaddr = pre_ip + '.' + client
                ip_array.append(ipaddr)
            clients.append(ip_array)
        return clients

    def get_client_ips(self, ip_pattern = configs['tc']['pattern']):
        '''
        检测客户端IP地址
        :param ip_pattern:
        :return: 各行IP组成的列表
        '''
        ip_img = self.preprocess_ip_image()
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            full_path = os.path.join(configs['log']['full_path'], 'pre_ip.png')
            cv.imwrite(full_path, ip_img)
        # OCR识别数字,需采用tesseract 4.0
        ip_str = ocr.image_to_string(ip_img)
        self.logger.debug("IP String: %s" % ip_str)
        # 处理IP字符串
        ip_list = self.string_to_ip(ip_str, ip_pattern)
        self.logger.debug("IP of clients: %s" % ip_list)
        return ip_list

    def get_menu_items(self, cv_img):
        '''识别图片中的菜单项数量'''
        self.logger.debug("Image Process: dilation.")
        lower_color = np.array([100, 43, 46])  # 蓝色
        upper_color = np.array([124, 255, 255])
        hsv = cv.cvtColor(cv_img, cv.COLOR_BGR2HSV)
        mask_color = cv.inRange(hsv, lower_color, upper_color)
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (6, 6))
        img_dilate = cv.dilate(mask_color, kernel, iterations=2)
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            full_path = os.path.join(configs['log']['full_path'], 'menu.png')
            cv.imwrite(full_path, img_dilate)
        self.logger.debug("Get the contours of menu image.")
        cnts = cv.findContours(img_dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        count = len(cnts[1])
        self.logger.debug("Total Menu items: %s" % count)
        return count

    def click_menu_btn(self, item_id, fixed=0):
        '''点击下拉菜单项'''
        cv_img, pop_win = self.capture_dropdown_menu()
        rect = pop_win.rectangle()
        items_num = self.get_menu_items(cv_img) - fixed  # 修正【放学】按钮中逗号导致的轮廓增加1的问题
        if item_id > items_num:
            self.logger.error("Index out of range.")
        else:
            mouse_x = int(rect.width() / 2)
            mouse_y = int(rect.height() * (item_id * 2 - 1) / (items_num * 2))
            pop_win.click_input(coords=(mouse_x, mouse_y))  # 点击操作
            self.logger.debug("Coordinates: %s, %s" % (mouse_x, mouse_y))

    def click_launch_app(self):
        '''
        点击【运行应用程序】
        :return:
        '''
        # 点击【远程命令】
        self.main_win[self.configs['teachermain']['toolbar']['BtnRemoteCommand']].click()
        # 点击
        self.click_menu_btn(self.configs['teachermain']['RemoteCommandMenu']['StartApp'])

    def click_launch_webpage(self):
        '''
        点击【打开网页】
        :return:
        '''
        # 点击【远程命令】
        self.main_win[self.configs['teachermain']['toolbar']['BtnRemoteCommand']].click()
        # 点击
        self.click_menu_btn(self.configs['teachermain']['RemoteCommandMenu']['OpenWeb'])

    def get_data_grid_list(self, grid):
        data_list= grid.children()
        items = {}
        for app in data_list:
            if app.friendly_class_name() == 'ListItem':
                items[app.window_text()] = app
        return items

    def add_app(self, runapp_win):
        runapp_win.window(**self.configs['teachermain']['run_app']['add_btn']).click()
        add_win = runapp_win.window(**self.configs['teachermain']['run_app']['add_pane']['id'])
        add_win.window(**self.configs['teachermain']['run_app']['add_pane']['name']).type_keys(
            self.configs['teachermain']['remote_app']['app_name'])
        add_win.window(**self.configs['teachermain']['run_app']['add_pane']['excute_path']).type_keys(
            self.configs['teachermain']['remote_app']['app_path'])
        add_win.window(**self.configs['teachermain']['run_app']['add_pane']['parameter']).type_keys(
            self.configs['teachermain']['remote_app']['app_arg'])
        add_win.window(**self.configs['teachermain']['run_app']['add_pane']['window_mode']).click()
        add_win.window(**self.configs['teachermain']['remote_app']['app_mode']).wrapper_object().click_input()
        add_win.window(**self.configs['teachermain']['run_app']['add_pane']['ok']).click()
        add_win.wait_not('visible', timeout=10)

    def add_web_page(self, webpage_win):
        webpage_win.window(**self.configs['teachermain']['open_webpage']['add_btn']).click()
        add_win = webpage_win.window(**self.configs['teachermain']['open_webpage']['add_pane']['id'])
        add_win.window(**self.configs['teachermain']['open_webpage']['add_pane']['name']).type_keys(
            self.configs['teachermain']['remote_page']['page_name'])
        add_win.window(**self.configs['teachermain']['open_webpage']['add_pane']['page_url']).type_keys(
            self.configs['teachermain']['remote_page']['page_url'])
        add_win.window(**self.configs['teachermain']['open_webpage']['add_pane']['ok']).click()
        add_win.wait_not('visible', timeout=10)

    def click_remote_run(self, pop_win, item_name, type=0):
        '''
        远程应用中弹出框的操作流程
        :param pop_win:
        :param item_name:
        :param type: 0 运行应用程序，1 打开网页
        :return:
        '''
        # app_name=self.configs['teachermain']['remote_app']['app_name']
        pop_win.wait('visible', timeout=10)
        grid = pop_win.window(**self.configs['teachermain']['pop_win']['data_grid'])
        data_list = self.get_data_grid_list(grid)
        if item_name not in data_list.keys():
            if  type== 0:
                self.add_app(pop_win)
            if type == 1:
                self.add_web_page(pop_win)
            data_list = self.get_data_grid_list(grid)
        data_list[item_name].click_input()  # 选中
        pop_win.window(**self.configs['teachermain']['pop_win']['remote_btn']).click()# 点击【远程执行】
        pop_win.window(**self.configs['teachermain']['pop_win']['exit']).click()

    def click_remote_app_run(self, app_name):
        runapp_win = self.main_win.window(**self.configs['teachermain']['run_app']['id'])
        runapp_win.wait('visible', timeout=10)
        self.click_remote_run(runapp_win, app_name, 0)

    def click_remote_open_webpage(self, page_name):
        open_webpage_win = self.main_win.window(**self.configs['teachermain']['open_webpage']['id'])
        open_webpage_win.wait('visible', timeout=10)
        self.click_remote_run(open_webpage_win, page_name, 1)

    def click_lesson(self, lesson_name):
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        lesson_win.wait('visible', timeout=30)
        lessons = self.get_lesson_list(lesson_win)
        for lesson in lessons.keys():
            #self.logger.debug("Lesson: %s." % lesson)
            if lesson_name == lesson:
                if len(lessons) > 1:    # 单个课程，不需点击
                    lessons[lesson_name].click()
                dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
                dialog_confirm.window(**self.configs['lesson_win']['confirm']['ok']).click()
                lesson_win.wait_not('visible', timeout=60)
            elif lesson_name in lesson and '\r\n(上课中...)' in lesson:
                self.logger.debug("%s is working." % lesson_name)
                lesson_win.window(**self.configs['lesson_win']['exit']).click()  # 关闭
            elif len(lessons) == 1: # 单个课程，且课程名称不匹配情况
                dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
                dialog_confirm.window(**self.configs['lesson_win']['confirm']['ng']).click()
                lesson_win.wait_not('visible', timeout=60)
            else:
                self.logger.debug("%s in config doesnot exists." % lesson_name)

    def get_lesson_list(self, lesson_win):
        '''课程选择窗口 \r\n(上课中...) '''
        lesson_list = lesson_win.window(**self.configs['lesson_win']['pane']['id']).children()
        lessons = {}
        for lesson in lesson_list:
            if lesson.class_name() == 'Button':
                lessons[lesson.window_text()] = lesson
        return lessons

    def start_lesson(self, lesson_name):
        ''' 上课 '''
        # 点击【课程控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnLesson']].click()
        # 点击【上课】
        self.click_menu_btn(self.configs['teachermain']['LessonMenu']['Start'])
        # 点击相应课程
        self.click_lesson(lesson_name)
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        lesson_win.wait_not('visible', timeout=60)

    def stop_lesson(self):
        ''' 下课 '''
        # 点击【课程控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnLesson']].click()
        # 点击【下课】
        self.click_menu_btn(self.configs['teachermain']['LessonMenu']['Stop'])
        #
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
        dialog_confirm.window(**self.configs['lesson_win']['confirm']['ok']).click()
        #sleep(60)
        #lesson_win.wait_not('visible', timeout=60)

    def restart_lesson(self):
        # 点击【课程控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnLesson']].click()
        # 点击【重启】
        self.click_menu_btn(self.configs['teachermain']['LessonMenu']['Restart'])
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
        dialog_confirm.window(**self.configs['lesson_win']['confirm']['ok']).click()
        #lesson_win.wait_not('visible', timeout=60)

    def click_class_over(self):
        # 点击【课程控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnLesson']].click()
        # 点击【放学】
        self.click_menu_btn(self.configs['teachermain']['LessonMenu']['ClassOver'])
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
        dialog_confirm.window(**self.configs['lesson_win']['confirm']['ok']).click()
        #lesson_win.wait_not('visible', timeout=60)

    def click_switch_local_mode(self):
        # 点击【课程控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnLesson']].click()
        # 点击【本地考试模式】
        self.click_menu_btn(self.configs['teachermain']['LessonMenu']['ExamMode'])
        lesson_win = Desktop(backend="uia").window(**self.configs['lesson_win']['id'])
        dialog_confirm = lesson_win.window(**self.configs['lesson_win']['confirm']['id'])
        dialog_confirm.window(**self.configs['lesson_win']['confirm']['ok']).click()
        #lesson_win.wait_not('visible', timeout=60)

    def click_tc_power_btn(self, btn):
        ''' 点击电源管理下的菜单按钮 '''
        # 点击【电源控制】
        self.main_win[self.configs['teachermain']['toolbar']['BtnPower']].click()
        #
        cv_img, pop_win = self.capture_dropdown_menu()
        self.click_menu_btn(btn)

    def click_clients_poweroff(self):
        ''' 关机终端 '''
        self.click_tc_power_btn(self.configs['teachermain']['PowerMenu']['Poweroff'])

    def click_clients_wakeup(self):
        ''' 唤醒终端 '''
        self.click_tc_power_btn(self.configs['teachermain']['PowerMenu']['Wakeup'])

    def click_clients_restart(self):
        ''' 重启终端 '''
        self.click_tc_power_btn(self.configs['teachermain']['PowerMenu']['Restart'])

    def click_host_wakeup(self):
        ''' 唤醒主机 '''
        self.click_tc_power_btn(self.configs['teachermain']['PowerMenu']['Wakeup_host'])

    def click_black_screen(self):
        ''' 点击【黑屏安静】
        :return:
        '''
        self.main_win[self.configs['teachermain']['RightSider']['toolbox']['BtnBlackScreen']].click()

    def click_cancel_black_screen(self):
        ''' 点击【取消黑屏安静】
        :return:
        '''
        self.main_win[self.configs['teachermain']['RightSider']['toolbox']['BtnCancelBlack']].click()

    def get_logon_time(self, timeout, offline=0):
        '''
        所有桌面全登录的时间计时
        :param timeout:
        :return:
        '''
        start_time = time()
        while True:
            end_time = time()
            total_time = end_time - start_time
            if self.get_offline_clients() == offline:
                break
            elif timeout > total_time:
                continue
            else:
                total_time = None
                self.logger.warning("timeout!")
                break
        return total_time

    def img_template_match(self, src, tpl):
        template = cv.imread(tpl, 0)
        w, h = template.shape[:2]

        img = cv.threshold(src, 200, 255, cv.THRESH_BINARY)[1]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
        wait_contours = cv.dilate(img, kernel, iterations=1)
        gray = cv.cvtColor(wait_contours, cv.COLOR_BGR2GRAY)
        bin = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)[1]
        gray_lap = cv.Laplacian(bin, -1, ksize=3)
        # cv.imshow('test1', gray_lap)
        cnts = cv.findContours(gray_lap, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        copy = src.copy()
        num = 0
        for i in range(len(cnts[1])):
            x, y, w, h = cv.boundingRect(cnts[1][i])
            if h > 30:
                crop = copy[y:(y + h), x:(x + w)]
                crop_gray = cv.cvtColor(crop, cv.COLOR_BGR2GRAY)
                res = cv.matchTemplate(crop_gray, template, cv.TM_CCOEFF_NORMED)
                threshold = 0.8  # 匹配程度大于%80的坐标y,x

                # 3.这边是Python/Numpy的知识，后面解释
                loc = np.where(res >= threshold)
                for pt in zip(*loc[::-1]):  # *号表示可选参数
                    # right_bottom = (pt[0] + w, pt[1] + h)
                    # cv.rectangle(img_rgb, pt, right_bottom, (0, 0, 255), 2)
                    num += 1
                    break
                    # cv.imshow(r'test', crop)
        return num

    def get_quiet_num(self):
        '''
        检测黑屏安静图标的数量
        :return:
        '''
        origin = self.capture_monitor_pane()
        template = os.path.join(configs['img']['full_path'], configs['img']['quiet'])
        num = self.img_template_match(origin, template)
        return num

    def get_remote_app_start_num(self):
        '''
        检测远程程序启动的数量，应用与素材必须一一匹配
        :return:
        '''
        origin = self.capture_monitor_pane()
        template = os.path.join(configs['img']['full_path'], configs['img']['app'])
        num = self.img_template_match(origin, template)
        return num

    def get_remote_page_start_num(self):
        '''
        检测远程网页打开的数量，页面与素材必须一一匹配
        :return:
        '''
        origin = self.capture_monitor_pane()
        template = os.path.join(configs['img']['full_path'], configs['img']['app'])
        num = self.img_template_match(origin, template)
        return num

    def click_enter_portal(self):
        '''
        点击【云校园】
        :return:
        '''
        # 点击【云校园】
        self.main_win[self.configs['teachermain']['toolbar']['BtnPortabl']].click()
        IvyCloud_win = Desktop(backend="uia").window(**self.configs['portal']['id'])
        IvyCloud_win.wait('visible', timeout=30)

    def click_enter_workspace(self):
        '''
        点击【作业空间】
        :return:
        '''
        # 点击【作业空间】
        self.main_win[self.configs['teachermain']['toolbar']['BtnWorkspace']].click()
        Workspace_win = Desktop(backend="uia").window(**self.configs['workspace']['id'])
        Workspace_win.wait('visible', timeout=30)

    def click_forbidden_net(self):
        '''
        点击【禁网】
        :return:
        '''
        # 点击【禁网】
        self.main_win[self.configs['teachermain']['toolbar']['BtnForbiddenNet']].click()

    def enter_policy_pane(self):
        '''进入策略视图'''
        self.main_win.window(**self.configs['teachermain']['left_sider']['policy_view']).click()
        policy_pane = self.main_win.window(**self.configs['teachermain']['policy_pane']['id'])
        policy_pane.wait('visible', timeout=30)
        return policy_pane

    def add_policy_item(self, policy_win, black=True):
        '''策略添加窗口中添加策略'''
        # 进入添加窗口
        policy_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['tab']['add_btn']).click()
        add_win = policy_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['add_win']['id'])
        add_win.wait('visible', timeout=30)
        # 添加策略
        if black:
            add_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['add_win']['url']).type_keys(
                configs['teachermain']['policy_black']['url'])
            add_win.window(
                **self.configs['teachermain']['policy_pane']['advance_win']['add_win']['description']).type_keys(
                configs['teachermain']['policy_black']['description'])
        else:
            add_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['add_win']['url']).type_keys(
                configs['teachermain']['policy_white']['url'])
            add_win.window(
                **self.configs['teachermain']['policy_pane']['advance_win']['add_win']['description']).type_keys(
                configs['teachermain']['policy_white']['description'])
        add_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['add_win']['ok']).click()

    def add_white_black_policy(self, black=True):
        '''添加黑白名单策略'''
        # 进入策略视图
        policy_pane = self.enter_policy_pane()
        policy_pane.window(**self.configs['teachermain']['policy_pane']['toolbar']['advance_btn']).click()
        # 网页限制窗口
        policy_win = self.main_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['id'])
        policy_win.wait('visible', timeout=30)
        # 判断黑白名单
        if black:
            policy_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['black_tab']).wrapper_object().click_input()
        # 添加策略
        self.add_policy_item(policy_win, black)
        # 保存策略
        policy_win.window(**self.configs['teachermain']['policy_pane']['advance_win']['btn_dialog']['ok_btn']).click()

    def apply_whitelist_policy(self):
        '''应用白名单'''
        policy_pane = self.enter_policy_pane()
        policy_pane.window(**self.configs['teachermain']['policy_pane']['toolbar']['whitelist_btn']).click()

    def apply_blacklist_policy(self):
        '''应用黑名单'''
        policy_pane = self.enter_policy_pane()
        policy_pane.window(**self.configs['teachermain']['policy_pane']['toolbar']['blacklist_btn']).click()

    def apply_allopen_policy(self):
        '''应用全部开放'''
        policy_pane = self.enter_policy_pane()
        policy_pane.window(**self.configs['teachermain']['policy_pane']['toolbar']['allopen_btn']).click()

    def get_clients_policy(self):
        policy_pane = self.enter_policy_pane()
        clients_pane = policy_pane.window(**self.configs['teachermain']['policy_pane']['clients_grid'])
        items = self.get_data_grid_list(clients_pane)
        return items

    def is_all_policy(self, policy_name):
        '''所有客户端策略是否相同'''
        items = self.get_clients_policy()
        policy_num = sum([policy_name in  x.texts() for x in items.values()])
        return policy_num == len(items)

    def is_all_blacklist(self):
        return self.is_all_policy(self.configs['teachermain']['policy_pane']['policy_status']['blacklist'])

    def is_all_whitelist(self):
        return self.is_all_policy(self.configs['teachermain']['policy_pane']['policy_status']['whitelist'])

    def is_all_allopen(self):
        return self.is_all_policy(self.configs['teachermain']['policy_pane']['policy_status']['allopen'])

if __name__ == '__main__':
    launch = Launch(configs)
    launch.start_teacher_main()
    import time
    #time.sleep(5)
    teacher = TeachingMain(configs)
    #teacher.start_lesson(configs['teachermain']['stability']['lesson_name'])
    #time.sleep(configs['teachermain']['stability']['wait'])
    #offline = teacher.get_offline_clients()
    #print(offline)
    #teacher.stop_lesson()
    #teacher.click_clients_poweroff()
    #time.sleep(30)
    #teacher.click_clients_wakeup()
    #time.sleep(30)
    # 测试黑屏安静
    #teacher.click_black_screen()
    # 测试主机唤醒
    #teacher.click_host_wakeup()
    #time.sleep(30)
    # 截取屏幕
    #img = teacher.capture_monitor_pane()
    #cv.imwrite(r'e:\png\app_launch.png', img)
    # 测试启动应用程序
    #teacher.click_launch_app()
    #teacher.click_remote_app_run(configs['teachermain']['remote_app']['app_name'])

    teacher.click_launch_webpage()
    teacher.click_remote_open_webpage(configs['teachermain']['remote_page']['page_name'])

    #teacher.add_white_black_policy(False)
    #teacher.apply_white_policy()

    #teacher.get_clients_policy()

    time.sleep(30)
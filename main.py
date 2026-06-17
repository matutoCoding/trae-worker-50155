#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检测实验室试剂耗材出入库管理系统
主入口文件
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪一剪 - 表情包分割器 V2.0 (PyQt6版本)
主程序入口
"""
import sys
import os

# 添加当前目录到路径 - 方案3的建议
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window_qt import MainWindowQt

def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("剪一剪")
        app.setOrganizationName("表情包工具")
        
        window = MainWindowQt()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
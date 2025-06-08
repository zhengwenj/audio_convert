#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频格式转换工具主程序入口
"""
import platform
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from config.settings import APP_NAME, APP_VERSION
from gui.main_window import MainWindow


def setup_exception_handling():
    """设置全局异常处理"""
    def show_exception_box(exctype, value, tb):
        """显示异常对话框"""
        traceback_str = ''.join(traceback.format_exception(exctype, value, tb))
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("程序错误")
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(f"程序发生未处理的异常:\n{str(value)}")
        msg_box.setDetailedText(traceback_str)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
        # 调用原始的异常处理
        sys.__excepthook__(exctype, value, tb)
        
    sys.excepthook = show_exception_box


def check_environment():
    """检查运行环境"""
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("警告: 推荐使用Python 3.9或更高版本")
        
    # 检查操作系统
    system = platform.system()
    if system == "Windows":
        if int(platform.release()) < 10:
            print("警告: 推荐使用Windows 10或更高版本")
    elif system == "Darwin":  # macOS
        mac_version = tuple(map(int, platform.mac_ver()[0].split('.')))
        if mac_version < (10, 14):
            print("警告: 推荐使用macOS 10.14或更高版本")
    elif system == "Linux":
        # 这里可以添加Linux发行版的检查
        pass
    else:
        print(f"警告: 未测试的操作系统: {system}")
        
    # 检查FFmpeg
    try:
        import ffmpeg
        print("FFmpeg已安装")
    except ImportError:
        print("警告: 未找到ffmpeg-python库")
    except Exception as e:
        print(f"警告: FFmpeg检查失败: {str(e)}")


def main():
    """主函数"""
    # 检查环境
    check_environment()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # 设置高DPI支持
    # PyQt6中这些属性已经默认启用，不需要显式设置
    # 如果需要禁用高DPI缩放，可以使用Qt.AA_DisableHighDpiScaling
    
    # 设置全局样式
    app.setStyle("Fusion")
    
    # 设置异常处理
    setup_exception_handling()
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
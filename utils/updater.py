"""
更新检查模块
"""
import json
import os
import re
import sys  # 添加缺少的sys模块导入
import threading
import urllib.error
import urllib.request
from urllib.parse import urlparse, quote, unquote
from typing import Optional, Tuple, Callable

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QHBoxLayout
)

from config.settings import APP_VERSION, APP_NAME, settings

# 自定义API服务器URL
UPDATE_API_URL = "http://127.0.0.1:8080/api/test"

# 测试模式：True表示使用模拟响应，False表示使用实际API请求
TEST_MODE = False

def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    解析版本号为元组，用于比较
    例如: "1.0.0" -> (1, 0, 0)
    """
    # 移除可能的'v'前缀
    if version_str.startswith('v'):
        version_str = version_str[1:]
        
    # 使用正则表达式提取版本号部分
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$', version_str)
    if not match:
        return (0, 0, 0)  # 无效版本号返回0
        
    major, minor, patch = map(int, match.group(1, 2, 3))
    return (major, minor, patch)


def compare_versions(current_version: str, latest_version: str) -> bool:
    """
    比较版本号，如果latest_version比current_version新，返回True
    """
    current = parse_version(current_version)
    latest = parse_version(latest_version)
    
    return latest > current


def get_mock_update_info() -> dict:
    """
    获取模拟的更新信息（仅用于测试）
    """
    # 模拟API响应格式
    return {
        "code": 200,
        "data": {
            "version": "1.0.1",  # 比当前版本高一个补丁版本
            "url": "https://example.com/downloads/audio-convert/latest",
            "description": "1. 修复了一些bug\n2. 改进了用户界面\n3. 优化了转换性能"
        }
    }


def get_latest_version_from_api() -> Optional[dict]:
    """
    从自定义API服务器获取最新版本信息
    
    返回:
        dict: 包含版本信息的字典，如果出错返回None
    """
    # 测试模式下返回模拟数据
    if TEST_MODE:
        mock_response = get_mock_update_info()
        # 检查模拟响应是否符合预期格式
        if mock_response.get("code") == 200 and "data" in mock_response:
            return mock_response["data"]
        return None
        
    try:
        # 添加User-Agent头和当前版本信息
        headers = {
            'User-Agent': f'{APP_NAME}/{APP_VERSION}',
            'Content-Type': 'application/json'
        }
        
        # 准备请求数据
        data = json.dumps({
            'current_version': APP_VERSION,
            'app_name': APP_NAME,
            'platform': 'windows'  # 可以根据实际平台动态设置
        }).encode('utf-8')
        
        # 创建请求
        req = urllib.request.Request(
            UPDATE_API_URL, 
            data=data,
            headers=headers,
            method='POST'
        )
        
        # 发送请求并获取响应
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # 检查响应格式是否符合预期
            if result.get("code") == 200 and "data" in result:
                data = result["data"]
                # 确保必要的字段存在
                if "version" in data and "url" in data:
                    return data
                    
            print("API响应格式不正确")
            return None
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"获取更新信息失败: {str(e)}")
        return None


class DownloadSignals(QObject):
    """下载信号类，用于在下载线程中传递信号"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


def download_file(url: str, save_path: str, signals: DownloadSignals) -> None:
    """
    下载文件
    
    参数:
        url: 下载链接
        save_path: 保存路径
        signals: 信号对象，用于通知下载进度和状态
    """
    try:
        # 处理URL中的中文字符
        parsed_url = urlparse(url)
        # 对路径部分进行编码，保留原始的协议和域名
        encoded_path = quote(parsed_url.path, safe='/')
        # 重新组合URL
        if parsed_url.query:
            encoded_query = quote(parsed_url.query, safe='=&')
            encoded_url = f"{parsed_url.scheme}://{parsed_url.netloc}{encoded_path}?{encoded_query}"
        else:
            encoded_url = f"{parsed_url.scheme}://{parsed_url.netloc}{encoded_path}"
            
        print(f"原始URL: {url}")
        print(f"编码后URL: {encoded_url}")
        
        # 创建请求
        req = urllib.request.Request(
            encoded_url,
            headers={'User-Agent': f'{APP_NAME}/{APP_VERSION}'}
        )
        
        # 打开URL
        with urllib.request.urlopen(req) as response:
            # 获取文件大小
            file_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 创建文件
            with open(save_path, 'wb') as f:
                # 每次读取的块大小
                block_size = 8192
                
                while True:
                    # 读取数据块
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                        
                    # 写入文件
                    f.write(buffer)
                    
                    # 更新下载大小
                    downloaded_size += len(buffer)
                    
                    # 计算进度百分比
                    if file_size > 0:
                        progress = int((downloaded_size / file_size) * 100)
                        signals.progress.emit(progress)
        
        # 下载完成
        signals.finished.emit(save_path)
    except Exception as e:
        # 下载出错
        signals.error.emit(str(e))
        
        # 如果文件已创建但下载失败，删除文件
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass


class UpdateSignals(QObject):
    """更新信号类，用于在线程间传递信号"""
    update_available = pyqtSignal(dict)
    no_update = pyqtSignal()
    error = pyqtSignal(str)


def check_for_updates(callback: Optional[Callable] = None, show_if_not_available: bool = False) -> None:
    """
    检查更新
    
    参数:
        callback: 检查完成后的回调函数，接收一个参数(更新信息字典或None)
        show_if_not_available: 如果没有更新，是否也显示消息
    """
    print(f"开始检查更新, 当前版本: {APP_VERSION}")
    
    # 检查是否启用了更新检查
    if not settings.get("general", "check_updates", True):
        print("更新检查已禁用")
        return
        
    # 检查是否忽略了特定版本
    ignored_version = settings.get("general", "ignored_version", "")
    if ignored_version:
        print(f"已忽略版本: {ignored_version}")
    
    # 创建进度对话框
    progress_dialog = None
    if show_if_not_available:
        progress_dialog = QDialog()
        progress_dialog.setWindowTitle("检查更新")
        progress_dialog.setFixedSize(300, 100)
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(progress_dialog)
        layout.addWidget(QLabel("正在检查更新..."))
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # 设置为不确定模式
        layout.addWidget(progress_bar)
        
        # 5秒后如果还没结果，自动关闭
        QTimer.singleShot(5000, progress_dialog.close)
        
        # 显示对话框但不阻塞
        progress_dialog.show()
    
    # 创建信号对象，用于线程间通信
    signals = UpdateSignals()
    
    # 连接信号到槽函数
    def on_update_available(update_info):
        if progress_dialog and progress_dialog.isVisible():
            progress_dialog.close()
        show_update_dialog(update_info)
        if callback:
            callback(update_info)
            
    def on_no_update():
        if show_if_not_available:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.close()
                
            msg = QMessageBox()
            msg.setWindowTitle("检查更新")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"您正在使用最新版本 {APP_VERSION}。")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        if callback:
            callback(None)
            
    def on_error(error_msg):
        if show_if_not_available:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.close()
                
            msg = QMessageBox()
            msg.setWindowTitle("检查更新")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"检查更新失败: {error_msg}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        if callback:
            callback(None)
    
    signals.update_available.connect(on_update_available)
    signals.no_update.connect(on_no_update)
    signals.error.connect(on_error)
    
    def _check_update_thread():
        """后台线程检查更新"""
        print("正在获取最新版本信息...")
        update_info = get_latest_version_from_api()
        
        if update_info:
            print(f"获取到版本信息: {update_info['version']}")
            
            if compare_versions(APP_VERSION, update_info['version']):
                print(f"有新版本可用: {update_info['version']}")
                
                # 检查是否忽略了该版本
                if ignored_version == update_info['version']:
                    print(f"用户已忽略此版本: {update_info['version']}")
                    signals.no_update.emit()
                    return
                    
                # 有更新可用
                print("准备显示更新对话框")
                signals.update_available.emit(update_info)
            else:
                print(f"已是最新版本: {APP_VERSION}")
                signals.no_update.emit()
        else:
            print("获取更新信息失败")
            signals.error.emit("无法连接到更新服务器")
    
    # 在后台线程中执行，避免阻塞UI
    threading.Thread(target=_check_update_thread, daemon=True).start()


def show_download_dialog(url: str, version: str) -> None:
    """
    显示下载对话框
    
    参数:
        url: 下载链接
        version: 版本号
    """
    # 创建下载对话框
    dialog = QDialog()
    dialog.setWindowTitle("下载更新")
    dialog.setFixedSize(400, 150)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    
    # 创建布局
    layout = QVBoxLayout(dialog)
    
    # 添加标签
    layout.addWidget(QLabel(f"正在下载 {APP_NAME} {version}..."))
    
    # 添加进度条
    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)
    layout.addWidget(progress_bar)
    
    # 添加状态标签
    status_label = QLabel("准备下载...")
    layout.addWidget(status_label)
    
    # 添加按钮
    button_layout = QHBoxLayout()
    cancel_button = QPushButton("取消")
    button_layout.addStretch()
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    
    # 创建信号对象
    signals = DownloadSignals()
    
    # 连接信号
    def on_progress(value):
        progress_bar.setValue(value)
        status_label.setText(f"下载中... {value}%")
        
    def on_finished(save_path):
        status_label.setText("下载完成!")
        progress_bar.setValue(100)
        
        # 关闭对话框
        dialog.accept()
        
        # 显示下载完成对话框
        msg = QMessageBox()
        msg.setWindowTitle("下载完成")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"{APP_NAME} {version} 已下载完成")
        msg.setInformativeText(f"文件已保存到:\n{save_path}")
        
        open_folder_button = msg.addButton("打开文件夹", QMessageBox.ButtonRole.ActionRole)
        run_button = msg.addButton("立即安装", QMessageBox.ButtonRole.AcceptRole)
        close_button = msg.addButton("关闭", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        clicked_button = msg.clickedButton()
        
        if clicked_button == open_folder_button:
            # 打开文件夹
            import subprocess
            import os
            folder_path = os.path.dirname(save_path)
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', folder_path])
        elif clicked_button == run_button:
            # 运行安装程序
            import subprocess
            import sys
            if sys.platform == 'win32':
                subprocess.Popen([save_path], shell=True)
            else:
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', save_path])
        
    def on_error(error_msg):
        status_label.setText(f"下载失败: {error_msg}")
        cancel_button.setText("关闭")
    
    signals.progress.connect(on_progress)
    signals.finished.connect(on_finished)
    signals.error.connect(on_error)
    
    # 获取保存路径
    default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # 尝试从URL中提取文件名
    try:
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)  # 解码URL路径
        url_filename = os.path.basename(url_path)
        # 如果URL中有文件名，使用它
        if url_filename and '.' in url_filename:
            # 确保文件名是安全的
            import re
            # 替换不安全的文件名字符
            safe_filename = re.sub(r'[\\/*?:"<>|]', "_", url_filename)
            default_filename = safe_filename
        else:
            # 否则使用应用名和版本号
            safe_app_name = APP_NAME.lower().replace(' ', '_')
            default_filename = f"{safe_app_name}_{version}.exe"
    except:
        # 出错时使用默认命名
        safe_app_name = APP_NAME.lower().replace(' ', '_')
        default_filename = f"{safe_app_name}_{version}.exe"
    
    save_path = os.path.join(default_dir, default_filename)
    
    # 检查目录是否存在，不存在则创建
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 取消按钮点击事件
    download_thread = [None]  # 使用列表存储线程引用，以便在lambda中修改
    
    def on_cancel_clicked():
        if download_thread[0] and download_thread[0].is_alive():
            # 线程无法直接停止，但我们可以关闭对话框
            dialog.reject()
        else:
            dialog.reject()
    
    cancel_button.clicked.connect(on_cancel_clicked)
    
    # 启动下载线程
    def download_thread_func():
        download_file(url, save_path, signals)
    
    download_thread[0] = threading.Thread(target=download_thread_func)
    download_thread[0].daemon = True
    download_thread[0].start()
    
    # 显示对话框
    dialog.exec()


def show_update_dialog(update_info: dict) -> None:
    """
    显示更新对话框
    
    参数:
        update_info: 更新信息字典
    """
    print("显示更新对话框")
    
    msg = QMessageBox()
    msg.setWindowTitle("发现新版本")
    msg.setIcon(QMessageBox.Icon.Information)
    
    # 准备更新信息文本
    current_version = APP_VERSION
    new_version = update_info['version']
    description = update_info['description']
    
    print(f"当前版本: {current_version}, 新版本: {new_version}")
    
    # 限制描述长度，避免对话框过大
    if len(description) > 300:
        description = description[:297] + "..."
    
    msg.setText(f"发现新版本: {new_version}\n当前版本: {current_version}")
    msg.setInformativeText(f"更新内容:\n{description}")
    
    # 添加按钮
    download_button = msg.addButton("直接下载", QMessageBox.ButtonRole.AcceptRole)
    browser_button = msg.addButton("浏览器下载", QMessageBox.ButtonRole.ActionRole)
    ignore_button = msg.addButton("忽略此版本", QMessageBox.ButtonRole.RejectRole)
    remind_button = msg.addButton("稍后提醒", QMessageBox.ButtonRole.ActionRole)
    
    print("准备显示对话框")
    msg.exec()
    print("对话框已关闭")
    
    clicked_button = msg.clickedButton()
    
    if clicked_button == download_button:
        print("用户选择直接下载")
        # 直接下载更新
        show_download_dialog(update_info['url'], new_version)
    elif clicked_button == browser_button:
        print("用户选择浏览器下载")
        # 打开浏览器下载页面
        import webbrowser
        webbrowser.open(update_info['url'])
    elif clicked_button == ignore_button:
        print("用户选择忽略此版本")
        # 记住忽略的版本
        settings.set("general", "ignored_version", new_version)
        settings.save_settings()
    else:
        print("用户选择稍后提醒") 
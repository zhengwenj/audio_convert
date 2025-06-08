"""
主窗口界面
"""
import os
import sys
import time
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox,
    QTabWidget, QSplitter, QProgressBar, QStatusBar, QToolBar,
    QStyle, QMenu, QListWidget, QListWidgetItem, QFrame,
    QCheckBox, QSpinBox, QLineEdit, QGroupBox, QDialog, QProgressDialog,
    QFormLayout
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QIcon, QAction, QFont, QDragEnterEvent, QDropEvent
import qtawesome as qta

from config.settings import settings
from gui.widgets import FileListWidget, ConversionSettingsWidget, WaveformWidget
from core.converter import AudioConverter
from core.formats import get_all_supported_formats, get_format_info
from core.errors import AudioConvertError
from utils.updater import check_for_updates


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle("Audio Convert - 音频格式转换工具")
        self.setMinimumSize(900, 600)
        
        # 从设置中恢复窗口大小和位置
        window_size = settings.get("ui", "window_size")
        window_position = settings.get("ui", "window_position")
        window_maximized = settings.get("ui", "window_maximized")
        
        if window_size:
            self.resize(window_size[0], window_size[1])
        if window_position:
            self.move(window_position[0], window_position[1])
        if window_maximized:
            self.showMaximized()
            
        # 设置应用图标
        self.setWindowIcon(qta.icon('fa5s.music', color='#1976D2'))
        
        # 初始化转换器
        self.converter = AudioConverter()
        
        # 设置接受拖放
        self.setAcceptDrops(True)
        
        # 当前任务状态
        self.current_task = None
        self.conversion_in_progress = False
        
        # 文件信息线程
        self.file_info_thread = None
        
        # 初始化UI组件
        self.init_ui()
        
        # 自动检查更新
        if settings.get("general", "check_updates") and settings.get("general", "check_updates_on_startup"):
            # 延迟2秒检查，避免影响启动速度
            QTimer.singleShot(2000, self.check_for_updates_silently)
        
    def init_ui(self):
        """初始化UI组件"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 上半部分 - 文件列表和设置
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 获取文件列表和设置面板的比例
        file_list_ratio = settings.get("ui", "file_list_ratio", 8)
        settings_ratio = settings.get("ui", "settings_ratio", 2)
        
        # 左侧 - 文件列表
        self.file_list_widget = FileListWidget()
        top_layout.addWidget(self.file_list_widget, file_list_ratio)
        
        # 右侧 - 转换设置
        self.settings_widget = ConversionSettingsWidget()
        top_layout.addWidget(self.settings_widget, settings_ratio)
        
        main_layout.addWidget(top_widget, 9)  # 文件列表和设置占据90%的空间
        
        # 下半部分 - 只保留进度条
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 简单的文件信息标签
        self.file_info_label = QLabel("未选择文件")
        self.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_info_label.setStyleSheet("font-size: 12px; color: #666666; padding: 5px;")
        bottom_layout.addWidget(self.file_info_label)
        
        # 进度条和状态
        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m")
        progress_layout.addWidget(self.progress_bar)
        
        self.convert_button = QPushButton("开始转换")
        self.convert_button.setIcon(qta.icon('fa5s.play', color='white'))
        self.convert_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.convert_button.clicked.connect(self.start_conversion)
        progress_layout.addWidget(self.convert_button)
        
        bottom_layout.addWidget(progress_widget)
        
        main_layout.addWidget(bottom_widget, 1)  # 进度条占据10%的空间
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 连接信号
        self.file_list_widget.files_changed.connect(self.update_ui_state)
        self.file_list_widget.file_selected.connect(self.show_file_info)
        self.settings_widget.settings_changed.connect(self.update_ui_state)
        
        # 初始化UI状态
        self.update_ui_state()
        
    def create_toolbar(self):
        """创建工具栏"""
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # 添加文件
        add_file_action = QAction(qta.icon('fa5s.file-audio', color='#1976D2'), "添加文件", self)
        add_file_action.triggered.connect(self.add_files)
        self.toolbar.addAction(add_file_action)
        
        # 添加文件夹
        add_folder_action = QAction(qta.icon('fa5s.folder-open', color='#1976D2'), "添加文件夹", self)
        add_folder_action.triggered.connect(self.add_folder)
        self.toolbar.addAction(add_folder_action)
        
        # 清空列表
        clear_action = QAction(qta.icon('fa5s.trash-alt', color='#F44336'), "清空列表", self)
        clear_action.triggered.connect(self.clear_files)
        self.toolbar.addAction(clear_action)
        
        self.toolbar.addSeparator()
        
        # 开始转换
        start_action = QAction(qta.icon('fa5s.play', color='#4CAF50'), "开始转换", self)
        start_action.triggered.connect(self.start_conversion)
        self.toolbar.addAction(start_action)
        
        # 停止转换
        stop_action = QAction(qta.icon('fa5s.stop', color='#F44336'), "停止转换", self)
        stop_action.triggered.connect(self.stop_conversion)
        stop_action.setEnabled(False)
        self.toolbar.addAction(stop_action)
        self.stop_action = stop_action
        
        self.toolbar.addSeparator()
        
        # 设置
        settings_action = QAction(qta.icon('fa5s.cog', color='#607D8B'), "设置", self)
        settings_action.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_action)
        
        # 检查更新
        update_action = QAction(qta.icon('fa5s.sync', color='#607D8B'), "检查更新", self)
        update_action.triggered.connect(self.check_for_updates)
        self.toolbar.addAction(update_action)
        
        # 帮助
        help_action = QAction(qta.icon('fa5s.question-circle', color='#607D8B'), "帮助", self)
        help_action.triggered.connect(self.show_help)
        self.toolbar.addAction(help_action)
        
    def update_ui_state(self):
        """更新UI状态"""
        files_count = self.file_list_widget.count()
        has_files = files_count > 0
        
        # 更新状态栏
        if has_files:
            self.statusBar.showMessage(f"已添加 {files_count} 个文件")
        else:
            self.statusBar.showMessage("就绪")
            
        # 更新转换按钮状态
        self.convert_button.setEnabled(has_files and not self.conversion_in_progress)
        
        # 更新工具栏按钮状态
        for action in self.toolbar.actions():
            if action.text() == "开始转换":
                action.setEnabled(has_files and not self.conversion_in_progress)
            elif action.text() == "停止转换":
                action.setEnabled(self.conversion_in_progress)
            elif action.text() in ["清空列表", "添加文件", "添加文件夹"]:
                action.setEnabled(not self.conversion_in_progress)
                
    def add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.aiff *.ape *.ac3);;所有文件 (*.*)"
        )
        
        if files:
            self.file_list_widget.add_files(files)
            
    def add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            ""
        )
        
        if folder:
            recursive = QMessageBox.question(
                self,
                "递归添加",
                "是否包含子文件夹中的音频文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes
            
            self.file_list_widget.add_folder(folder, recursive)
            
    def clear_files(self):
        """清空文件列表"""
        self.file_list_widget.clear()
        
    def show_file_info(self, file_path):
        """显示文件信息"""
        if not file_path:
            self.file_info_label.setText("未选择文件")
            return
            
        # 显示加载中状态
        self.file_info_label.setText("加载文件信息中...")
        
        # 停止之前的线程（如果有）
        if self.file_info_thread and self.file_info_thread.isRunning():
            self.file_info_thread.stop()
            
        # 创建并启动新的文件信息线程
        self.file_info_thread = FileInfoThread(file_path)
        self.file_info_thread.info_loaded.connect(self._on_file_info_loaded)
        self.file_info_thread.error_occurred.connect(self._on_file_info_error)
        self.file_info_thread.start()
        
    def _on_file_info_loaded(self, file_path, info):
        """文件信息加载完成的回调"""
        # 构建显示文本
        if info['duration'] is not None:
            info_text = (
                f"文件: {info['file_name']} | "
                f"大小: {info['file_size']:.2f} MB | "
                f"时长: {int(info['duration'] // 60)}:{int(info['duration'] % 60):02d} | "
                f"声道: {info['channels']} | "
                f"采样率: {info['sample_rate']} Hz"
            )
        else:
            # 如果无法获取音频信息，只显示基本文件信息
            info_text = f"文件: {info['file_name']} | 大小: {info['file_size']:.2f} MB"
        
        self.file_info_label.setText(info_text)
        
    def _on_file_info_error(self, file_path, error_msg):
        """文件信息加载错误的回调"""
        self.file_info_label.setText(f"无法读取文件信息: {error_msg}")
        
    def start_conversion(self):
        """开始转换"""
        # 检查是否已有转换在进行
        if self.conversion_in_progress:
            QMessageBox.warning(self, "警告", "已有转换任务正在进行中")
            return
            
        # 获取文件列表
        files = self.file_list_widget.get_all_files()
        if not files:
            QMessageBox.warning(self, "警告", "请先添加要转换的文件")
            return
            
        # 获取转换设置
        output_format = self.settings_widget.get_output_format()
        output_dir = self.settings_widget.get_output_directory()
        
        # 检查输出目录
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
            
        # 确保输出目录存在
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建输出目录失败: {str(e)}")
            return
            
        # 获取转换参数
        params = self.settings_widget.get_params()
        
        # 创建转换器
        converter = AudioConverter()
        
        # 创建并启动转换线程
        self.conversion_thread = ConversionThread(
            converter,
            files,
            output_format,
            output_dir,
            params
        )
        
        # 连接信号
        self.conversion_thread.progress_updated.connect(self.update_progress)
        self.conversion_thread.conversion_finished.connect(self.conversion_finished)
        self.conversion_thread.error_occurred.connect(self.conversion_error)
        
        # 更新UI状态
        self.conversion_in_progress = True
        self.update_ui_state()
        
        # 开始转换
        self.conversion_thread.start()
        self.statusBar.showMessage("开始转换...")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def stop_conversion(self):
        """停止转换"""
        if not self.conversion_in_progress or not hasattr(self, 'conversion_thread'):
            return
            
        # 更新UI状态
        self.statusBar.showMessage("正在停止转换...")
        
        # 禁用停止按钮，防止重复点击
        for action in self.toolbar.actions():
            if action.text() == "停止转换":
                action.setEnabled(False)
                break
                
        # 停止转换线程
        try:
            self.conversion_thread.stop()
            
            # 添加一个定时器，如果线程在一定时间内没有停止，则更新UI状态
            QTimer.singleShot(2000, self._check_conversion_stopped)
        except Exception as e:
            self.statusBar.showMessage(f"停止转换失败: {str(e)}")
            self.conversion_in_progress = False
            self.update_ui_state()
            
    def _check_conversion_stopped(self):
        """检查转换是否已停止"""
        if hasattr(self, 'conversion_thread') and self.conversion_thread.isRunning():
            # 线程仍在运行
            self.statusBar.showMessage("停止转换中，请稍候...")
            
            # 再次检查
            QTimer.singleShot(1000, self._check_conversion_stopped)
        else:
            # 线程已停止
            if self.conversion_in_progress:
                self.conversion_in_progress = False
                self.update_ui_state()
                self.statusBar.showMessage("转换已停止")
                
    def update_progress(self, file_index, progress):
        """更新转换进度"""
        if not self.conversion_in_progress:
            return
            
        # 获取文件总数
        total_files = len(self.file_list_widget.get_all_files())
        if total_files == 0:
            return
            
        # 计算总体进度
        overall_progress = (file_index + progress) / total_files * 100
        
        # 更新进度条
        self.progress_bar.setValue(int(overall_progress))
        
        # 更新状态栏
        current_file = os.path.basename(self.file_list_widget.get_all_files()[file_index])
        self.statusBar.showMessage(f"正在转换 ({file_index + 1}/{total_files}): {current_file} - {int(progress * 100)}%")
        
    def conversion_finished(self, success_count, failed_count):
        """转换完成"""
        self.conversion_in_progress = False
        self.update_ui_state()
        
        # 特殊情况：被用户停止的转换
        if success_count == -1 and failed_count == -1:
            self.statusBar.showMessage("转换已被用户停止")
            return
            
        message = f"转换完成: {success_count} 个成功, {failed_count} 个失败"
        self.statusBar.showMessage(message)
        
        if failed_count == 0:
            QMessageBox.information(self, "转换完成", f"成功转换 {success_count} 个文件")
        else:
            QMessageBox.warning(
                self,
                "转换完成",
                f"转换完成，但有 {failed_count} 个文件失败\n成功: {success_count} 个文件"
            )
            
    def conversion_error(self, error_message):
        """转换错误"""
        self.conversion_in_progress = False
        self.update_ui_state()
        self.statusBar.showMessage(f"转换错误: {error_message}")
        
        QMessageBox.critical(self, "转换错误", error_message)
        
    def show_settings(self):
        """显示设置对话框"""
        # 创建简单的设置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QVBoxLayout(ui_group)
        
        # 文件列表比例设置
        file_list_layout = QHBoxLayout()
        file_list_label = QLabel("文件列表占比:")
        file_list_spin = QSpinBox()
        file_list_spin.setRange(1, 10)
        file_list_spin.setValue(settings.get("ui", "file_list_ratio", 8))
        file_list_layout.addWidget(file_list_label)
        file_list_layout.addWidget(file_list_spin)
        ui_layout.addLayout(file_list_layout)
        
        layout.addWidget(ui_group)
        
        # 更新设置
        update_group = QGroupBox("更新设置")
        update_layout = QVBoxLayout(update_group)
        
        # 自动检查更新选项
        check_updates_check = QCheckBox("启用自动检查更新")
        check_updates_check.setChecked(settings.get("general", "check_updates", True))
        update_layout.addWidget(check_updates_check)
        
        # 启动时检查更新选项
        check_updates_on_startup_check = QCheckBox("启动时检查更新")
        check_updates_on_startup_check.setChecked(settings.get("general", "check_updates_on_startup", True))
        check_updates_on_startup_check.setEnabled(check_updates_check.isChecked())
        update_layout.addWidget(check_updates_on_startup_check)
        
        # 连接信号，使启动时检查更新选项依赖于启用自动检查更新选项
        check_updates_check.stateChanged.connect(
            lambda state: check_updates_on_startup_check.setEnabled(state == Qt.CheckState.Checked.value)
        )
        
        layout.addWidget(update_group)
        
        # 转换设置
        conversion_group = QGroupBox("转换设置")
        conversion_layout = QVBoxLayout(conversion_group)
        
        # 保留原始音质选项
        preserve_quality_check = QCheckBox("默认保留原始音质")
        preserve_quality_check.setChecked(settings.get("conversion", "preserve_quality", True))
        conversion_layout.addWidget(preserve_quality_check)
        
        # 保留元数据选项
        preserve_metadata_check = QCheckBox("默认保留元数据")
        preserve_metadata_check.setChecked(settings.get("conversion", "preserve_metadata", True))
        conversion_layout.addWidget(preserve_metadata_check)
        
        layout.addWidget(conversion_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        result = dialog.exec()
        
        # 如果用户点击确定，保存设置
        if result == QDialog.DialogCode.Accepted:
            # 保存界面设置
            settings.set("ui", "file_list_ratio", file_list_spin.value())
            settings.set("ui", "settings_ratio", 10 - file_list_spin.value())  # 总和为10
            
            # 保存更新设置
            settings.set("general", "check_updates", check_updates_check.isChecked())
            settings.set("general", "check_updates_on_startup", check_updates_on_startup_check.isChecked())
            
            # 保存转换设置
            settings.set("conversion", "preserve_quality", preserve_quality_check.isChecked())
            settings.set("conversion", "preserve_metadata", preserve_metadata_check.isChecked())
            
            # 保存设置到文件
            settings.save_settings()
            
            # 应用文件列表比例设置
            self.apply_file_list_ratio()
            
            # 提示用户设置已保存
            QMessageBox.information(
                self,
                "设置已保存",
                "设置已保存并应用。"
            )
            
    def apply_file_list_ratio(self):
        """应用文件列表比例设置"""
        file_list_ratio = settings.get("ui", "file_list_ratio", 8)
        settings_ratio = settings.get("ui", "settings_ratio", 2)
        
        # 获取顶部布局
        top_widget = self.centralWidget().layout().itemAt(1).widget()
        top_layout = top_widget.layout()
        
        # 重新设置比例
        top_layout.setStretch(0, file_list_ratio)  # 文件列表
        top_layout.setStretch(1, settings_ratio)   # 设置面板
        
    def show_help(self):
        """显示帮助信息"""
        # TODO: 实现帮助对话框
        QMessageBox.information(
            self,
            "帮助",
            "Audio Convert - 音频格式转换工具\n\n"
            "使用方法:\n"
            "1. 点击'添加文件'或'添加文件夹'按钮添加音频文件\n"
            "2. 在右侧设置输出格式和参数\n"
            "3. 点击'开始转换'按钮开始转换\n\n"
            "支持拖放文件和文件夹到程序中"
        )
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖动进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        urls = event.mimeData().urls()
        
        files = []
        folders = []
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                folders.append(path)
                
        # 添加文件
        if files:
            self.file_list_widget.add_files(files)
            
        # 添加文件夹
        for folder in folders:
            recursive = QMessageBox.question(
                self,
                "递归添加",
                f"是否包含'{os.path.basename(folder)}'文件夹中的子文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes
            
            self.file_list_widget.add_folder(folder, recursive)
            
    def closeEvent(self, event):
        """关闭事件"""
        # 保存窗口状态
        settings.set("ui", "window_size", [self.width(), self.height()])
        settings.set("ui", "window_position", [self.x(), self.y()])
        settings.set("ui", "window_maximized", self.isMaximized())
        settings.save_settings()
        
        # 如果正在转换，询问是否退出
        if self.conversion_in_progress:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "转换任务正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        event.accept()

    def check_for_updates(self):
        """检查更新（显示结果）"""
        check_for_updates(show_if_not_available=True)
        
    def check_for_updates_silently(self):
        """静默检查更新（只在有更新时显示）"""
        check_for_updates(show_if_not_available=False)


class ConversionThread(QThread):
    """转换线程"""
    progress_updated = pyqtSignal(int, float)
    conversion_finished = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, converter, files, output_format, output_dir, params):
        super().__init__()
        self.converter = converter
        self.files = files
        self.output_format = output_format
        self.output_dir = output_dir
        self.params = params
        self._stopped = False
        self.batch_size = 10  # 批处理大小
        self._current_task = None  # 当前正在处理的任务
        
    def run(self):
        """线程运行函数"""
        success_count = 0
        failed_count = 0
        
        try:
            # 创建转换器实例
            converter = AudioConverter()
            
            # 定义进度回调函数
            def progress_callback(index, progress):
                # 检查是否需要停止
                if self._stopped:
                    raise InterruptedError("转换已被用户停止")
                self.progress_updated.emit(index, progress)
                
            # 开始转换
            success_count, failed_count = converter.batch_convert(
                self.files,
                self.output_dir,
                self.output_format,
                self.params,
                progress_callback
            )
            
            # 检查是否被停止
            if self._stopped:
                # 发送特殊信号表示转换被用户停止
                self.conversion_finished.emit(-1, -1)
                return
                
            # 转换完成，发出信号
            self.conversion_finished.emit(success_count, failed_count)
            
        except InterruptedError:
            # 用户中断转换
            self.conversion_finished.emit(-1, -1)
        except Exception as e:
            # 转换过程中出现错误
            self.error_occurred.emit(str(e))
            self.conversion_finished.emit(success_count, failed_count)
        finally:
            # 确保线程结束时重置停止标志
            self._stopped = False
        
    def stop(self):
        """停止线程"""
        self._stopped = True
        
        # 强制中断当前任务
        self.requestInterruption()  # 请求中断线程
        
        # 等待一小段时间，如果线程还在运行，则尝试终止它
        if not self.wait(100):  # 等待100毫秒
            # 线程仍在运行，发出警告信号
            self.error_occurred.emit("正在尝试停止转换，请稍候...")
            
            # 继续等待更长时间
            if not self.wait(1000):  # 再等待1秒
                # 如果仍然无法停止，通知用户
                self.error_occurred.emit("转换任务停止中，可能需要几秒钟完成...")
                
                # 继续等待，但不阻塞UI
                QTimer.singleShot(100, self._check_if_stopped)

    def _check_if_stopped(self):
        """检查线程是否停止"""
        if self.isFinished():
            return
            
        # 如果线程仍在运行，再次检查
        QTimer.singleShot(100, self._check_if_stopped) 


class FileInfoThread(QThread):
    """文件信息加载线程"""
    info_loaded = pyqtSignal(str, dict)  # 文件路径, 信息字典
    error_occurred = pyqtSignal(str, str)  # 文件路径, 错误信息
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.stopped = False
        
    def run(self):
        """运行线程"""
        if not self.file_path or not os.path.exists(self.file_path) or self.stopped:
            return
            
        try:
            # 获取基本文件信息
            file_name = os.path.basename(self.file_path)
            file_size = os.path.getsize(self.file_path) / (1024 * 1024)  # MB
            
            info = {
                'file_name': file_name,
                'file_size': file_size,
                'duration': None,
                'channels': None,
                'sample_rate': None
            }
            
            # 尝试获取音频信息
            try:
                # 导入放在这里，避免不必要的导入
                from pydub import AudioSegment
                
                # 检查线程是否被停止
                if self.stopped:
                    return
                    
                audio = AudioSegment.from_file(self.file_path)
                
                # 检查线程是否被停止
                if self.stopped:
                    return
                    
                info['duration'] = audio.duration_seconds
                info['channels'] = audio.channels
                info['sample_rate'] = audio.frame_rate
                
            except Exception as e:
                # 无法获取音频信息，但不影响基本文件信息的显示
                print(f"无法获取音频详细信息: {str(e)}")
                
            # 发送信号
            if not self.stopped:
                self.info_loaded.emit(self.file_path, info)
                
        except Exception as e:
            if not self.stopped:
                self.error_occurred.emit(self.file_path, str(e))
                
    def stop(self):
        """停止线程"""
        self.stopped = True
        
        # 等待线程结束
        if not self.wait(100):  # 等待100毫秒
            # 如果线程仍在运行，强制终止
            self.terminate()
            self.wait()  # 等待线程真正结束 
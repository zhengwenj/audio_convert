"""
自定义组件
"""
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QFileDialog,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QSlider, QSizePolicy, QFrame,
    QScrollArea, QMessageBox, QToolButton, QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QPixmap
import qtawesome as qta
from pydub import AudioSegment
import mutagen

# 设置matplotlib使用Qt6后端
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from core.formats import get_all_supported_formats, get_format_info
from config.settings import settings


class FileListWidget(QWidget):
    """文件列表组件"""
    
    # 自定义信号
    files_changed = pyqtSignal()
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self._files = []
        self.batch_size = 50  # 批量添加文件的大小
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("文件列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)
        
        # 添加文件按钮
        add_button = QToolButton()
        add_button.setIcon(qta.icon('fa5s.plus', color='#1976D2'))
        add_button.setToolTip("添加文件")
        add_button.clicked.connect(self.add_files_dialog)
        title_layout.addWidget(add_button)
        
        # 清空按钮
        clear_button = QToolButton()
        clear_button.setIcon(qta.icon('fa5s.trash-alt', color='#F44336'))
        clear_button.setToolTip("清空列表")
        clear_button.clicked.connect(self.clear)
        title_layout.addWidget(clear_button)
        
        layout.addLayout(title_layout)
        
        # 文件列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setUniformItemSizes(True)  # 优化性能
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
        """)
        self.list_widget.currentItemChanged.connect(self.on_item_changed)
        
        # 设置垂直滚动条策略，提高滚动性能
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(self.list_widget)
        
        # 文件计数标签
        self.count_label = QLabel("0 个文件")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.count_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(self.count_label)
        
        # 接受拖放
        self.setAcceptDrops(True)
        
    def add_files(self, file_paths: List[str]):
        """添加文件"""
        if not file_paths:
            return
            
        # 如果文件数量大于批处理大小，显示进度对话框
        if len(file_paths) > self.batch_size:
            progress_dialog = QProgressDialog("正在添加文件...", "取消", 0, len(file_paths), self)
            progress_dialog.setWindowTitle("添加文件")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(500)  # 只有当操作需要超过500ms时才显示
            
            # 禁用自动关闭，这样用户必须点击"关闭"按钮
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
        else:
            progress_dialog = None
            
        # 暂时禁用UI更新
        self.list_widget.setUpdatesEnabled(False)
        
        # 批量处理文件
        added_count = 0
        new_files = []
        
        for i, file_path in enumerate(file_paths):
            # 检查文件是否已经在列表中
            if file_path in self._files:
                continue
                
            # 获取文件信息
            try:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                
                # 创建列表项
                item = QListWidgetItem()
                item.setText(f"{file_name} ({file_size:.2f} MB)")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setIcon(qta.icon('fa5s.file-audio', color='#1976D2'))
                
                # 添加到列表
                self.list_widget.addItem(item)
                new_files.append(file_path)
                added_count += 1
                
                # 更新进度对话框
                if progress_dialog and i % 10 == 0:  # 每10个文件更新一次进度
                    progress_dialog.setValue(i)
                    QApplication.processEvents()  # 处理UI事件
                    
                    if progress_dialog.wasCanceled():
                        break
            except Exception as e:
                print(f"添加文件失败: {file_path}, 错误: {str(e)}")
                
        # 更新文件列表
        self._files.extend(new_files)
        
        # 恢复UI更新
        self.list_widget.setUpdatesEnabled(True)
        
        # 更新计数标签
        self.count_label.setText(f"{len(self._files)} 个文件")
        
        # 关闭进度对话框
        if progress_dialog:
            progress_dialog.setValue(len(file_paths))
            
        # 发送信号
        if added_count > 0:
            self.files_changed.emit()
            
    def add_files_dialog(self):
        """打开文件对话框添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.aiff *.ape *.ac3);;所有文件 (*.*)"
        )
        
        if files:
            self.add_files(files)
            
    def add_folder(self, folder_path: str, recursive: bool = False):
        """添加文件夹中的音频文件"""
        if not os.path.isdir(folder_path):
            return
            
        # 显示进度对话框
        progress_dialog = QProgressDialog("正在扫描文件夹...", "取消", 0, 100, self)
        progress_dialog.setWindowTitle("添加文件夹")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(500)
        progress_dialog.setValue(0)
        
        # 支持的音频格式扩展名
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.aiff', '.ape', '.ac3']
        
        files = []
        
        # 在单独的函数中扫描文件夹，以便可以更新进度
        def scan_folder():
            file_count = 0
            for root, dirs, filenames in os.walk(folder_path):
                # 如果不是递归且不是根目录，则跳过
                if not recursive and root != folder_path:
                    continue
                    
                for filename in filenames:
                    # 检查文件扩展名
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in audio_extensions:
                        files.append(os.path.join(root, filename))
                        file_count += 1
                        
                        # 每找到10个文件更新一次进度
                        if file_count % 10 == 0:
                            progress_dialog.setValue(min(file_count, 100))
                            QApplication.processEvents()
                            
                            if progress_dialog.wasCanceled():
                                return
        
        # 扫描文件夹
        scan_folder()
        progress_dialog.setValue(100)
        
        # 添加文件
        if files and not progress_dialog.wasCanceled():
            self.add_files(files)
            
    def clear(self):
        """清空文件列表"""
        # 禁用UI更新以提高性能
        self.setUpdatesEnabled(False)
        
        try:
            # 清空内部数据结构
            self._files = []
            
            # 批量移除所有项目，比逐个删除更高效
            self.list_widget.clear()
            
            # 更新计数标签
            self.count_label.setText(f"文件数量: 0")
            
            # 发出文件列表变化的信号
            self.files_changed.emit()
        finally:
            # 确保总是重新启用UI更新
            self.setUpdatesEnabled(True)
            
        # 强制重绘以确保UI更新
        self.list_widget.repaint()
        
    def count(self):
        """获取文件数量"""
        return len(self._files)
        
    def get_all_files(self):
        """获取所有文件路径"""
        return self._files.copy()
        
    def get_selected_file(self):
        """获取选中的文件路径"""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
        
    def on_item_changed(self, current, previous):
        """列表项选择改变"""
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            self.file_selected.emit(file_path)
            
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
            self.add_files(files)
            
        # 添加文件夹
        for folder in folders:
            recursive = QMessageBox.question(
                self,
                "递归添加",
                f"是否包含'{os.path.basename(folder)}'文件夹中的子文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes
            
            self.add_folder(folder, recursive)


class ConversionSettingsWidget(QWidget):
    """转换设置组件"""
    
    # 自定义信号
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题
        title_label = QLabel("转换设置")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll_area)
        
        # 创建滚动区域内的容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 输出格式组
        format_group = QGroupBox("输出格式")
        format_layout = QVBoxLayout(format_group)
        
        # 格式选择下拉框
        self.format_combo = QComboBox()
        self.format_combo.setMinimumWidth(200)  # 设置最小宽度
        self.format_combo.setMaxVisibleItems(10)  # 设置最大可见项数
        self.format_combo.view().setTextElideMode(Qt.TextElideMode.ElideNone)  # 禁用省略号
        self.format_combo.view().setMinimumWidth(300)  # 设置下拉列表的最小宽度
        
        # 添加支持的格式
        formats = get_all_supported_formats()
        for format_id, format_info in formats.items():
            # 使用格式名称和描述作为显示文本
            display_text = f"{format_info['name']} ({format_info['description']})"
            self.format_combo.addItem(display_text, format_id)
        
        # 设置默认格式
        default_format = settings.get("conversion", "default_output_format", "mp3")
        for i in range(self.format_combo.count()):
            if self.format_combo.itemData(i) == default_format:
                self.format_combo.setCurrentIndex(i)
                break
                
        format_layout.addWidget(self.format_combo)
        
        # 添加保留原始音质选项
        self.preserve_quality_checkbox = QCheckBox("保留原始音质")
        self.preserve_quality_checkbox.setChecked(settings.get("conversion", "preserve_quality", True))
        self.preserve_quality_checkbox.stateChanged.connect(self.on_preserve_quality_changed)
        format_layout.addWidget(self.preserve_quality_checkbox)
        
        scroll_layout.addWidget(format_group)
        
        # 输出目录设置
        output_group = QGroupBox("输出目录")
        output_layout = QHBoxLayout(output_group)
        output_layout.setContentsMargins(8, 8, 8, 8)  # 减小内边距
        output_layout.setSpacing(5)  # 减小间距
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 3px;  /* 减小内边距 */
                background-color: #f5f5f5;
            }
        """)
        output_layout.addWidget(self.output_dir_edit)
        
        browse_button = QPushButton("浏览...")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                padding: 3px 8px;  /* 减小按钮内边距 */
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_button)
        
        scroll_layout.addWidget(output_group)
        
        # 音频参数设置
        params_group = QGroupBox("音频参数")
        params_layout = QFormLayout(params_group)
        params_layout.setContentsMargins(8, 8, 8, 8)  # 减小内边距
        params_layout.setSpacing(5)  # 减小行间距
        params_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # 比特率
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["自动", "128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentText(settings.get("conversion", "default_bitrate"))
        self.bitrate_combo.currentTextChanged.connect(self.settings_changed.emit)
        params_layout.addRow("比特率:", self.bitrate_combo)
        
        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["自动", "44100 Hz", "48000 Hz", "96000 Hz", "192000 Hz"])
        self.sample_rate_combo.setCurrentIndex(0)
        self.sample_rate_combo.currentTextChanged.connect(self.settings_changed.emit)
        params_layout.addRow("采样率:", self.sample_rate_combo)
        
        # 声道
        self.channels_combo = QComboBox()
        self.channels_combo.addItems(["自动", "单声道", "立体声"])
        self.channels_combo.setCurrentIndex(0)
        self.channels_combo.currentTextChanged.connect(self.settings_changed.emit)
        params_layout.addRow("声道:", self.channels_combo)
        
        # 音量调整
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(-10, 10)
        self.volume_slider.setValue(0)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(5)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(3)  # 减小间距
        volume_layout.addWidget(QLabel("-10 dB"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(QLabel("+10 dB"))
        
        self.volume_label = QLabel("0 dB")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        params_layout.addRow("音量:", volume_layout)
        params_layout.addRow("", self.volume_label)
        
        # 保留元数据
        self.metadata_check = QCheckBox("保留元数据")
        self.metadata_check.setChecked(settings.get("conversion", "preserve_metadata"))
        self.metadata_check.stateChanged.connect(self.settings_changed.emit)
        params_layout.addRow("", self.metadata_check)
        
        scroll_layout.addWidget(params_group)
        
        # 添加弹性空间
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 初始更新UI
        self.on_format_changed()
        
        # 应用保留原始音质设置
        if self.preserve_quality_checkbox.isChecked():
            self.on_preserve_quality_changed()
        
    def on_format_changed(self):
        """格式改变时更新UI"""
        format_id = self.get_output_format()
        format_info = get_format_info(format_id)
        
        if format_info:
            # 更新比特率选项
            self.bitrate_combo.clear()
            self.bitrate_combo.addItem("自动")
            
            if format_info['lossy'] and format_info['bitrate_options']:
                self.bitrate_combo.setEnabled(True)
                for bitrate in format_info['bitrate_options']:
                    self.bitrate_combo.addItem(bitrate)
                    
                # 设置默认比特率
                if format_info['default_bitrate']:
                    index = self.bitrate_combo.findText(format_info['default_bitrate'])
                    if index >= 0:
                        self.bitrate_combo.setCurrentIndex(index)
            else:
                self.bitrate_combo.setEnabled(False)
                
            # 更新采样率选项
            self.sample_rate_combo.clear()
            self.sample_rate_combo.addItem("自动")
            
            if format_info['sample_rate_options']:
                self.sample_rate_combo.setEnabled(True)
                for rate in format_info['sample_rate_options']:
                    self.sample_rate_combo.addItem(f"{rate} Hz")
            else:
                self.sample_rate_combo.setEnabled(False)
                
            # 如果保留原始音质被选中，应用相应设置
            if self.preserve_quality_checkbox.isChecked():
                self.on_preserve_quality_changed()
                
        self.settings_changed.emit()
        
    def on_preserve_quality_changed(self):
        """保留原始音质选项改变时更新UI"""
        if self.preserve_quality_checkbox.isChecked():
            format_id = self.get_output_format()
            format_info = get_format_info(format_id)
            
            if format_info:
                # 如果是有损格式，选择最高比特率
                if format_info['lossy'] and format_info['bitrate_options']:
                    # 获取最高比特率选项
                    highest_bitrate = format_info['bitrate_options'][-1]
                    index = self.bitrate_combo.findText(highest_bitrate)
                    if index >= 0:
                        self.bitrate_combo.setCurrentIndex(index)
                
                # 选择最高采样率
                if format_info['sample_rate_options']:
                    highest_rate = max(format_info['sample_rate_options'])
                    index = self.sample_rate_combo.findText(f"{highest_rate} Hz")
                    if index >= 0:
                        self.sample_rate_combo.setCurrentIndex(index)
                
                # 设置立体声
                self.channels_combo.setCurrentText("立体声")
        
        self.settings_changed.emit()
        
    def on_volume_changed(self, value):
        """音量滑块值改变"""
        self.volume_label.setText(f"{value} dB")
        self.settings_changed.emit()
        
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            self.settings_changed.emit()
            
    def get_output_format(self):
        """获取输出格式"""
        return self.format_combo.currentData()
        
    def get_output_directory(self):
        """获取输出目录"""
        return self.output_dir_edit.text()
        
    def set_output_directory(self, directory):
        """设置输出目录"""
        self.output_dir_edit.setText(directory)
        
    def get_params(self):
        """获取转换参数"""
        params = {}
        
        # 获取比特率
        if hasattr(self, 'bitrate_combo') and not self.preserve_quality_checkbox.isChecked():
            bitrate_text = self.bitrate_combo.currentText()
            if bitrate_text != "自动":
                # 提取数字部分
                import re
                match = re.search(r'(\d+)', bitrate_text)
                if match:
                    params['bitrate'] = f"{match.group(1)}k"
        
        # 如果有其他参数，可以在这里添加
        # 例如：采样率、声道数等
        
        return params


class WaveformWidget(QWidget):
    """波形显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.current_file = None
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_layout = QHBoxLayout()
        self.title_label = QLabel("波形显示")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # 文件信息
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #666666;")
        title_layout.addWidget(self.info_label)
        
        layout.addLayout(title_layout)
        
        # 创建Figure和Canvas
        self.figure, self.ax = plt.subplots(figsize=(5, 2), dpi=100)
        self.figure.patch.set_facecolor('#f5f5f5')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #f5f5f5;")
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout.addWidget(self.canvas)
        
        # 初始显示
        self.ax.set_title("未选择文件")
        self.ax.set_xlabel("时间 (秒)")
        self.ax.set_ylabel("振幅")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
    def load_file(self, file_path):
        """加载音频文件并显示波形"""
        if not file_path or not os.path.exists(file_path):
            return
            
        self.current_file = file_path
        
        try:
            # 加载音频文件
            audio = AudioSegment.from_file(file_path)
            
            # 获取音频数据
            samples = np.array(audio.get_array_of_samples())
            
            # 如果是立体声，取平均
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
                samples = samples.mean(axis=1)
                
            # 归一化
            samples = samples / np.max(np.abs(samples))
            
            # 计算时间轴
            duration = audio.duration_seconds
            time = np.linspace(0, duration, len(samples))
            
            # 如果样本太多，进行下采样
            if len(samples) > 10000:
                step = len(samples) // 10000
                samples = samples[::step]
                time = time[::step]
                
            # 清除之前的图像
            self.ax.clear()
            
            # 绘制波形
            self.ax.plot(time, samples, color='#1976D2', linewidth=0.5)
            self.ax.set_xlim(0, duration)
            self.ax.set_ylim(-1.1, 1.1)
            self.ax.set_title(os.path.basename(file_path))
            self.ax.set_xlabel("时间 (秒)")
            self.ax.set_ylabel("振幅")
            self.ax.grid(True, alpha=0.3)
            
            # 更新Canvas
            self.canvas.draw()
            
            # 显示文件信息
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            info_text = (
                f"格式: {audio.channels}声道 {audio.frame_rate}Hz | "
                f"时长: {int(duration // 60)}:{int(duration % 60):02d} | "
                f"大小: {file_size:.2f} MB"
            )
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.ax.clear()
            self.ax.set_title(f"无法加载文件: {str(e)}")
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
            self.info_label.setText("") 
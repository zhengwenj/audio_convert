# Audio Convert - 通用音频格式转换工具

<div align="center">
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/zhengwenj/audio_convert)

## 📝 项目概述

Audio Convert 是一款功能强大、界面友好的音频格式转换工具，支持多种主流音频格式之间的相互转换。无论是单个文件转换还是批量处理，Audio Convert 都能提供高效、高质量的转换体验。

## ✨ 主要特性

- **多格式支持**：支持 MP3, WAV, FLAC, AAC, OGG, M4A, WMA, AIFF, APE, AC3 等主流音频格式
- **批量转换**：支持多文件同时转换和整个文件夹的批量处理
- **参数调整**：可调节比特率、采样率、声道设置等参数
- **质量保证**：支持无损转换和高质量的有损转换
- **简洁界面**：直观易用的图形用户界面，支持拖放操作
- **自动更新**：内置更新检查和下载功能
- **跨平台支持**：兼容 Windows、macOS 和 Linux 系统

## 🔧 安装指南

### 方法一：下载可执行文件（推荐）

1. 访问 [Releases](https://github.com/zhengwenj/audio_convert/releases) 页面
2. 下载适合您操作系统的最新版本
3. 运行安装程序或解压缩文件
4. 启动 Audio Convert

### 方法二：从源码安装

确保您已安装 Python 3.9 或更高版本：

```bash
# 克隆仓库
git clone https://github.com/zhengwenj/audio_convert.git
cd audio_convert

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 依赖项

- Python 3.9+
- FFmpeg
- PyQt6
- pydub
- 其他依赖见 requirements.txt

## 📖 使用说明

### 基本使用流程

1. **添加文件**：点击"添加文件"按钮或直接拖放音频文件到程序窗口
2. **选择输出格式**：从下拉菜单中选择目标音频格式
3. **调整设置**：根据需要调整输出质量、比特率等参数
4. **选择输出位置**：指定转换后文件的保存位置
5. **开始转换**：点击"开始转换"按钮

### 高级功能

- **批量转换**：选择多个文件或整个文件夹进行批量转换
- **保留原始质量**：勾选"保留原始质量"选项，自动优化转换参数
- **自定义参数**：调整比特率、采样率等参数，满足特定需求

## 🛠️ 开发相关

### 项目结构

```
audio_convert/
├── core/           # 核心转换功能
├── gui/            # 图形界面组件
├── config/         # 配置文件
├── utils/          # 辅助工具
└── ...
```

### 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 👥 联系方式

- 项目维护者: [zhengwenj](mailto:jun.zw@aliyun.com)
- 项目主页: [GitHub](https://github.com/zhengwenj/audio_convert)

## 🙏 致谢

- [FFmpeg](https://ffmpeg.org/) - 强大的音频处理库
- [PyQt](https://www.riverbankcomputing.com/software/pyqt/) - Python GUI 框架
- [pydub](https://github.com/jiaaro/pydub) - 简单易用的音频处理库 
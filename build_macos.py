#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS系统打包脚本 - 使用PyInstaller
"""
import PyInstaller.__main__
import os
import shutil
import sys
import platform

# 检查是否在macOS上运行
if platform.system() != "Darwin":
    print("错误: 此脚本仅适用于macOS系统。")
    sys.exit(1)

print("开始打包 Audio Convert 应用程序...")

# 检查PyInstaller是否已安装
try:
    import PyInstaller
except ImportError:
    print("错误: 未安装PyInstaller。请运行 'pip install pyinstaller' 安装。")
    sys.exit(1)

# 清理旧的构建文件
print("清理旧的构建文件...")
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("AudioConvert.spec"):
    os.remove("AudioConvert.spec")

# 定义图标文件路径
# 如果您有图标文件，请取消注释下面的行并指定路径
# icon_path = "path/to/icon.icns"  # macOS 需要 .icns 格式的图标

# 收集需要包含的数据文件
data_files = [
    ("config", "config"),
    ("gui/resources", "gui/resources"),
]

# 构建数据文件参数 (macOS使用冒号而不是分号)
data_args = []
for src, dst in data_files:
    if os.path.exists(src):
        data_args.append(f"--add-data={src}:{dst}")
    else:
        print(f"警告: 数据目录 '{src}' 不存在，将被跳过")

# 构建隐藏导入参数
hidden_imports = [
    "PyQt6.QtSvg",
    "PyQt6.QtXml",
    "pydub.generators",
    "mutagen",
    "numpy",
    "matplotlib",
]

hidden_import_args = [f"--hidden-import={imp}" for imp in hidden_imports]

# PyInstaller 参数
args = [
    "main.py",
    "--name=AudioConvert",
    "--onefile",
    "--windowed",
    "--clean",
    # f"--icon={icon_path}",  # 如果有图标，取消注释
    "--osx-bundle-identifier=com.audioconvert.app",  # macOS特有参数
]

# 添加数据文件和隐藏导入参数
args.extend(data_args)
args.extend(hidden_import_args)

print(f"PyInstaller 参数: {args}")
print("开始构建...")

# 运行 PyInstaller
PyInstaller.__main__.run(args)

# 检查构建结果
if os.path.exists("dist/AudioConvert.app"):
    print("="*60)
    print("打包成功！应用程序位于 dist/AudioConvert.app")
    print("="*60)
    
    # 提示创建DMG
    print("如果您想创建DMG安装包，请运行以下命令:")
    print("brew install create-dmg")
    print("create-dmg --volname \"Audio Convert Installer\" --window-pos 200 120 --window-size 600 400 --icon-size 100 --icon \"AudioConvert.app\" 200 190 --hide-extension \"AudioConvert.app\" --app-drop-link 400 190 \"AudioConvert.dmg\" \"dist/AudioConvert.app\"")
else:
    print("="*60)
    print("打包似乎失败了。请检查上面的错误信息。")
    print("="*60) 
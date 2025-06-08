#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows系统打包脚本 - 使用PyInstaller
"""
import PyInstaller.__main__
import os
import shutil
import sys

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
# icon_path = "path/to/icon.ico"

# 收集需要包含的数据文件
data_files = [
    ("config", "config"),
    ("gui/resources", "gui/resources"),
]

# 构建数据文件参数
data_args = []
for src, dst in data_files:
    if os.path.exists(src):
        data_args.append(f"--add-data={src};{dst}")
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
]

# 添加数据文件和隐藏导入参数
args.extend(data_args)
args.extend(hidden_import_args)

print(f"PyInstaller 参数: {args}")
print("开始构建...")

# 运行 PyInstaller
PyInstaller.__main__.run(args)

# 检查构建结果
if os.path.exists("dist/AudioConvert.exe"):
    print("="*60)
    print("打包成功！可执行文件位于 dist/AudioConvert.exe")
    print("="*60)
else:
    print("="*60)
    print("打包似乎失败了。请检查上面的错误信息。")
    print("="*60) 
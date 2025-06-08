# Audio Convert 打包指南

本文档提供了将 Audio Convert 应用程序打包为单个可执行文件的详细指南，适用于 Windows 和 macOS 系统。

## 目录

- [准备工作](#准备工作)
- [Windows 打包指南](#windows-打包指南)
  - [使用 PyInstaller](#使用-pyinstaller-windows)
  - [使用 Nuitka](#使用-nuitka-windows)
- [macOS 打包指南](#macos-打包指南)
  - [使用 PyInstaller](#使用-pyinstaller-macos)
  - [创建 DMG 安装包](#创建-dmg-安装包)
- [打包后的测试](#打包后的测试)
- [常见问题解决](#常见问题解决)

## 准备工作

在开始打包之前，请确保：

1. 您的开发环境已安装所有依赖项：
   ```bash
   pip install -r requirements.txt
   ```

2. 应用程序在开发环境中运行正常

3. 安装打包工具：
   ```bash
   pip install pyinstaller
   # 如果使用 Nuitka (可选)
   pip install nuitka
   ```

## Windows 打包指南

### 使用 PyInstaller (Windows)

PyInstaller 是一个流行的 Python 应用程序打包工具，可以将 Python 程序打包为单个可执行文件。

1. **创建打包脚本**

   创建一个名为 `build_windows.py` 的文件，内容如下：

   ```python
   import PyInstaller.__main__
   import os
   import shutil

   # 清理旧的构建文件
   if os.path.exists("build"):
       shutil.rmtree("build")
   if os.path.exists("dist"):
       shutil.rmtree("dist")

   # 定义图标文件路径
   # 如果有图标文件，请取消注释下面的行并指定路径
   # icon_path = "path/to/icon.ico"

   # PyInstaller 参数
   args = [
       "main.py",
       "--name=AudioConvert",
       "--onefile",
       "--windowed",
       "--clean",
       # f"--icon={icon_path}",  # 如果有图标，取消注释
       "--add-data=config;config",
       "--hidden-import=PyQt6.QtSvg",
       "--hidden-import=PyQt6.QtXml",
       "--hidden-import=pydub.generators",
   ]

   # 运行 PyInstaller
   PyInstaller.__main__.run(args)

   print("打包完成！可执行文件位于 dist 目录中。")
   ```

2. **运行打包脚本**

   ```bash
   python build_windows.py
   ```

3. **打包完成后**

   打包好的可执行文件将位于 `dist` 目录中，名为 `AudioConvert.exe`。

### 使用 Nuitka (Windows)

Nuitka 是一个将 Python 代码编译为 C 代码的工具，通常可以生成更小、更快的可执行文件。

1. **安装 Nuitka 和依赖项**

   ```bash
   pip install nuitka
   pip install zstandard  # 用于压缩
   ```

2. **创建打包脚本**

   创建一个名为 `build_nuitka_windows.py` 的文件，内容如下：

   ```python
   import os
   import subprocess
   import sys

   # 定义 Nuitka 命令
   cmd = [
       sys.executable, 
       "-m", "nuitka", 
       "--standalone",
       "--onefile",
       "--windows-disable-console",
       "--include-package=PyQt6",
       "--include-package=pydub",
       "--include-data-dir=config=config",
       # "--windows-icon-from-ico=path/to/icon.ico",  # 如果有图标，取消注释
       "main.py"
   ]

   # 运行 Nuitka
   subprocess.run(cmd)

   print("打包完成！")
   ```

3. **运行打包脚本**

   ```bash
   python build_nuitka_windows.py
   ```

4. **打包完成后**

   打包好的可执行文件将位于项目根目录中，名为 `main.exe` 或 `main.bin`。

## macOS 打包指南

### 使用 PyInstaller (macOS)

1. **创建打包脚本**

   创建一个名为 `build_macos.py` 的文件，内容如下：

   ```python
   import PyInstaller.__main__
   import os
   import shutil

   # 清理旧的构建文件
   if os.path.exists("build"):
       shutil.rmtree("build")
   if os.path.exists("dist"):
       shutil.rmtree("dist")

   # 定义图标文件路径
   # 如果有图标文件，请取消注释下面的行并指定路径
   # icon_path = "path/to/icon.icns"  # macOS 需要 .icns 格式的图标

   # PyInstaller 参数
   args = [
       "main.py",
       "--name=AudioConvert",
       "--onefile",
       "--windowed",
       "--clean",
       # f"--icon={icon_path}",  # 如果有图标，取消注释
       "--add-data=config:config",  # 注意 macOS 使用冒号而不是分号
       "--hidden-import=PyQt6.QtSvg",
       "--hidden-import=PyQt6.QtXml",
       "--hidden-import=pydub.generators",
   ]

   # 运行 PyInstaller
   PyInstaller.__main__.run(args)

   print("打包完成！应用程序位于 dist 目录中。")
   ```

2. **运行打包脚本**

   ```bash
   python build_macos.py
   ```

3. **打包完成后**

   打包好的应用程序将位于 `dist` 目录中，名为 `AudioConvert`。

### 创建 DMG 安装包

要创建一个更专业的 macOS 安装包，您可以将应用程序打包为 DMG 文件：

1. **安装 create-dmg 工具**

   ```bash
   brew install create-dmg
   ```

2. **创建 DMG 文件**

   ```bash
   create-dmg \
     --volname "Audio Convert Installer" \
     --volicon "path/to/icon.icns" \
     --window-pos 200 120 \
     --window-size 600 400 \
     --icon-size 100 \
     --icon "AudioConvert.app" 200 190 \
     --hide-extension "AudioConvert.app" \
     --app-drop-link 400 190 \
     "AudioConvert.dmg" \
     "dist/AudioConvert.app"
   ```

## 打包后的测试

无论使用哪种打包方法，都应该在打包后进行全面测试：

1. **基本功能测试**
   - 启动应用程序
   - 添加文件并转换
   - 测试所有主要功能

2. **在干净环境中测试**
   - 在没有安装 Python 或依赖项的计算机上测试
   - 确保所有资源文件都被正确包含

3. **检查常见问题**
   - 文件路径引用是否正确
   - 外部资源是否可访问
   - 配置文件是否可读写

## 常见问题解决

### PyInstaller 问题

1. **缺少模块错误**

   如果出现 `ModuleNotFoundError`，将缺少的模块添加到 `--hidden-import` 参数中：
   ```
   --hidden-import=missing_module
   ```

2. **资源文件找不到**

   确保使用正确的 `--add-data` 参数，并在代码中使用适当的路径解析：
   ```python
   import sys
   import os
   
   # 获取正确的资源路径
   def resource_path(relative_path):
       if getattr(sys, 'frozen', False):
           # 如果是打包后的应用
           base_path = sys._MEIPASS
       else:
           # 如果是开发环境
           base_path = os.path.abspath(".")
       return os.path.join(base_path, relative_path)
   ```

### Nuitka 问题

1. **依赖项缺失**

   使用 `--include-package` 确保所有必要的包都被包含：
   ```
   --include-package=package_name
   ```

2. **编译错误**

   确保您的系统上安装了适当的编译器：
   - Windows: Visual Studio Build Tools
   - macOS: Xcode Command Line Tools

### macOS 特定问题

1. **签名问题**

   在 macOS 上，您可能需要对应用程序进行签名：
   ```bash
   codesign --deep --force --sign - dist/AudioConvert.app
   ```

2. **Gatekeeper 警告**

   用户可能会看到"无法验证开发者"的警告。解决方法：
   - 获取 Apple 开发者证书并签名
   - 指导用户通过右键点击应用程序并选择"打开"来绕过警告

---

如有其他打包问题，请查阅 [PyInstaller 文档](https://pyinstaller.readthedocs.io/) 或 [Nuitka 文档](https://nuitka.net/doc/user-manual.html)，或在项目 GitHub 页面提出问题。 
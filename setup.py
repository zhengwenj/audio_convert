#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频格式转换工具安装脚本
"""
from setuptools import setup, find_packages

from config.settings import APP_NAME, APP_VERSION, AUTHOR

setup(
    name=APP_NAME.lower().replace(' ', '_'),
    version=APP_VERSION,
    description='通用音频格式转换工具',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email='jun.zw@aliyun.com',
    url='https://github.com/zhengwenj/audio_convert',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyQt6>=6.4.0',
        'pydub>=0.25.1',
        'ffmpeg-python>=0.2.0',
        'mutagen>=1.45.1',
        'numpy>=1.22.0',
        'matplotlib>=3.5.1',
        'pillow>=9.0.0',
        'qtawesome>=1.1.1',
    ],
    entry_points={
        'console_scripts': [
            'audio_convert=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Utilities',
    ],
    python_requires='>=3.9',
) 
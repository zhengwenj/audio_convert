"""
错误处理类
"""

class AudioConvertError(Exception):
    """音频转换工具基础异常类"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConversionError(AudioConvertError):
    """音频转换过程中的错误"""
    pass


class UnsupportedFormatError(AudioConvertError):
    """不支持的音频格式错误"""
    pass


class FileAccessError(AudioConvertError):
    """文件访问错误"""
    pass


class ConfigError(AudioConvertError):
    """配置错误"""
    pass


class ValidationError(AudioConvertError):
    """输入验证错误"""
    pass


class FFmpegError(AudioConvertError):
    """FFmpeg相关错误"""
    pass


class BatchProcessError(AudioConvertError):
    """批量处理错误"""
    def __init__(self, message: str, failed_files=None):
        self.failed_files = failed_files or []
        super().__init__(message) 
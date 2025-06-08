"""
音频转换器核心类
"""
import os
import time
from typing import Dict, List, Optional, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from core.formats import SUPPORTED_FORMATS, get_format_info, is_format_supported
from core.errors import ConversionError, UnsupportedFormatError, FileAccessError


class AudioConverter:
    """音频转换器核心类"""
    
    def __init__(self):
        """初始化转换器"""
        self.current_tasks = {}
        self.completed_tasks = []
        self.failed_tasks = []
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count())
        
    def convert_file(self, 
                    input_path: str, 
                    output_path: str, 
                    output_format: str, 
                    bitrate: Optional[str] = None,
                    sample_rate: Optional[int] = None,
                    channels: Optional[int] = None,
                    volume_adjustment: Optional[float] = None,
                    progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        转换单个音频文件
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 输出格式
            bitrate: 比特率，如"192k"
            sample_rate: 采样率，如44100
            channels: 声道数，1为单声道，2为立体声
            volume_adjustment: 音量调整，单位为dB，正值增加音量，负值降低音量
            progress_callback: 进度回调函数，接收一个0-1之间的浮点数表示进度
            
        返回:
            bool: 转换是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(input_path):
                raise FileAccessError(f"输入文件不存在: {input_path}")
                
            # 检查输出格式是否支持
            if not is_format_supported(output_format):
                raise UnsupportedFormatError(f"不支持的输出格式: {output_format}")
                
            # 确保输出目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 加载音频文件
            if progress_callback:
                progress_callback(0.1)
                
            try:
                audio = AudioSegment.from_file(input_path)
            except Exception as e:
                raise ConversionError(f"无法加载音频文件: {str(e)}")
                
            if progress_callback:
                progress_callback(0.3)
                
            # 应用音频参数调整
            if sample_rate:
                audio = audio.set_frame_rate(sample_rate)
                
            if channels:
                audio = audio.set_channels(channels)
                
            if volume_adjustment:
                audio = audio.apply_gain(volume_adjustment)
                
            if progress_callback:
                progress_callback(0.6)
                
            # 导出为目标格式
            export_args = {}
            if bitrate:
                export_args["bitrate"] = bitrate
                
            try:
                audio.export(
                    output_path,
                    format=output_format,
                    **export_args
                )
            except Exception as e:
                raise ConversionError(f"导出音频文件失败: {str(e)}")
                
            if progress_callback:
                progress_callback(1.0)
                
            return True
            
        except (FileAccessError, UnsupportedFormatError, ConversionError) as e:
            # 这些是已知的错误类型，可以直接处理
            if progress_callback:
                progress_callback(0)
            raise e
        except Exception as e:
            # 未知错误类型，包装为ConversionError
            if progress_callback:
                progress_callback(0)
            raise ConversionError(f"转换过程中发生未知错误: {str(e)}")
    
    def batch_convert(self, 
                     files: List[str],
                     output_dir: str,
                     output_format: str,
                     params: Dict = None,
                     progress_callback: Optional[Callable[[int, float], None]] = None) -> Tuple[int, int]:
        """
        批量转换音频文件
        
        参数:
            files: 文件路径列表
            output_dir: 输出目录
            output_format: 输出格式
            params: 转换参数，包括bitrate, sample_rate, channels, volume_adjustment等
            progress_callback: 进度回调函数，接收文件索引和进度
            
        返回:
            Tuple[int, int]: 成功和失败的文件数量
        """
        if params is None:
            params = {}
            
        success_count = 0
        failed_count = 0
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        for i, input_path in enumerate(files):
            # 生成输出文件名
            file_name = os.path.basename(input_path)
            output_name = f"{os.path.splitext(file_name)[0]}.{output_format}"
            output_path = os.path.join(output_dir, output_name)
            
            # 为单个文件创建进度回调
            def file_progress_callback(progress):
                if progress_callback:
                    progress_callback(i, progress)
            
            try:
                self.convert_file(
                    input_path=input_path,
                    output_path=output_path,
                    output_format=output_format,
                    bitrate=params.get('bitrate'),
                    sample_rate=params.get('sample_rate'),
                    channels=params.get('channels'),
                    volume_adjustment=params.get('volume_adjustment'),
                    progress_callback=file_progress_callback
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                # 记录错误但继续处理其他文件
                print(f"转换文件 {input_path} 失败: {str(e)}")
                
            # 短暂暂停，让其他线程有机会处理
            time.sleep(0.01)
        
        return success_count, failed_count
    
    def convert_folder(self,
                      input_folder: str,
                      output_folder: str,
                      output_format: str,
                      recursive: bool = False,
                      params: Dict = None,
                      progress_callback: Optional[Callable[[int, float], None]] = None) -> Tuple[int, int]:
        """
        转换文件夹中的所有音频文件
        
        参数:
            input_folder: 输入文件夹
            output_folder: 输出文件夹
            output_format: 输出格式
            recursive: 是否递归处理子文件夹
            params: 转换参数
            progress_callback: 进度回调函数
            
        返回:
            Tuple[int, int]: 成功和失败的文件数量
        """
        if not os.path.isdir(input_folder):
            raise FileAccessError(f"输入路径不是文件夹: {input_folder}")
            
        os.makedirs(output_folder, exist_ok=True)
        
        file_paths = []
        
        # 收集所有音频文件
        for root, dirs, files in os.walk(input_folder):
            if not recursive and root != input_folder:
                continue
                
            for file in files:
                file_ext = os.path.splitext(file)[1].lower().lstrip('.')
                if is_format_supported(file_ext):
                    input_path = os.path.join(root, file)
                    file_paths.append(input_path)
        
        # 执行批量转换
        success_count, failed_count = self.batch_convert(
            files=file_paths,
            output_dir=output_folder,
            output_format=output_format,
            params=params,
            progress_callback=progress_callback
        )
        
        return success_count, failed_count 
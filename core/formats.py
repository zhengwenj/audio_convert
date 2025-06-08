"""
音频格式定义和检测
"""
from typing import Dict, List, Optional, Tuple

# 支持的音频格式
SUPPORTED_FORMATS = {
    'mp3': {
        'name': 'MP3',
        'description': 'MPEG-1 Audio Layer III',
        'extension': '.mp3',
        'mime_type': 'audio/mpeg',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k', '320k'],
        'sample_rate_options': [44100, 48000],
    },
    'wav': {
        'name': 'WAV',
        'description': 'Waveform Audio File Format',
        'extension': '.wav',
        'mime_type': 'audio/wav',
        'lossy': False,
        'default_bitrate': None,
        'bitrate_options': [],
        'sample_rate_options': [44100, 48000, 96000, 192000],
    },
    'flac': {
        'name': 'FLAC',
        'description': 'Free Lossless Audio Codec',
        'extension': '.flac',
        'mime_type': 'audio/flac',
        'lossy': False,
        'default_bitrate': None,
        'bitrate_options': [],
        'sample_rate_options': [44100, 48000, 96000, 192000],
    },
    'aac': {
        'name': 'AAC',
        'description': 'Advanced Audio Coding',
        'extension': '.aac',
        'mime_type': 'audio/aac',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k'],
        'sample_rate_options': [44100, 48000],
    },
    'ogg': {
        'name': 'OGG',
        'description': 'Ogg Vorbis',
        'extension': '.ogg',
        'mime_type': 'audio/ogg',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k', '320k'],
        'sample_rate_options': [44100, 48000],
    },
    'm4a': {
        'name': 'M4A',
        'description': 'MPEG-4 Audio',
        'extension': '.m4a',
        'mime_type': 'audio/m4a',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k'],
        'sample_rate_options': [44100, 48000],
    },
    'wma': {
        'name': 'WMA',
        'description': 'Windows Media Audio',
        'extension': '.wma',
        'mime_type': 'audio/x-ms-wma',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k'],
        'sample_rate_options': [44100, 48000],
    },
    'aiff': {
        'name': 'AIFF',
        'description': 'Audio Interchange File Format',
        'extension': '.aiff',
        'mime_type': 'audio/aiff',
        'lossy': False,
        'default_bitrate': None,
        'bitrate_options': [],
        'sample_rate_options': [44100, 48000, 96000],
    },
    'ape': {
        'name': 'APE',
        'description': 'Monkey\'s Audio',
        'extension': '.ape',
        'mime_type': 'audio/ape',
        'lossy': False,
        'default_bitrate': None,
        'bitrate_options': [],
        'sample_rate_options': [44100, 48000, 96000],
    },
    'ac3': {
        'name': 'AC3',
        'description': 'Audio Codec 3',
        'extension': '.ac3',
        'mime_type': 'audio/ac3',
        'lossy': True,
        'default_bitrate': '192k',
        'bitrate_options': ['128k', '192k', '256k', '384k', '448k'],
        'sample_rate_options': [44100, 48000],
    }
}

# 常见采样率选项
SAMPLE_RATE_OPTIONS = [44100, 48000, 96000, 192000]

# 常见声道选项
CHANNEL_OPTIONS = [1, 2]

def get_format_info(format_id: str) -> Optional[Dict]:
    """
    获取指定格式的详细信息
    
    参数:
        format_id: 格式ID，如'mp3', 'wav'等
        
    返回:
        Dict: 格式信息字典，如果格式不存在则返回None
    """
    return SUPPORTED_FORMATS.get(format_id.lower())

def is_format_supported(format_id: str) -> bool:
    """
    检查指定格式是否被支持
    
    参数:
        format_id: 格式ID，如'mp3', 'wav'等
        
    返回:
        bool: 是否支持该格式
    """
    return format_id.lower() in SUPPORTED_FORMATS

def get_extension_for_format(format_id: str) -> str:
    """
    获取指定格式的文件扩展名
    
    参数:
        format_id: 格式ID，如'mp3', 'wav'等
        
    返回:
        str: 文件扩展名，如'.mp3', '.wav'等
    """
    format_info = get_format_info(format_id)
    if format_info:
        return format_info['extension']
    return f".{format_id.lower()}"

def detect_format_from_extension(filename: str) -> Optional[str]:
    """
    从文件名中检测音频格式
    
    参数:
        filename: 文件名
        
    返回:
        str: 格式ID，如'mp3', 'wav'等，如果无法检测则返回None
    """
    extension = filename.lower().split('.')[-1]
    for format_id, info in SUPPORTED_FORMATS.items():
        if info['extension'].lower().lstrip('.') == extension:
            return format_id
    return None

def get_all_supported_formats() -> Dict[str, Dict]:
    """
    获取所有支持的格式列表
    
    返回:
        Dict[str, Dict]: 格式ID到格式信息的映射字典
    """
    return SUPPORTED_FORMATS

def get_optimal_settings(input_format: str, output_format: str) -> Dict:
    """
    获取从一种格式转换到另一种格式的最佳设置
    
    参数:
        input_format: 输入格式ID
        output_format: 输出格式ID
        
    返回:
        Dict: 最佳设置参数
    """
    input_info = get_format_info(input_format)
    output_info = get_format_info(output_format)
    
    settings = {}
    
    # 如果输出格式是有损的，设置比特率
    if output_info and output_info['lossy'] and output_info['default_bitrate']:
        settings['bitrate'] = output_info['default_bitrate']
    
    # 采样率保持不变或使用输出格式的推荐值
    if output_info and output_info['sample_rate_options']:
        settings['sample_rate'] = output_info['sample_rate_options'][0]
    
    # 默认使用立体声
    settings['channels'] = 2
    
    return settings 
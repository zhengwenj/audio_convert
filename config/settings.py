"""
默认设置
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# 应用程序基本信息
APP_NAME = "Audio Convert"
APP_VERSION = "1.0.0"
AUTHOR = "Your Name"
WEBSITE = "https://example.com"

# 默认设置
DEFAULT_SETTINGS = {
    # 常规设置
    "general": {
        "language": "zh_CN",
        "theme": "light",
        "check_updates": True,
        "check_updates_on_startup": True,  # 默认在启动时检查更新
        "ignored_version": "",
        "last_update_check": "",
        "save_history": True,
        "max_history_items": 100,
        "default_output_dir": "auto",  # "auto" 表示与输入文件相同的目录
        "confirm_overwrite": True,
        "show_notifications": True,
    },
    
    # 转换设置
    "conversion": {
        "default_output_format": "mp3",
        "preserve_metadata": True,
        "default_bitrate": "320k",
        "default_sample_rate": 44100,
        "default_channels": 2,
        "thread_count": os.cpu_count(),
        "auto_normalize": False,
        "preserve_quality": True,
    },
    
    # 界面设置
    "ui": {
        "show_file_info": True,
        "show_waveform": False,  # 波形显示默认关闭
        "enable_waveform": False,  # 完全禁用波形显示功能
        "show_spectrum": False,
        "file_list_columns": ["name", "format", "duration", "size"],
        "toolbar_actions": ["open", "convert", "settings", "help"],
        "window_size": [800, 500],  # 减小默认窗口大小
        "window_position": [100, 100],
        "window_maximized": False,
        "recent_directories": [],
        "file_list_ratio": 6,  # 文件列表占比设置为6
        "settings_ratio": 4,   # 设置面板占比设置为4
    },
    
    # 高级设置
    "advanced": {
        "ffmpeg_path": "auto",  # "auto" 表示自动查找
        "temp_dir": "auto",  # "auto" 表示使用系统临时目录
        "log_level": "info",
        "enable_experimental": False,
        "custom_ffmpeg_args": "",
    }
}

# 用户配置文件路径
USER_CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    ".audio_convert"
)

USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "settings.json")

# 预设目录
PRESETS_DIR = os.path.join(USER_CONFIG_DIR, "presets")

# 确保配置目录存在
os.makedirs(USER_CONFIG_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

class Settings:
    """设置管理类"""
    
    def __init__(self):
        """初始化设置"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        
    def load_settings(self) -> None:
        """从配置文件加载设置"""
        if os.path.exists(USER_CONFIG_FILE):
            try:
                with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    
                # 递归更新设置
                self._update_dict(self.settings, user_settings)
            except Exception as e:
                print(f"加载设置文件失败: {str(e)}")
                
    def save_settings(self) -> None:
        """保存设置到配置文件"""
        try:
            with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置文件失败: {str(e)}")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取设置值"""
        try:
            return self.settings[section][key]
        except KeyError:
            return default
            
    def set(self, section: str, key: str, value: Any) -> None:
        """设置值"""
        if section not in self.settings:
            self.settings[section] = {}
            
        self.settings[section][key] = value
        
    def _update_dict(self, target: Dict, source: Dict) -> None:
        """递归更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
                
    def reset_to_defaults(self) -> None:
        """重置为默认设置"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()
        
    def get_all(self) -> Dict:
        """获取所有设置"""
        return self.settings.copy()
        
    def get_section(self, section: str) -> Dict:
        """获取指定部分的设置"""
        return self.settings.get(section, {}).copy()
        
    def save_preset(self, name: str, settings: Dict) -> None:
        """保存预设"""
        preset_path = os.path.join(PRESETS_DIR, f"{name}.json")
        try:
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存预设失败: {str(e)}")
            
    def load_preset(self, name: str) -> Optional[Dict]:
        """加载预设"""
        preset_path = os.path.join(PRESETS_DIR, f"{name}.json")
        if os.path.exists(preset_path):
            try:
                with open(preset_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载预设失败: {str(e)}")
        return None
        
    def get_presets_list(self) -> list:
        """获取所有预设名称"""
        presets = []
        for file in os.listdir(PRESETS_DIR):
            if file.endswith('.json'):
                presets.append(os.path.splitext(file)[0])
        return presets
        
    def delete_preset(self, name: str) -> bool:
        """删除预设"""
        preset_path = os.path.join(PRESETS_DIR, f"{name}.json")
        if os.path.exists(preset_path):
            try:
                os.remove(preset_path)
                return True
            except Exception as e:
                print(f"删除预设失败: {str(e)}")
        return False


# 全局设置实例
settings = Settings() 
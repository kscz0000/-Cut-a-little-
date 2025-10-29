"""
配置管理模块
负责加载、保存和管理用户设置
"""
import json
import os
from typing import Dict, Any


class SettingsManager:
    """用户设置管理器"""
    
    def __init__(self, settings_file: str = "settings.json"):
        """
        初始化设置管理器
        
        Args:
            settings_file: 设置文件路径
        """
        self.settings_file = settings_file
        self.default_settings = {
            "last_directory": os.path.expanduser("~/Pictures"),
            "output_format": "PNG",
            "default_grid_type": "auto",
            "custom_rows": 3,
            "custom_cols": 3,
            "enable_manual_lines": False,
            "window_size": "1000x750",
            "output_mode": "same_dir",
            "custom_output_path": "",
            "last_rotation_angles": {},
            "language": "zh",  # 默认语言为中文
            "edge_detection_enabled": True,  # 默认启用智能边缘线识别
            "edge_detector_type": "basic",  # 默认边缘检测器类型
            "edge_detector_mode": "auto"  # 默认边缘检测模式
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        从文件加载设置
        
        Returns:
            设置字典
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # 合并默认设置和加载的设置
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
            else:
                # 如果设置文件不存在，创建默认设置文件
                self.save_settings()
                return self.default_settings.copy()
        except json.JSONDecodeError as e:
            print(f"设置文件格式错误: {e}")
            # 使用默认设置并重新保存
            self.save_settings()
            return self.default_settings.copy()
        except Exception as e:
            print(f"加载设置失败: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """
        保存设置到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取设置值
        
        Args:
            key: 设置键名
            default: 默认值
            
        Returns:
            设置值
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置值并自动保存
        
        Args:
            key: 设置键名
            value: 设置值
        """
        self.settings[key] = value
        self.save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有设置"""
        return self.settings.copy()

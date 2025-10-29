"""
语言管理模块
负责处理应用的多语言支持
"""
from typing import Dict, Any


class LanguageManager:
    """语言管理器"""
    
    def __init__(self):
        """初始化语言管理器"""
        self.current_language = "zh"  # 默认语言为中文
        self.translations = {
            "zh": {
                # 主窗口标题
                "app_title": "剪一剪 - 表情包分割器",
                
                # 导航栏
                "nav_title": "✂️ 剪一剪",
                "nav_subtitle": "表情包分割器 V2.0",
                "nav_ready": "● 就绪",
                
                # 左侧文件管理面板
                "file_management": "文件管理",
                "preview_settings": "预览与设置",
                "action_control": "操作控制",
                
                # 文件管理区域
                "selected_files": "已选{}个",
                "max_files": "最多10个",
                "add_files": "添加文件",
                "delete_selected": "删除选中",
                "clear_list": "清空列表",
                
                # 原图预览区域
                "original_preview": "原图预览",
                "reset": "重置",
                "rotate_left": "左转",
                "rotate_right": "右转",
                "flip_horizontal": "水平翻转",
                "angle": "角度",
                "dimensions": "尺寸",
                
                # 分割预览区域
                "split_preview": "分割预览",
                "split_info": "分割: {}×{} | 总数: {}张",
                
                # 参数设置区域
                "param_settings": "参数设置",
                "split_mode": "分割模式",
                "auto_detect": "自动",
                "manual": "手动",
                "rows": "行数",
                "cols": "列数",
                "output_format": "输出格式",
                "png_transparent": "PNG (透明)",
                "jpg_small": "JPG (小文件)",
                
                # 操作控制区域
                "process_progress": "处理进度",
                "ready": "准备就绪...",
                "start_process": "开始处理",
                "open_output": "打开输出",
                "process_log": "处理日志",
                "clear_log": "清空日志",
                
                # 设置对话框
                "settings_title": "应用设置",
                "settings_subtitle": "个性化您的使用体验",
                "output_path": "输出路径",
                "default_output_dir": "默认输出目录",
                "browse": "浏览",
                "about_app": "关于剪一剪",
                "app_info_support": "应用信息与支持",
                "version": "版本",
                "view_details": "查看详情",
                "restore_defaults": "恢复默认",
                "close": "关闭",
                
                # 关于对话框
                "about_title": "关于剪一剪",
                "app_description": "一款现代化的图像裁剪与表情包分割工具",
                "features": "核心特性",
                "milestones": "项目进展",
                "badges": "项目成就",
                "support_ways": "支持方式",
                "thanks": "感谢您的支持与信任！",
                
                # 支持方式
                "star_github": "Star on GitHub",
                "github_desc": "在 GitHub 上为项目加星标",
                "qq_email": "QQ邮箱",
                "gmail": "谷歌邮箱",
                
                # 社交链接
                "github": "GitHub",
                "email": "Email",
                
                # 通用
                "confirm": "确认",
                "cancel": "取消",
                "ok": "确定",
                "language": "语言设置",
                "选择界面显示语言": "选择界面显示语言",
                "语言设置已保存，部分更改将在下次启动时生效。": "语言设置已保存，部分更改将在下次启动时生效。",
            },
            "en": {
                # Main window title
                "app_title": "Cut It - Sticker Splitter",
                
                # Navigation bar
                "nav_title": "✂️ Cut It",
                "nav_subtitle": "Sticker Splitter V2.0",
                "nav_ready": "● Ready",
                
                # Left file management panel
                "file_management": "File Management",
                "preview_settings": "Preview & Settings",
                "action_control": "Action Control",
                
                # File management area
                "selected_files": "{} selected",
                "max_files": "Max 10 files",
                "add_files": "Add Files",
                "delete_selected": "Delete Selected",
                "clear_list": "Clear List",
                
                # Original preview area
                "original_preview": "Original Preview",
                "reset": "Reset",
                "rotate_left": "Rotate Left",
                "rotate_right": "Rotate Right",
                "flip_horizontal": "Flip Horizontal",
                "angle": "Angle",
                "dimensions": "Dimensions",
                
                # Split preview area
                "split_preview": "Split Preview",
                "split_info": "Split: {}×{} | Total: {} images",
                
                # Parameter settings area
                "param_settings": "Parameter Settings",
                "split_mode": "Split Mode",
                "auto_detect": "Auto",
                "manual": "Manual",
                "rows": "Rows",
                "cols": "Columns",
                "output_format": "Output Format",
                "png_transparent": "PNG (Transparent)",
                "jpg_small": "JPG (Smaller File)",
                
                # Action control area
                "process_progress": "Processing Progress",
                "ready": "Ready...",
                "start_process": "Start Processing",
                "open_output": "Open Output",
                "process_log": "Process Log",
                "clear_log": "Clear Log",
                
                # Settings dialog
                "settings_title": "App Settings",
                "settings_subtitle": "Personalize Your Experience",
                "output_path": "Output Path",
                "default_output_dir": "Default Output Directory",
                "browse": "Browse",
                "about_app": "About Cut It",
                "app_info_support": "App Info & Support",
                "version": "Version",
                "view_details": "View Details",
                "restore_defaults": "Restore Defaults",
                "close": "Close",
                
                # About dialog
                "about_title": "About Cut It",
                "app_description": "A modern image cropping and sticker splitting tool",
                "features": "Core Features",
                "milestones": "Project Progress",
                "badges": "Project Achievements",
                "support_ways": "Support Ways",
                "thanks": "Thank you for your support and trust!",
                
                # Support ways
                "star_github": "Star on GitHub",
                "github_desc": "Star the project on GitHub",
                "qq_email": "QQ Email",
                "gmail": "Gmail",
                
                # Social links
                "github": "GitHub",
                "email": "Email",
                
                # General
                "confirm": "Confirm",
                "cancel": "Cancel",
                "ok": "OK",
                "language": "Language",
                "选择界面显示语言": "Select interface language",
                "语言设置已保存，部分更改将在下次启动时生效。": "Language settings saved. Some changes will take effect after restart",
            }
        }
    
    def set_language(self, language: str) -> None:
        """
        设置当前语言
        
        Args:
            language: 语言代码 ("zh" 或 "en")
        """
        if language in self.translations:
            self.current_language = language
    
    def get_text(self, key: str) -> str:
        """
        获取指定键的翻译文本
        
        Args:
            key: 文本键名
            
        Returns:
            翻译后的文本
        """
        return self.translations[self.current_language].get(key, key)
    
    def get_all_texts(self) -> Dict[str, str]:
        """
        获取当前语言的所有文本
        
        Returns:
            文本字典
        """
        return self.translations[self.current_language]
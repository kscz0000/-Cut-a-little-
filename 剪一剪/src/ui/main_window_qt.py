#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪一剪 - 表情包分割器 V2.0 (PyQt6版本)
现代化UI设计 + 高性能图像处理
"""
import os
import sys
import math
import json
import gc
import weakref
import platform
import subprocess
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

# PyQt6组件
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFileDialog,
    QMessageBox, QProgressBar, QTextEdit, QSpinBox, QRadioButton, 
    QButtonGroup, QComboBox, QSizePolicy, QListWidget, QGroupBox,
    QDialog, QMenu, QCheckBox
)
from PyQt6.QtGui import (
    QPixmap, QIcon, QFont, QDesktopServices, QMouseEvent, QWheelEvent,
    QDragEnterEvent, QDropEvent, QPaintEvent, QPainter, QPen, QColor,
    QImage, QAction, QTransform
)
from PyQt6.QtCore import (
    Qt, QTimer, QUrl, QPoint, pyqtSignal, QObject, QThread, QMutex,
    QMutexLocker, QRect, QEasingCurve
)

# 确保正确的模块导入路径
# 移除相对路径添加，使用setup.py配置确保模块可找到

from core.settings_manager import SettingsManager
from core.language_manager import LanguageManager
from core.image_processor import ImageProcessor
from core.file_manager import FileManager
from core.edge_detection.smart_edge_detector import SmartEdgeDetector
from core.edge_detection.enhanced_edge_detector import EnhancedEdgeDetector
from core.edge_detection.dl_edge_detector import DLEdgeDetector
from core.edge_detection.adaptive_edge_detector import AdaptiveEdgeDetector
from core.edge_detection.enhanced_smart_edge_detector import EnhancedSmartEdgeDetector
from core.edge_detection.optimized_smart_edge_detector import OptimizedSmartEdgeDetector
# 尝试导入深度学习边缘检测器，如果失败则使用占位符
try:
    # 深度学习边缘检测器已移除
# 根据用户要求，删除了边缘线处理相关功能
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    # 创建一个占位符类
    class DeepLearningEdgeDetector:
        def __init__(self):
            pass
        
        def detect_and_remove_edges(self, image, mode='auto'):
            # 回退到基础检测器
            from core.edge_detection.smart_edge_detector import SmartEdgeDetector
            detector = SmartEdgeDetector()
            return detector.detect_and_remove_edges(image, mode)
        
        def preview_detection(self, image, mode='auto'):
            # 回退到基础检测器
            from core.edge_detection.smart_edge_detector import SmartEdgeDetector
            detector = SmartEdgeDetector()
            return detector.preview_detection(image)
    
    DEEP_LEARNING_AVAILABLE = False
from core.edge_detection.simple_smart_crop_dialog import SimpleSmartCropDialog
from utils.validators import Validators
import time
import numpy as np
from PIL import Image


# ==================== 配置管理 ====================
class AboutConfig:
    """关于页面配置"""
    VERSION = "v2.0.0"
    APP_NAME = "剪一剪"
    RELEASE_DATE = "2025-01-25"
    
    # 链接配置
    GITHUB_URL = "https://github.com/剪一剪/jianyijian"
    TWITTER_URL = "https://twitter.com/your-handle"
    EMAIL = "byilb3619b@gmail.com"
    ISSUES_URL = "https://github.com/剪一剪/jianyijian/issues"
    
    # 特性列表
    FEATURES = [
        ("⚡ 极速处理", "GPU加速，毫秒级响应", "🚀"),
        ("🎯 智能识别", "自动检测九宫格/四宫格", "🤖"),
        ("💎 高质输出", "无损分割，保持原画质", "✨"),
        ("🔄 批量操作", "一次处理多个文件", "📦"),
    ]
    
    # 支持方式
    SUPPORT_ITEMS = [
        ("⭐", "Star on GitHub", "在 GitHub 上为项目加星标", GITHUB_URL),
        ("📧", "QQ邮箱", "1715635335", None),
        ("✉️", "谷歌邮箱", "byilb3619b@gmail.com", None),
    ]
    
    # 社交链接
    SOCIAL_LINKS = [
        ("GitHub", "🐙", GITHUB_URL, "#333333"),
        ("Email", "✉️", f"mailto:{EMAIL}", "#EA4335"),
    ]


# ==================== 缓存系统（优化版） ====================
class ImageCache:
    """图像缓存类 - LRU策略（性能优化）"""
    
    def __init__(self, max_size: int = 15, max_memory_mb: int = 50):
        """初始化缓存
        
        Args:
            max_size: 最大缓存数量
            max_memory_mb: 最大内存使用（MB）
        """
        self.cache = {}  # {(path, angle): QPixmap}
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory = 0
        self.access_order = []  # LRU访问顺序
        self._lock = QMutex()  # 线程安全
    
    def _estimate_pixmap_size(self, pixmap: QPixmap) -> int:
        """估算QPixmap内存占用（优化版）"""
        if pixmap.isNull():
            return 0
        # 更准确的估算：width * height * 4 (RGBA)
        return pixmap.width() * pixmap.height() * 4
    
    def get(self, file_path: str, angle: float) -> Optional[QPixmap]:
        """获取缓存的图像（线程安全）"""
        with QMutexLocker(self._lock):
            key = (file_path, int(angle))
            if key in self.cache:
                # 更新访问顺序
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
        return None
    
    def put(self, file_path: str, angle: float, pixmap: QPixmap) -> None:
        """存入缓存（带内存管理，线程安全）"""
        with QMutexLocker(self._lock):
            key = (file_path, int(angle))
            pixmap_size = self._estimate_pixmap_size(pixmap)
            
            # 如果单个图片超过最大内存限制，不缓存
            if pixmap_size > self.max_memory_bytes:
                return
            
            # 释放内存直到有足够空间
            while (self.current_memory + pixmap_size > self.max_memory_bytes or 
                   len(self.cache) >= self.max_size) and self.access_order:
                oldest = self.access_order.pop(0)
                if oldest in self.cache:
                    old_pixmap = self.cache[oldest]
                    self.current_memory -= self._estimate_pixmap_size(old_pixmap)
                    del self.cache[oldest]
            
            # 存入缓存
            self.cache[key] = pixmap
            self.current_memory += pixmap_size
            
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self) -> None:
        """清空缓存"""
        with QMutexLocker(self._lock):
            self.cache.clear()
            self.access_order.clear()
            self.current_memory = 0
        gc.collect()
    
    def clear_file(self, file_path: str) -> None:
        """清除指定文件的所有缓存"""
        with QMutexLocker(self._lock):
            keys_to_remove = [k for k in self.cache.keys() if k[0] == file_path]
            for key in keys_to_remove:
                pixmap = self.cache[key]
                self.current_memory -= self._estimate_pixmap_size(pixmap)
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)


class SplitCache:
    """分割结果缓存类（优化版）"""
    
    def __init__(self, max_size: int = 10):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
        self._lock = QMutex()
    
    def get(self, file_path: str, angle: float, rows: int, cols: int) -> Optional[list]:
        """获取缓存的分割结果"""
        with QMutexLocker(self._lock):
            key = (file_path, int(angle), rows, cols)
            if key in self.cache:
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
        return None
    
    def put(self, file_path: str, angle: float, rows: int, cols: int, images: list) -> None:
        """存入缓存"""
        with QMutexLocker(self._lock):
            key = (file_path, int(angle), rows, cols)
            
            # LRU淘汰
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest = self.access_order.pop(0)
                if oldest in self.cache:
                    del self.cache[oldest]
            
            self.cache[key] = images
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self) -> None:
        """清空缓存"""
        with QMutexLocker(self._lock):
            self.cache.clear()
            self.access_order.clear()
        gc.collect()


# ==================== 自定义组件 ====================
class ClickableLabel(QLabel):
    """可点击的标签（优化版）"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pressed = False
    
    def mousePressEvent(self, ev):
        """鼠标按下事件"""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
        super().mousePressEvent(ev)
    
    def mouseReleaseEvent(self, ev):
        """鼠标释放事件"""
        if ev and ev.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self.clicked.emit()
        super().mouseReleaseEvent(ev)


class InteractiveLabel(QLabel):
    """可交互的标签组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._click_handler = None
    
    def set_click_handler(self, handler):
        """设置点击处理函数"""
        self._click_handler = handler
    
    def mousePressEvent(self, ev):
        """鼠标按下事件"""
        if self._click_handler and ev and ev.button() == Qt.MouseButton.LeftButton:
            self._click_handler(ev)
        super().mousePressEvent(ev)


class RotatableLabel(QLabel):
    """可旋转的图片标签 - GPU加速（优化版）"""
    
    dragging_rotation = pyqtSignal(float)
    final_rotation = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start = None
        self.last_angle = 0
        self.current_angle = 0
        self.is_dragging = False
        
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def mousePressEvent(self, ev):
        """鼠标按下事件"""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.drag_start = ev.pos()
            self.last_angle = self.current_angle
            self.is_dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, ev):
        """鼠标移动事件"""
        if self.drag_start is not None and ev and (ev.buttons() & Qt.MouseButton.LeftButton):
            center = self.rect().center()
            
            angle1 = math.atan2(
                self.drag_start.y() - center.y(),
                self.drag_start.x() - center.x()
            )
            
            angle2 = math.atan2(
                ev.pos().y() - center.y(),
                ev.pos().x() - center.x()
            )
            
            delta_angle = math.degrees(angle2 - angle1)
            new_angle = (self.last_angle + delta_angle) % 360
            self.current_angle = new_angle
            
            self.dragging_rotation.emit(new_angle)
    
    def mouseReleaseEvent(self, ev):
        """鼠标释放事件"""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.drag_start = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            
            if self.is_dragging:
                self.is_dragging = False
                self.final_rotation.emit(self.current_angle)
    
    def reset_angle(self):
        """重置角度"""
        self.current_angle = 0
        self.last_angle = 0
    
    def set_angle(self, angle):
        """设置角度"""
        self.current_angle = angle
        self.last_angle = angle


class ProcessThread(QThread):
    """处理线程（优化版）"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, int, float)
    log = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, files, rotation_angles, settings, parent=None):
        super().__init__(parent)
        self.files = files
        self.rotation_angles = rotation_angles
        self.settings = settings
        self.image_processor = ImageProcessor()
        self.file_manager = FileManager()
        self.edge_detector = SmartEdgeDetector()
        self.enhanced_edge_detector = EnhancedEdgeDetector()
        self.dl_edge_detector = DLEdgeDetector()
        self.adaptive_edge_detector = AdaptiveEdgeDetector()
        self.enhanced_smart_edge_detector = EnhancedSmartEdgeDetector()
        self.optimized_smart_edge_detector = OptimizedSmartEdgeDetector()
        self.deep_learning_edge_detector = DeepLearningEdgeDetector()
        self._is_cancelled = False
    
    def cancel(self):
        """取消处理"""
        self._is_cancelled = True
    
    def run(self):
        """执行处理"""
        total = len(self.files)
        success_count = 0
        fail_count = 0
        start_time = time.time()
        
        try:
            for i, file_path in enumerate(self.files):
                if self._is_cancelled:
                    self.log.emit("处理已取消")
                    break
                
                progress = int((i / total) * 100)
                filename = os.path.basename(file_path)
                
                self.progress.emit(progress, f"处理中: {i+1}/{total} - {filename}")
                self.log.emit(f"[处理] {filename}")
                
                try:
                    success = self.process_single_file(file_path)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    self.log.emit(f"  [异常] {str(e)}")
                    self.error.emit(f"处理 {filename} 时出错: {str(e)}")
                    fail_count += 1
            
            elapsed = time.time() - start_time
            self.progress.emit(100, "处理完成！")
            self.finished.emit(success_count, fail_count, elapsed)
            
        except Exception as e:
            self.error.emit(f"线程异常: {str(e)}")
            self.finished.emit(success_count, fail_count, time.time() - start_time)
    
    def process_single_file(self, file_path: str) -> bool:
        """处理单个文件"""
        try:
            image = self.image_processor.load_image(file_path)
            if not image:
                self.log.emit(f"  [失败] 无法加载图片")
                return False
            
            angle = self.rotation_angles.get(file_path, 0)
            if angle != 0:
                image = self.image_processor.rotate_image(image, angle)
            
            # 智能边缘线识别功能已移除
            # 根据用户要求，删除了边缘线处理相关逻辑
            
            if self.settings['mode'] == 'auto':
                grid_type = self.image_processor.detect_grid_type(*image.size)
                rows, cols = (3, 3) if grid_type == "9grid" else (2, 2)
            else:
                rows = self.settings['rows']
                cols = self.settings['cols']
            
            split_images = self.image_processor.crop_by_lines(image, rows, cols)
            
            base_path = self.file_manager.get_output_path(file_path)
            folder_name = self.file_manager.generate_output_folder_name(os.path.basename(file_path))
            
            success, output_path = self.file_manager.create_output_folder(base_path, folder_name)
            if not success:
                self.log.emit(f"  [失败] {output_path}")
                return False
            
            output_format = self.settings['format']
            saved_count, failed_files = self.file_manager.save_split_images(
                split_images,
                output_path,
                os.path.basename(file_path),
                output_format
            )
            
            if failed_files:
                for error in failed_files:
                    self.log.emit(f"  [失败] {error}")
            
            self.log.emit(f"  [成功] 已保存 {saved_count} 张图片 -> {os.path.basename(output_path)}")
            
            return saved_count > 0
            
        except Exception as e:
            self.log.emit(f"  [异常] {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ModernButton(QPushButton):
    """现代化按钮组件（优化版）"""
    
    def __init__(self, text, style='primary', parent=None):
        super().__init__(text, parent)
        self.setFont(QFont('Microsoft YaHei UI', 9))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        
        styles = {
            'primary': {
                'bg': '#4CAF50',
                'hover': '#66BB6A',
                'pressed': '#388E3C',
                'text': '#FFFFFF'
            },
            'success': {
                'bg': '#4CAF50',
                'hover': '#66BB6A',
                'pressed': '#388E3C',
                'text': '#FFFFFF'
            },
            'danger': {
                'bg': '#E53935',
                'hover': '#EF5350',
                'pressed': '#C62828',
                'text': '#FFFFFF'
            },
            'secondary': {
                'bg': '#78909C',
                'hover': '#90A4AE',
                'pressed': '#546E7A',
                'text': '#FFFFFF'
            }
        }
        
        s = styles.get(style, styles['primary'])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {s['bg']};
                color: {s['text']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {s['hover']};
            }}
            QPushButton:pressed {{
                background-color: {s['pressed']};
                padding-top: 11px;
                padding-bottom: 9px;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
        """)


# ==================== 主窗口 ====================
class MainWindowQt(QMainWindow):
    """PyQt6主窗口 - 完整优化版"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.settings = SettingsManager()
        self.language_manager = LanguageManager()
        self.image_processor = ImageProcessor()
        self.file_manager = FileManager()
        self.validators = Validators()
        # 边缘检测器已移除
        # 根据用户要求，删除了边缘线处理相关功能
        
        # 设置当前语言
        language = self.settings.get("language", "zh")
        self.language_manager.set_language(language)
        
        # 状态变量
        self.selected_files = []
        self.current_file_index = -1
        self.rotation_angles = {}
        
        # UI组件文本映射（用于语言切换时更新文本）
        self.ui_text_mapping = {}
        self.current_image = None
        self.current_pixmap = None
        self.processing = False
        self.last_output_folder = None
        
        # 图像缓存系统
        self.image_cache = ImageCache(max_size=15, max_memory_mb=100)
        self.split_cache = SplitCache(max_size=20)
        
        # QPixmap原始缓存
        self.original_pixmap_raw = None
        
        # 防抖Timer（单例）
        self._rotation_timer = QTimer(self)
        self._rotation_timer.setSingleShot(True)
        self._rotation_timer.timeout.connect(self._on_rotation_timer_timeout)
        
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.update_preview)
        
        # 处理线程引用（使用弱引用避免循环引用）
        self._process_thread_ref = None
        
        # 主题颜色
        self.theme = {
            'bg_primary': '#F5F7FA',
            'bg_secondary': '#FFFFFF',
            'bg_accent': '#ECEFF1',
            'bg_card': '#FAFAFA',
            'primary': '#4CAF50',
            'primary_hover': '#66BB6A',
            'success': '#4CAF50',
            'danger': '#E53935',
            'warning': '#FF9800',
            'text_primary': '#212121',
            'text_secondary': '#616161',
            'text_tertiary': '#9E9E9E',
            'border': '#E0E0E0',
            'shadow': 'rgba(0, 0, 0, 0.08)',
        }
        
        # 初始化UI
        self.init_ui()
        
        # 添加初始日志
        app_name = self.language_manager.get_text("app_title")
        self.show_log(f"{app_name} 已启动")
        self.show_log("专业级图像分割工具")
        self.show_log("功能: 预览 | 旋转 | 批量处理 | 导出")
        self.show_log("请添加图片文件开始")
        self.show_log("="*50)
    
    def _on_rotation_timer_timeout(self):
        """旋转Timer超时回调"""
        self.update_preview()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{AboutConfig.APP_NAME} {AboutConfig.VERSION}")
        self.setGeometry(100, 100, 1280, 800)
        self.setMinimumSize(800, 650)
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme['bg_primary']};
            }}
            QLabel {{
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QWidget {{
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QPushButton {{
                font-weight: bold;
            }}
            QRadioButton {{
                font-weight: bold;
            }}
            QSpinBox {{
                font-weight: bold;
            }}
            QListWidget {{
                font-weight: bold;
            }}
            QTextEdit {{
                font-weight: bold;
            }}
            QProgressBar {{
                font-weight: bold;
            }}
        """)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 主内容区
        content = self.create_content_area()
        main_layout.addWidget(content, 1)
    
    def create_content_area(self):
        """创建主内容区"""
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 左侧文件管理面板
        left_panel = self.create_file_panel()
        layout.addWidget(left_panel)
        
        # 中间预览与设置面板
        center_panel = self.create_preview_panel()
        layout.addWidget(center_panel, 1)
        
        # 右侧操作面板
        right_panel = self.create_action_panel()
        layout.addWidget(right_panel)
        
        return content
    
    def create_file_panel(self):
        """创建文件管理面板（修复版 - 按钮不被遮挡）"""
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_secondary']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel(self.language_manager.get_text("file_management"))
        title.setFont(QFont('Microsoft YaHei UI', 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[title] = "file_management"
        layout.addWidget(title)
        
        # 文件列表（增加弹性空间）
        self.file_list = QListWidget()
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Microsoft YaHei UI';
                font-size: 9pt;
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QListWidget::item {{
                padding: 12px 10px;
                border-radius: 4px;
                margin: 3px 0;
                color: {self.theme['text_secondary']};
                font-weight: bold;
            }}
            QListWidget::item:selected {{
                background-color: {self.theme['primary']};
                color: white;
                font-weight: bold;
            }}
            QListWidget::item:hover {{
                background-color: {self.theme['bg_accent']};
                font-weight: bold;
            }}
        """)
        self.file_list.setDragEnabled(True)
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.file_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_file_context_menu)
        # 关键修复：设置最小高度，确保列表不会被压缩
        self.file_list.setMinimumHeight(250)
        layout.addWidget(self.file_list, 1)  # stretch factor = 1，占据剩余空间
        
        # 文件信息
        file_info_layout = QHBoxLayout()
        file_info_layout.setSpacing(8)
        
        self.file_count_label = QLabel(self._get_file_count_text(0))
        self.file_count_label.setFont(QFont('Microsoft YaHei UI', 9))
        self.file_count_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        file_info_layout.addWidget(self.file_count_label)
        
        file_info_layout.addStretch()
        
        max_label = QLabel("(最多10个)")
        max_label.setFont(QFont('Microsoft YaHei UI', 9))
        max_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        file_info_layout.addWidget(max_label)
        
        layout.addLayout(file_info_layout)
        
        # 按钮区域 - 使用固定高度容器确保按钮可见
        btn_container = QWidget()
        btn_container.setFixedHeight(140)  # 固定高度确保按钮可见
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        
        # 添加文件按钮
        add_btn = QPushButton(self.language_manager.get_text("add_files"))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFixedHeight(40)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: #388E3C;
            }}
        """)
        add_btn.clicked.connect(self.add_files)
        # 添加到文本映射
        self.ui_text_mapping[add_btn] = "add_files"
        btn_layout.addWidget(add_btn)
        
        # 删除和清空按钮 - 横向排列
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setSpacing(10)
        
        delete_btn = QPushButton(self.language_manager.get_text("delete_selected"))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedHeight(40)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: #F44336;
            }}
            QPushButton:pressed {{
                background-color: #D32F2F;
            }}
        """)
        delete_btn.clicked.connect(self.delete_selected_files)
        # 添加到文本映射
        self.ui_text_mapping[delete_btn] = "delete_selected"
        bottom_btn_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton(self.language_manager.get_text("clear_list"))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setFixedHeight(40)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['bg_accent']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['border']};
            }}
            QPushButton:pressed {{
                background-color: #CFD8DC;
            }}
        """)
        clear_btn.clicked.connect(self.clear_file_list)
        # 添加到文本映射
        self.ui_text_mapping[clear_btn] = "clear_list"
        bottom_btn_layout.addWidget(clear_btn)
        
        btn_layout.addLayout(bottom_btn_layout)
        
        layout.addWidget(btn_container)
        
        return panel
    
    def _get_file_count_text(self, count: int) -> str:
        """获取文件计数文本（性能优化）"""
        if count >= 10:
            return f"已选择 {count} 个文件 (已达上限)"
        else:
            return f"已选择 {count} 个文件"
    
    def create_preview_panel(self):
        """创建预览面板"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_secondary']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 预览区域容器
        preview_container = QWidget()
        preview_layout = QHBoxLayout(preview_container)
        preview_layout.setSpacing(16)
        
        # 左侧：原图预览
        left_preview = self.create_original_preview()
        preview_layout.addWidget(left_preview)
        
        # 右侧：分割预览
        right_preview = self.create_split_preview()
        preview_layout.addWidget(right_preview, 1)
        
        layout.addWidget(preview_container, 1)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {self.theme['border']};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # 设置区域
        settings_widget = self.create_settings_panel()
        layout.addWidget(settings_widget)
        
        return panel
    
    def create_original_preview(self):
        """创建原图预览区域"""
        frame = QFrame()
        frame.setFixedWidth(280)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_card']};
                border-radius: 6px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题和重置按钮
        title_layout = QHBoxLayout()
        
        title = QLabel(self.language_manager.get_text("original_preview"))
        title.setFont(QFont('Microsoft YaHei UI', 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[title] = "original_preview"
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        btn_reset = QPushButton(self.language_manager.get_text("reset"))
        btn_reset.setFont(QFont('Microsoft YaHei UI', 9))
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setFixedSize(60, 28)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['bg_accent']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary']};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {self.theme['primary_hover']};
            }}
        """)
        btn_reset.clicked.connect(self.reset_rotation)
        # 添加到文本映射
        self.ui_text_mapping[btn_reset] = "reset"
        title_layout.addWidget(btn_reset)
        
        layout.addLayout(title_layout)
        
        # 图片显示区域
        self.original_label = RotatableLabel()
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setMinimumSize(240, 240)
        self.original_label.setScaledContents(False)
        self.original_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme['bg_accent']};
                border: 2px dashed {self.theme['border']};
                border-radius: 6px;
                color: {self.theme['text_tertiary']};
            }}
        """)
        self.original_label.setText("未选择图片")
        self.original_label.dragging_rotation.connect(self.on_dragging_rotation)
        self.original_label.final_rotation.connect(self.on_final_rotation)
        layout.addWidget(self.original_label, 1)
        
        # 图片信息
        self.image_info_label = QLabel("角度: 0° | 尺寸: --")
        self.image_info_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        self.image_info_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_info_label)
        
        return frame
    
    def create_split_preview(self):
        """创建分割预览区域"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_card']};
                border-radius: 6px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel(self.language_manager.get_text("split_preview"))
        title.setFont(QFont('Microsoft YaHei UI', 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[title] = "split_preview"
        layout.addWidget(title)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['bg_accent']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
            }}
            QScrollBar:vertical {{
                background-color: {self.theme['bg_card']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme['border']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # 分割预览容器
        self.split_container = QWidget()
        self.split_layout = QGridLayout(self.split_container)
        self.split_layout.setSpacing(8)
        self.split_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.split_container)
        layout.addWidget(scroll, 1)
        
        # 分割信息
        self.split_info_label = QLabel("分割: -- | 总数: --")
        self.split_info_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        self.split_info_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        layout.addWidget(self.split_info_label)
        
        return frame
    
    def create_settings_panel(self):
        """创建设置面板"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_card']};
                border-radius: 6px;
                border: 1px solid {self.theme['border']};
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel(self.language_manager.get_text("param_settings"))
        title.setFont(QFont('Microsoft YaHei UI', 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[title] = "param_settings"
        layout.addWidget(title)
        
        # 分割模式
        mode_layout = QHBoxLayout()
        mode_label = QLabel(self.language_manager.get_text("split_mode"))
        mode_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        mode_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        # 添加到文本映射
        self.ui_text_mapping[mode_label] = "split_mode"
        mode_layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup()
        self.radio_auto = QRadioButton(self.language_manager.get_text("auto_detect"))
        self.radio_manual = QRadioButton(self.language_manager.get_text("manual"))
        self.radio_auto.setChecked(True)
        # 添加到文本映射
        self.ui_text_mapping[self.radio_auto] = "auto_detect"
        self.ui_text_mapping[self.radio_manual] = "manual"
        
        radio_style = f"""
            QRadioButton {{
                color: {self.theme['text_primary']};
                spacing: 6px;
                font-size: 9pt;
                font-weight: bold;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid {self.theme['border']};
                border-radius: 8px;
                background-color: white;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {self.theme['primary']};
                border-radius: 8px;
                background-color: {self.theme['primary']};
            }}
        """
        
        self.radio_auto.setStyleSheet(radio_style)
        self.radio_manual.setStyleSheet(radio_style)
        
        self.mode_group.addButton(self.radio_auto, 0)
        self.mode_group.addButton(self.radio_manual, 1)
        
        mode_layout.addWidget(self.radio_auto)
        mode_layout.addWidget(self.radio_manual)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 行列设置
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(20)
        
        # 行数设置
        row_container = QWidget()
        row_layout = QHBoxLayout(row_container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        
        row_label = QLabel(self.language_manager.get_text("rows"))
        row_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        row_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        # 添加到文本映射
        self.ui_text_mapping[row_label] = "rows"
        row_layout.addWidget(row_label)
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 18)
        self.rows_spin.setValue(3)
        self.rows_spin.setFixedWidth(70)
        self.rows_spin.setStyleSheet(f"""
            QSpinBox {{
                padding: 6px 10px;
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                background-color: white;
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QSpinBox:hover {{
                border-color: {self.theme['primary']};
            }}
            QSpinBox:focus {{
                border-color: {self.theme['primary']};
                border-width: 2px;
            }}
        """)
        self.rows_spin.valueChanged.connect(self.on_settings_change)
        row_layout.addWidget(self.rows_spin)
        
        grid_layout.addWidget(row_container)
        
        # 列数设置
        col_container = QWidget()
        col_layout = QHBoxLayout(col_container)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(8)
        
        col_label = QLabel(self.language_manager.get_text("cols"))
        col_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        col_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        # 添加到文本映射
        self.ui_text_mapping[col_label] = "cols"
        col_layout.addWidget(col_label)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 18)
        self.cols_spin.setValue(3)
        self.cols_spin.setFixedWidth(70)
        self.cols_spin.setStyleSheet(f"""
            QSpinBox {{
                padding: 6px 10px;
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                background-color: white;
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QSpinBox:hover {{
                border-color: {self.theme['primary']};
            }}
            QSpinBox:focus {{
                border-color: {self.theme['primary']};
                border-width: 2px;
            }}
        """)
        self.cols_spin.valueChanged.connect(self.on_settings_change)
        col_layout.addWidget(self.cols_spin)
        
        grid_layout.addWidget(col_container)
        grid_layout.addStretch()
        layout.addLayout(grid_layout)
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_label = QLabel(self.language_manager.get_text("output_format"))
        format_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        format_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        format_layout.addWidget(format_label)
        
        self.format_group = QButtonGroup()
        self.radio_png = QRadioButton(self.language_manager.get_text("png_transparent"))
        self.radio_jpg = QRadioButton(self.language_manager.get_text("jpg_small"))
        self.radio_png.setChecked(True)
        # 添加到文本映射
        self.ui_text_mapping[self.radio_png] = "png_transparent"
        self.ui_text_mapping[self.radio_jpg] = "jpg_small"
        
        self.radio_png.setStyleSheet(radio_style)
        self.radio_jpg.setStyleSheet(radio_style)
        
        self.format_group.addButton(self.radio_png, 0)
        self.format_group.addButton(self.radio_jpg, 1)
        
        format_layout.addWidget(self.radio_png)
        format_layout.addWidget(self.radio_jpg)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # 绑定参数变化事件
        self.mode_group.buttonClicked.connect(lambda: self.on_settings_change())
        
        return panel
    
    def on_settings_change(self):
        """设置变更时更新预览（防抖优化）"""
        if self.current_image and self.current_file_index != -1:
            self._update_timer.stop()
            self._update_timer.start(150)  # 减少防抖延迟到150ms以提高响应性
    
    def create_action_panel(self):
        """创建操作面板"""
        panel = QFrame()
        panel.setFixedWidth(300)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_secondary']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 顶部：标题和设置按钮
        title_layout = QHBoxLayout()
        
        title = QLabel(self.language_manager.get_text("action_control"))
        title.setFont(QFont('Microsoft YaHei UI', 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[title] = "action_control"
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        settings_btn = QPushButton(self.language_manager.get_text("settings_title"))
        settings_btn.setFont(QFont('Microsoft YaHei UI', 9))
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setFixedSize(60, 32)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['bg_accent']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary']};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {self.theme['primary_hover']};
            }}
        """)
        settings_btn.clicked.connect(self.show_settings)
        # 添加到文本映射
        self.ui_text_mapping[settings_btn] = "settings_title"
        title_layout.addWidget(settings_btn)
        
        layout.addLayout(title_layout)
        
        # 进度区域
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_card']};
                border-radius: 6px;
                border: 1px solid {self.theme['border']};
                padding: 16px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        
        progress_title = QLabel(self.language_manager.get_text("process_progress"))
        progress_title.setFont(QFont('Microsoft YaHei UI', 10, QFont.Weight.Bold))
        # 添加到文本映射
        self.ui_text_mapping[progress_title] = "process_progress"
        progress_layout.addWidget(progress_title)
        
        self.progress_label = QLabel("准备就绪...")
        self.progress_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        self.progress_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
                height: 26px;
                background-color: {self.theme['bg_accent']};
                color: {self.theme['text_primary']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['primary']};
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # 操作按钮
        # 智能裁剪按钮已移除
        # 根据用户要求，删除了边缘线处理相关功能
        
        self.process_btn = ModernButton(self.language_manager.get_text("start_process"), 'success')
        self.process_btn.setMinimumHeight(48)
        self.process_btn.clicked.connect(self.start_processing)
        # 添加到文本映射
        self.ui_text_mapping[self.process_btn] = "start_process"
        layout.addWidget(self.process_btn)
        
        btn_open = ModernButton(self.language_manager.get_text("open_output"), 'primary')
        btn_open.clicked.connect(self.open_output_folder)
        # 添加到文本映射
        self.ui_text_mapping[btn_open] = "open_output"
        layout.addWidget(btn_open)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {self.theme['border']};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # 日志区域
        log_title = QLabel(self.language_manager.get_text("process_log"))
        log_title.setFont(QFont('Microsoft YaHei UI', 11, QFont.Weight.Bold))
        # 添加到文本映射
        self.ui_text_mapping[log_title] = "process_log"
        layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['bg_card']};
                color: {self.theme['text_secondary']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                line-height: 1.6;
                font-weight: bold;
            }}
            QScrollBar:vertical {{
                background-color: {self.theme['bg_card']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme['border']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        layout.addWidget(self.log_text, 1)
        
        btn_clear_log = ModernButton(self.language_manager.get_text("clear_log"), 'secondary')
        btn_clear_log.clicked.connect(self.clear_log)
        # 添加到文本映射
        self.ui_text_mapping[btn_clear_log] = "clear_log"
        layout.addWidget(btn_clear_log)
        
        return panel
    
    # ==================== 事件处理方法 ====================
    
    def add_files(self):
        """添加文件（性能优化）"""
        if len(self.selected_files) >= 10:
            QMessageBox.warning(self, "提示", "已达文件数量上限（10个），无法继续添加")
            return
        
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择图片文件",
                self.settings.get("last_directory", ""),
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.webp);;所有文件 (*.*)"
            )
            
            if not files:
                return
            
            added_count = 0
            first_added_index = len(self.selected_files)
            
            for file_path in files:
                if len(self.selected_files) >= 10:
                    QMessageBox.warning(self, "提示", f"已达文件数量上限（10个），成功添加 {added_count} 个文件")
                    break
                
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    # 性能优化：直接添加到列表，避免重建整个列表
                    self.file_list.addItem(f"{len(self.selected_files)}. {os.path.basename(file_path)}")
                    added_count += 1
            
            # 更新文件计数
            self._update_file_count_label()
            
            if files:
                self.settings.set("last_directory", os.path.dirname(files[0]))
            
            # 自动选中第一个新添加的文件
            if added_count > 0:
                if self.current_file_index == -1:
                    self.file_list.setCurrentRow(first_added_index)
                    self.on_file_select(first_added_index)
            
            self.show_log(f"已添加 {added_count} 个文件")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加文件失败: {str(e)}")
            self.show_log(f"[错误] 添加文件失败: {str(e)}")
    
    def _update_file_count_label(self):
        """更新文件计数标签（性能优化）"""
        count = len(self.selected_files)
        self.file_count_label.setText(self._get_file_count_text(count))
        
        if count >= 10:
            self.file_count_label.setStyleSheet(f"color: {self.theme['danger']};")
        else:
            self.file_count_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
    
    def delete_selected_files(self):
        """删除选中文件"""
        self.remove_selected()
    
    def remove_selected(self):
        """删除选中文件（性能优化）"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            removed_file = self.selected_files.pop(current_row)
            self.image_cache.clear_file(removed_file)
            
            # 性能优化：直接移除项，然后重新编号
            self.file_list.takeItem(current_row)
            
            # 重新编号剩余项
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                if item:
                    filename = os.path.basename(self.selected_files[i])
                    item.setText(f"{i+1}. {filename}")
            
            # 更新当前选中项
            if self.selected_files:  # 如果还有剩余文件
                # 确保current_row不超过剩余文件数量
                new_current_row = min(current_row, len(self.selected_files) - 1)
                if new_current_row >= 0:
                    self.file_list.setCurrentRow(new_current_row)
                    self.on_file_select(new_current_row)
                else:
                    # 如果没有剩余文件，清空预览
                    self.current_image = None
                    self.current_pixmap = None
                    self.original_pixmap_raw = None
                    self.original_label.clear()
                    self.original_label.setText("未选择图片")
                    self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.image_info_label.setText("角度: 0° | 尺寸: --")
                    self.clear_split_preview()
            else:
                # 没有剩余文件，清空预览
                self.current_image = None
                self.current_pixmap = None
                self.original_pixmap_raw = None
                self.original_label.clear()
                self.original_label.setText("未选择图片")
                self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.image_info_label.setText("角度: 0° | 尺寸: --")
                self.clear_split_preview()
            
            self._update_file_count_label()
            self.show_log(f"已删除: {os.path.basename(removed_file)}")
    
    def clear_file_list(self):
        """清空文件列表"""
        self.clear_files()
    
    def clear_files(self):
        """清空文件列表（性能优化）"""
        self.selected_files.clear()
        self.rotation_angles.clear()
        self.current_file_index = -1
        
        self.current_image = None
        self.current_pixmap = None
        self.original_pixmap_raw = None
        
        # 性能优化：直接清空列表
        self.file_list.clear()
        self._update_file_count_label()
        
        self.original_label.clear()
        self.original_label.setText("未选择图片")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_info_label.setText("角度: 0° | 尺寸: --")
        
        self.clear_split_preview()
        
        self.image_cache.clear()
        self.split_cache.clear()
        
        self.show_log("已清空文件列表")
    
    def show_file_context_menu(self, position):
        """显示文件列表上下文菜单"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.theme['bg_secondary']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 4px 0px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                color: {self.theme['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {self.theme['primary']};
                color: white;
            }}
        """)
        
        delete_action = QAction("删除选中", self)
        delete_action.triggered.connect(self.remove_selected)
        context_menu.addAction(delete_action)
        
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(self.clear_files)
        context_menu.addAction(clear_action)
        
        context_menu.exec(self.file_list.mapToGlobal(position))
    
    def update_file_list(self):
        """更新文件列表（已废弃，保留兼容性）"""
        # 为了兼容性保留，实际使用增量更新
        self._update_file_count_label()
    
    def on_file_selection_changed(self):
        """文件选择变更事件"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.on_file_select(current_row)
    
    def on_file_select(self, index):
        """文件选择事件（性能优化）"""
        if index >= 0 and index < len(self.selected_files):
            self.current_file_index = index
            file_path = self.selected_files[index]
            
            try:
                # 性能优化：延迟加载图像
                self.current_image = self.image_processor.load_image(file_path)
                if self.current_image:
                    if file_path not in self.rotation_angles:
                        self.rotation_angles[file_path] = 0
                    
                    current_angle = self.rotation_angles.get(file_path, 0)
                    self.original_label.set_angle(current_angle)
                    
                    # 异步更新预览，避免阻塞UI
                    QTimer.singleShot(50, self.update_preview)
                    
                    width, height = self.current_image.size
                    self.show_log(f"已选中: {os.path.basename(file_path)} ({width}x{height}px)")
                else:
                    self.show_log(f"[错误] 无法加载: {os.path.basename(file_path)}")
            except Exception as e:
                self.show_log(f"[错误] 加载失败: {str(e)}")
    
    def update_preview(self):
        """更新预览显示（性能优化）"""
        if not self.current_image or self.current_file_index == -1:
            self.original_label.clear()
            self.original_label.setText("未选择图片")
            self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_info_label.setText("角度: 0° | 尺寸: --")
            self.clear_split_preview()
            return
        
        try:
            file_path = self.selected_files[self.current_file_index]
            angle = self.rotation_angles.get(file_path, 0)
            
            # 先检查缓存
            cached_pixmap = self.image_cache.get(file_path, angle)
            
            if cached_pixmap:
                rotated = self.current_image if angle == 0 else self.image_processor.rotate_image(self.current_image, angle)
                self.original_label.setPixmap(cached_pixmap)
                self.current_pixmap = cached_pixmap
                
                width, height = rotated.size
                self.image_info_label.setText(f"角度: {int(angle)}° | 尺寸: {width}x{height}px")
                
                self.update_split_preview(rotated)
            else:
                if angle != 0:
                    rotated = self.image_processor.rotate_image(self.current_image, angle)
                else:
                    rotated = self.current_image
                
                self.update_original_preview(rotated, angle, file_path)
                self.update_split_preview(rotated)
                
        except Exception as e:
            self.show_log(f"[错误] 更新预览失败: {str(e)}")
    
    def update_original_preview(self, image, angle, file_path):
        """更新原图预览（性能优化）"""
        try:
            thumb = self.image_processor.create_thumbnail(image, (240, 240))
            
            qimage = self.pil_to_qimage(thumb)
            pixmap = QPixmap.fromImage(qimage)
            
            # 存入缓存
            self.image_cache.put(file_path, angle, pixmap)
            
            if angle == 0:
                self.original_pixmap_raw = pixmap.copy()
            else:
                if self.current_image:
                    original_thumb = self.image_processor.create_thumbnail(self.current_image, (240, 240))
                    original_qimage = self.pil_to_qimage(original_thumb)
                    self.original_pixmap_raw = QPixmap.fromImage(original_qimage)
            
            self.original_label.setPixmap(pixmap)
            self.current_pixmap = pixmap
            
            width, height = image.size
            self.image_info_label.setText(f"角度: {int(angle)}° | 尺寸: {width}x{height}px")
            
        except Exception as e:
            self.show_log(f"[错误] 更新原图预览失败: {str(e)}")
    
    def clear_split_preview(self):
        """清空分割预览区域（性能优化）"""
        # 批量删除，避免逐个删除的开销
        while self.split_layout.count():
            item = self.split_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        
        self.split_info_label.setText("分割: -- | 总数: --")
        self.split_info_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
    
    def update_split_preview(self, image):
        """更新分割预览（性能优化）"""
        try:
            # 清空现有预览
            while self.split_layout.count():
                item = self.split_layout.takeAt(0)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
            
            # 获取分割参数
            if self.radio_auto.isChecked():
                grid_type = self.image_processor.detect_grid_type(*image.size)
                rows, cols = (3, 3) if grid_type == "9grid" else (2, 2)
            else:
                rows = self.rows_spin.value()
                cols = self.cols_spin.value()
            
            valid, error_msg = self.validators.validate_grid_size(rows, cols)
            if not valid:
                self.split_info_label.setText(f"错误: {error_msg}")
                self.split_info_label.setStyleSheet(f"color: {self.theme['danger']};")
                return
            
            # 执行分割
            split_images = self.image_processor.crop_by_lines(image, rows, cols)
            
            total_count = len(split_images)
            cols_per_row = min(6, cols)
            available_width = 450 - 20 - (cols_per_row - 1) * 8
            thumb_width = available_width // cols_per_row
            thumb_width = max(40, min(80, thumb_width))
            thumb_size = (thumb_width, thumb_width)
            
            # 批量创建缩略图
            for i, img in enumerate(split_images):
                thumb = self.image_processor.create_thumbnail(img, thumb_size)
                qimage = self.pil_to_qimage(thumb)
                pixmap = QPixmap.fromImage(qimage)
                
                item_widget = QWidget()
                item_widget.setFixedSize(thumb_size[0] + 10, thumb_size[1] + 32)
                item_layout = QVBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 4, 4, 4)
                item_layout.setSpacing(4)
                
                img_label = QLabel()
                img_label.setFixedSize(thumb_size[0], thumb_size[1])
                img_label.setPixmap(pixmap)
                img_label.setScaledContents(True)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: white;
                        border: 1px solid {self.theme['border']};
                        border-radius: 3px;
                    }}
                """)
                item_layout.addWidget(img_label)
                
                w, h = img.size
                info_label = QLabel(f"{i+1}: {w}x{h}")
                info_label.setFont(QFont('Microsoft YaHei UI', 8))
                info_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
                info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(info_label)
                
                row = i // cols_per_row
                col = i % cols_per_row
                self.split_layout.addWidget(item_widget, row, col)
            
            self.split_info_label.setText(f"分割: {rows}×{cols} | 总数: {total_count}张")
            self.split_info_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
            
        except Exception as e:
            self.show_log(f"[错误] 更新分割预览失败: {str(e)}")
    
    def pil_to_qimage(self, pil_image: Image.Image) -> QImage:
        """PIL Image转QImage（修复颜色问题）"""
        try:
            if pil_image.mode == "RGB":
                data = pil_image.tobytes("raw", "RGB")
                qimage = QImage(data, pil_image.size[0], pil_image.size[1], 
                               QImage.Format.Format_RGB888)
            elif pil_image.mode == "RGBA":
                data = pil_image.tobytes("raw", "RGBA")
                qimage = QImage(data, pil_image.size[0], pil_image.size[1], 
                               QImage.Format.Format_RGBA8888)
            elif pil_image.mode == "P":
                pil_image = pil_image.convert("RGBA")
                data = pil_image.tobytes("raw", "RGBA")
                qimage = QImage(data, pil_image.size[0], pil_image.size[1], 
                               QImage.Format.Format_RGBA8888)
            else:
                pil_image = pil_image.convert("RGBA")
                data = pil_image.tobytes("raw", "RGBA")
                qimage = QImage(data, pil_image.size[0], pil_image.size[1], 
                               QImage.Format.Format_RGBA8888)
            
            return qimage.copy()
            
        except Exception as e:
            print(f"图像转换失败: {e}")
            return QImage()
    
    def on_dragging_rotation(self, angle):
        """拖动旋转事件（实时预览 - 性能优化）"""
        if self.current_image and self.current_file_index != -1:
            file_path = self.selected_files[self.current_file_index]
            
            if self.original_pixmap_raw:
                transform = QTransform()
                transform.rotate(angle)
                rotated_pixmap = self.original_pixmap_raw.transformed(
                    transform, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.original_label.setPixmap(rotated_pixmap)
                self.current_pixmap = rotated_pixmap
                
                self.image_info_label.setText(
                    f"角度: {int(angle)}° | 尺寸: {self.current_image.size[0]}x{self.current_image.size[1]}px"
                )
            
            self.rotation_angles[file_path] = angle
            
            # 防抖：拖动时延迟更新分割预览
            self._rotation_timer.stop()
            self._rotation_timer.start(100)  # 减少延迟到100ms以提高响应性
    
    def reset_rotation(self):
        """重置旋转角度"""
        if self.current_image and self.current_file_index != -1:
            file_path = self.selected_files[self.current_file_index]
            self.rotation_angles[file_path] = 0
            self.original_label.reset_angle()
            self.update_preview()
            self.show_log("已重置旋转角度")
    
    def on_final_rotation(self, angle):
        """最终旋转事件（高质量更新）"""
        if self.current_image and self.current_file_index != -1:
            file_path = self.selected_files[self.current_file_index]
            self.rotation_angles[file_path] = angle
            self.update_preview()
            self.show_log(f"旋转完成 -> 角度: {int(angle)}°")
    
    def start_processing(self):
        """开始处理"""
        if not self.selected_files:
            QMessageBox.warning(self, "提示", "请先添加图片文件！")
            return
        
        if self.processing:
            return
        
        if not self.radio_auto.isChecked():
            rows = self.rows_spin.value()
            cols = self.cols_spin.value()
            valid, error_msg = self.validators.validate_grid_size(rows, cols)
            if not valid:
                QMessageBox.critical(self, "错误", error_msg)
                return
        
        settings = {
            'mode': 'auto' if self.radio_auto.isChecked() else 'custom',
            'rows': self.rows_spin.value(),
            'cols': self.cols_spin.value(),
            'format': 'PNG' if self.radio_png.isChecked() else 'JPG'
        }
        
        self.processing = True
        self.process_btn.setEnabled(False)
        self.process_btn.setText("处理中...")
        
        self.show_log("开始批量处理...")
        
        process_thread = ProcessThread(
            self.selected_files.copy(),
            self.rotation_angles.copy(),
            settings,
            self
        )
        
        # 使用弱引用避免循环引用
        self._process_thread_ref = weakref.ref(process_thread)
        
        process_thread.progress.connect(self.on_progress_update)
        process_thread.log.connect(self.show_log)
        process_thread.error.connect(self.show_error)
        process_thread.finished.connect(self.on_processing_complete)
        process_thread.finished.connect(process_thread.deleteLater)
        
        process_thread.start()
    
    def on_progress_update(self, value: int, text: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(text)
    
    def on_processing_complete(self, success: int, fail: int, elapsed: float):
        """处理完成回调"""
        self.processing = False
        self.process_btn.setEnabled(True)
        self.process_btn.setText("开始处理")
        
        total = success + fail
        elapsed_str = f"{elapsed:.1f}秒" if elapsed < 60 else f"{int(elapsed//60)}分{int(elapsed%60)}秒"
        
        message = f"处理完成！\n\n成功: {success} 个\n失败: {fail} 个\n总耗时: {elapsed_str}"
        
        self.show_log("="*50)
        self.show_log(f"处理完成！成功 {success} 个，失败 {fail} 个，共耗时 {elapsed_str}")
        self.show_log("="*50)
        
        QMessageBox.information(self, "处理完成", message)
    
    def show_error(self, error_msg: str):
        """显示错误信息"""
        self.show_log(f"[错误] {error_msg}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        try:
            if self.last_output_folder and os.path.exists(self.last_output_folder):
                self._open_folder(self.last_output_folder)
            else:
                if self.selected_files:
                    base_path = self.file_manager.get_output_path(self.selected_files[0])
                    if os.path.exists(base_path):
                        self._open_folder(base_path)
                    else:
                        QMessageBox.information(self, "提示", "没有可打开的输出文件夹。\n请先完成图片处理。")
                else:
                    QMessageBox.information(self, "提示", "没有可打开的输出文件夹。\n请先完成图片处理。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开文件夹失败: {str(e)}")
            self.show_log(f"[错误] 打开文件夹失败: {str(e)}")
    
    def _open_folder(self, folder_path: str):
        """跨平台打开文件夹"""
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
                
            self.show_log(f"已打开: {folder_path}")
            
        except Exception as e:
            raise Exception(f"无法打开文件夹: {str(e)}")
    
    # 智能裁剪功能已移除
    # 根据用户要求，删除了边缘线处理相关功能
    
    def show_log(self, message):
        """添加日志（性能优化）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 性能优化：批量滚动
        QTimer.singleShot(10, lambda: self._scroll_to_bottom())
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.show_log("日志已清空")
    
    # ==================== 设置对话框（优化版）====================
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.language_manager.get_text("settings_title"))
        dialog.setFixedSize(520, 480)
        dialog.setStyleSheet(f"background-color: {self.theme['bg_primary']};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部标题栏
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['primary']};
                border-radius: 0px;
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel(self.language_manager.get_text("settings_title"))
        title.setFont(QFont('Microsoft YaHei UI', 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("自定义您的工作流程")
        subtitle.setFont(QFont('Microsoft YaHei UI', 9))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F5F7FA;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #CBD5E0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4CAF50;
            }
        """)
        
        # 内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(16)
        
        # 输出路径设置
        path_card = self._create_settings_card("输出路径", "默认输出目录")
        path_card_layout = path_card.findChild(QVBoxLayout)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        self.settings_path_label = QLabel(self.settings.get('custom_output_path', '') or '与原图相同')
        self.settings_path_label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 12px 16px;
                color: {self.theme['text_secondary']};
                font-size: 9pt;
            }}
        """)
        self.settings_path_label.setWordWrap(True)
        path_layout.addWidget(self.settings_path_label, 1)
        
        path_btn = QPushButton("浏览")
        path_btn.setFixedWidth(100)
        path_btn.setFixedHeight(44)
        path_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: #388E3C;
            }}
        """)
        path_btn.clicked.connect(lambda: self._select_output_directory(dialog))
        # 添加到文本映射
        self.ui_text_mapping[path_btn] = "browse"
        path_layout.addWidget(path_btn)
        
        path_card_layout.addLayout(path_layout)
        content_layout.addWidget(path_card)
        
        # 语言设置
        language_card = self._create_settings_card("语言设置", "选择界面显示语言")
        language_card_layout = language_card.findChild(QVBoxLayout)
        
        language_layout = QHBoxLayout()
        language_layout.setSpacing(10)
        
        language_label = QLabel("语言")
        language_label.setFont(QFont('Microsoft YaHei UI', 9, QFont.Weight.Bold))
        language_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        # 添加到文本映射
        self.ui_text_mapping[language_label] = "language"
        language_layout.addWidget(language_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setFixedWidth(200)
        self.language_combo.setFixedHeight(40)
        self.language_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10pt;
                font-weight: bold;
            }}
            QComboBox:hover {{
                border-color: {self.theme['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.theme['text_secondary']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                selection-background-color: {self.theme['primary']};
                selection-color: white;
            }}
        """)
        
        # 添加语言选项
        self.language_combo.addItem("🇨🇳 中文 (Chinese)", "zh")
        self.language_combo.addItem("🇺🇸 English (English)", "en")
        
        # 设置当前语言
        current_language = self.settings.get("language", "zh")
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # 连接信号（延迟连接避免初始化时触发）
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        
        language_card_layout.addLayout(language_layout)
        content_layout.addWidget(language_card)
        
        # 智能边缘线识别设置已移除
        # 根据用户要求，删除了边缘线处理相关选项
        
        # 关于应用区域
        about_card = self._create_settings_card("关于应用", "应用信息与支持")
        about_card_layout = about_card.findChild(QVBoxLayout)
        
        # 版本信息
        version_layout = QHBoxLayout()
        version_icon = QLabel("🎨")
        version_icon.setFont(QFont('Segoe UI Emoji', 16))
        version_layout.addWidget(version_icon)
        
        version_text = QLabel(f"<b>版本 {AboutConfig.VERSION}</b><br><span style='color: #9E9E9E;'>PyQt6 + 现代化设计</span>")
        version_text.setFont(QFont('Microsoft YaHei UI', 9))
        version_layout.addWidget(version_text, 1)
        about_card_layout.addLayout(version_layout)
        
        # 按钮容器
        btn_container = QHBoxLayout()
        btn_container.setSpacing(12)
        
        about_btn = QPushButton("查看详情")
        about_btn.setFixedHeight(40)
        about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {self.theme['text_primary']};
                border: 2px solid {self.theme['primary']};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary']};
                color: white;
            }}
        """)
        about_btn.clicked.connect(lambda: self.show_about_dialog(dialog))
        # 添加到文本映射
        self.ui_text_mapping[about_btn] = "view_details"
        btn_container.addWidget(about_btn)
        
        restore_btn = QPushButton("恢复默认")
        restore_btn.setFixedHeight(40)
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['bg_accent']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['border']};
            }}
        """)
        restore_btn.clicked.connect(self._restore_default_settings)
        # 添加到文本映射
        self.ui_text_mapping[restore_btn] = "restore_defaults"
        btn_container.addWidget(restore_btn)
        
        about_card_layout.addLayout(btn_container)
        content_layout.addWidget(about_card)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, 1)
        
        # 底部按钮
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {self.theme['bg_secondary']}; border-top: 1px solid {self.theme['border']};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 16, 30, 16)
        footer_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(120)
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary_hover']};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        # 添加到文本映射
        self.ui_text_mapping[close_btn] = "close"
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer)
        
        # 保存设置
        def save_settings():
            # 边缘线识别设置已移除
            # 根据用户要求，删除了边缘线处理相关选项
            pass
        
        dialog.finished.connect(save_settings)
        
        dialog.exec()
    
    def _create_settings_card(self, title: str, subtitle: str = "") -> QFrame:
        """创建设置卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_secondary']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setFont(QFont('Microsoft YaHei UI', 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        layout.addWidget(title_label)
        
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont('Microsoft YaHei UI', 9))
            subtitle_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
            layout.addWidget(subtitle_label)
        
        return card
    
    def _select_output_directory(self, parent_dialog):
        """选择输出目录"""
        current_path = self.settings.get('custom_output_path', '') or os.path.expanduser("~/Pictures")
        
        directory = QFileDialog.getExistingDirectory(
            parent_dialog,
            "选择输出目录",
            current_path
        )
        
        if directory:
            self.settings.set('custom_output_path', directory)
            if hasattr(self, 'settings_path_label'):
                self.settings_path_label.setText(directory)
            self.show_log(f"已设置输出路径: {directory}")
    
    def _restore_default_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, 
            "确认", 
            "确定要恢复所有默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.set('custom_output_path', '')
            self.settings.set('show_appreciation', True)
            if hasattr(self, 'settings_path_label'):
                self.settings_path_label.setText('与原图相同')
            QMessageBox.information(self, "提示", "已恢复默认设置")
            self.show_log("已恢复默认设置")
    
    def _on_language_changed(self, index):
        """语言切换事件处理（优化版）"""
        if index < 0:
            return
        
        language_code = self.language_combo.itemData(index)
        if not language_code:
            return
        
        previous_language = self.settings.get("language", "zh")
        
        # 只有当语言真正发生变化时才进行更新
        if previous_language != language_code:
            # 保存语言设置
            self.settings.set("language", language_code)
            self.language_manager.set_language(language_code)
            
            # 使用QTimer延迟更新，确保语言管理器完全加载
            QTimer.singleShot(100, self.update_ui_texts)
            
            # 显示提示（延迟200ms确保UI已更新）
            QTimer.singleShot(200, lambda: QMessageBox.information(
                self,
                "确认",
                "语言设置已保存，界面已更新。",
                QMessageBox.StandardButton.Ok
            ))
    
    def update_ui_texts(self):
        """更新界面文本（完整优化版）"""
        try:
            # 1. 更新窗口标题
            self.setWindowTitle(f"{AboutConfig.APP_NAME} {AboutConfig.VERSION}")
            
            # 2. 更新文件计数标签
            self._update_file_count_label()
            
            # 3. 更新图像信息标签
            if hasattr(self, 'image_info_label') and self.image_info_label:
                if self.current_image and self.current_file_index != -1:
                    file_path = self.selected_files[self.current_file_index]
                    angle = self.rotation_angles.get(file_path, 0)
                    width, height = self.current_image.size
                    self.image_info_label.setText(f"角度: {int(angle)}° | 尺寸: {width}x{height}px")
                else:
                    self.image_info_label.setText("角度: 0° | 尺寸: --")
            
            # 4. 更新进度标签
            if hasattr(self, 'progress_label') and self.progress_label:
                if not self.processing and self.progress_label.text() in ["准备就绪...", "Ready..."]:
                    self.progress_label.setText("准备就绪...")
            
            # 5. 更新处理按钮
            if hasattr(self, 'process_btn') and self.process_btn:
                if not self.processing:
                    self.process_btn.setText(self.language_manager.get_text("start_process") or "开始处理")
            
            # 6. 遍历UI文本映射更新所有组件文本
            for widget, text_key in self.ui_text_mapping.items():
                if hasattr(widget, 'setText') and text_key:
                    widget.setText(self.language_manager.get_text(text_key))
            
            # 7. 更新日志
            self.show_log("语言已切换")
            
        except Exception as e:
            print(f"更新UI文本失败: {e}")
            import traceback
            traceback.print_exc()
    
    # ==================== 关于对话框（完整优化版）====================
    
    def show_about_dialog(self, parent_dialog):
        """显示关于对话框"""
        parent_dialog.hide()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"关于{AboutConfig.APP_NAME}")
        dialog.setFixedSize(540, 750)
        dialog.setStyleSheet(f"background-color: {self.theme['bg_primary']};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ========== 顶部展示区 ==========
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.theme['primary']}, 
                    stop:1 {self.theme['primary_hover']});
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 30, 40, 30)
        header_layout.setSpacing(15)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 主图片
        main_image = QLabel()
        main_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 尝试加载图片
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        image_paths = [
            os.path.join(project_root, "@AGI.png"),
            os.path.join(os.getcwd(), "@AGI.png"),
            os.path.join(os.path.dirname(project_root), "@AGI.png")
        ]
        
        image_loaded = False
        for img_path in image_paths:
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                                 Qt.TransformationMode.SmoothTransformation)
                    main_image.setPixmap(scaled_pixmap)
                    image_loaded = True
                    break
        
        if not image_loaded:
            main_image.setText("🎨")
            main_image.setFont(QFont('Segoe UI Emoji', 64))
            main_image.setStyleSheet("color: white;")
        
        header_layout.addWidget(main_image)
        
        # 应用名称
        app_name = QLabel(AboutConfig.APP_NAME)
        app_name.setFont(QFont('Microsoft YaHei UI', 24, QFont.Weight.Bold))
        app_name.setStyleSheet("color: white;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(app_name)
        
        # 版本标签
        version_badge = QLabel(AboutConfig.VERSION)
        version_badge.setFont(QFont('Microsoft YaHei UI', 10, QFont.Weight.Bold))
        version_badge.setStyleSheet("""
            color: white;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 4px 16px;
        """)
        version_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version_badge)
        
        layout.addWidget(header)
        
        # ========== 滚动内容区 ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)
        
        # === 1. 项目统计卡片 ===
        stats_card = self._create_about_card()
        stats_layout = stats_card.findChild(QVBoxLayout)
        
        stats_title = QLabel("🚀 项目特性")
        stats_title.setFont(QFont('Microsoft YaHei UI', 13, QFont.Weight.Bold))
        stats_layout.addWidget(stats_title)
        
        # 统计项
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(15)
        
        stats_items = [
            ("⚡", "快速", "毫秒级处理"),
            ("🎯", "精准", "智能识别"),
            ("💯", "高质", "无损输出")
        ]
        
        for emoji, title, desc in stats_items:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(4)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            emoji_label = QLabel(emoji)
            emoji_label.setFont(QFont('Segoe UI Emoji', 24))
            emoji_label.setStyleSheet(f"color: {self.theme['primary']};")
            emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(emoji_label)
            
            title_label = QLabel(title)
            title_label.setFont(QFont('Microsoft YaHei UI', 11, QFont.Weight.Bold))
            title_label.setStyleSheet(f"color: {self.theme['text_primary']};")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(title_label)
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont('Microsoft YaHei UI', 8))
            desc_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(desc_label)
            
            stats_grid.addWidget(stat_widget)
        
        stats_layout.addLayout(stats_grid)
        content_layout.addWidget(stats_card)
        
        # === 2. 作者信息卡片 ===
        author_card = self._create_about_card()
        author_layout = author_card.findChild(QVBoxLayout)
        
        # 作者头像和信息
        author_header = QHBoxLayout()
        author_header.setSpacing(16)
        
        avatar = ClickableLabel()
        avatar.setFixedSize(80, 80)
        avatar.setStyleSheet(f"""
            QLabel {{
                border: 3px solid {self.theme['primary']};
                border-radius: 40px;
                background-color: white;
            }}
        """)
        
        # 尝试加载作者头像
        author_img_paths = [
            os.path.join(project_root, "cai.jpg"),
            os.path.join(os.getcwd(), "cai.jpg")
        ]
        
        avatar_loaded = False
        for img_path in author_img_paths:
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(74, 74, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
                    avatar.setPixmap(scaled)
                    avatar_loaded = True
                    break
        
        if not avatar_loaded:
            avatar.setText("👨‍💻")
            avatar.setFont(QFont('Segoe UI Emoji', 32))
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 移除作者头像的点击跳转功能，仅保留显示功能
        avatar.setCursor(Qt.CursorShape.ArrowCursor)
        # 断开所有可能的连接
        try:
            avatar.clicked.disconnect()
        except:
            pass
        author_header.addWidget(avatar)
        
        # 作者文字信息
        author_info = QVBoxLayout()
        author_info.setSpacing(6)
        
        author_name = QLabel("剪一剪团队")
        author_name.setFont(QFont('Microsoft YaHei UI', 14, QFont.Weight.Bold))
        author_name.setStyleSheet(f"color: {self.theme['text_primary']};")
        author_info.addWidget(author_name)
        
        author_desc = QLabel("专注图像处理工具开发")
        author_desc.setFont(QFont('Microsoft YaHei UI', 9))
        author_desc.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        author_info.addWidget(author_desc)
        
        author_header.addLayout(author_info, 1)
        author_layout.addLayout(author_header)
        
        # 关注按钮 - 移除跳转功能
        follow_btn = QPushButton("⭐ 关注作者")
        follow_btn.setFixedHeight(42)
        follow_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary_hover']};
            }}
        """)
        # 移除关注按钮的点击跳转功能，仅保留显示功能
        follow_btn.setCursor(Qt.CursorShape.ArrowCursor)
        # 断开所有可能的连接
        try:
            follow_btn.clicked.disconnect()
        except:
            pass
        author_layout.addWidget(follow_btn)
        
        content_layout.addWidget(author_card)
        
        # === 3. 支持方式卡片 ===
        support_card = self._create_about_card()
        support_layout = support_card.findChild(QVBoxLayout)
        
        support_title = QLabel("💕 支持方式")
        support_title.setFont(QFont('Microsoft YaHei UI', 13, QFont.Weight.Bold))
        support_layout.addWidget(support_title)
        
        # 支持列表
        for emoji, title, desc, url in AboutConfig.SUPPORT_ITEMS:
            item_card = QFrame()
            item_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme['bg_card']};
                    border-radius: 8px;
                    border: 1px solid {self.theme['border']};
                    padding: 12px;
                }}
                QFrame:hover {{
                    background-color: {self.theme['bg_accent']};
                    border-color: {self.theme['primary']};
                }}
            """)
            
            # 默认情况下所有元素均无交互功能
            item_card.setCursor(Qt.CursorShape.ArrowCursor)
            
            item_layout = QHBoxLayout(item_card)
            item_layout.setSpacing(12)
            
            icon_label = QLabel(emoji)
            icon_label.setFont(QFont('Segoe UI Emoji', 20))
            icon_label.setFixedWidth(40)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 图标无交互功能
            icon_label.setCursor(Qt.CursorShape.ArrowCursor)
            item_layout.addWidget(icon_label)
            
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            title_label = QLabel(title)
            title_label.setFont(QFont('Microsoft YaHei UI', 10, QFont.Weight.Bold))
            title_label.setStyleSheet(f"color: {self.theme['text_primary']};")
            # 标题无交互功能
            title_label.setCursor(Qt.CursorShape.ArrowCursor)
            text_layout.addWidget(title_label)
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont('Microsoft YaHei UI', 9))
            desc_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
            
            # 严格按照要求设置交互功能
            if url and title == "Star on GitHub":
                # 仅GitHub按钮保留跳转功能
                desc_label.setCursor(Qt.CursorShape.PointingHandCursor)
                # 创建跳转处理函数
                def make_url_handler(url):
                    def handler(ev):
                        if ev and ev.button() == Qt.MouseButton.LeftButton:
                            QDesktopServices.openUrl(QUrl(url))
                    return handler
                desc_label.mousePressEvent = make_url_handler(url)
            elif title in ["QQ邮箱", "谷歌邮箱"]:
                # 仅QQ邮箱和谷歌邮箱按钮保留复制功能
                desc_label.setCursor(Qt.CursorShape.PointingHandCursor)
                # 创建复制处理函数
                def make_copy_handler(text):
                    def handler(ev):
                        if ev and ev.button() == Qt.MouseButton.LeftButton:
                            self._copy_to_clipboard(text)
                    return handler
                desc_label.mousePressEvent = make_copy_handler(desc)
            else:
                # 其他所有元素均无交互功能
                desc_label.setCursor(Qt.CursorShape.ArrowCursor)
            
            text_layout.addWidget(desc_label)
            
            item_layout.addLayout(text_layout, 1)
            support_layout.addWidget(item_card)
        
        content_layout.addWidget(support_card)
        
        # === 4. 感谢语 ===
        thanks = QLabel("感谢您的支持与信任！")
        thanks.setFont(QFont('Microsoft YaHei UI', 10))
        thanks.setStyleSheet(f"color: {self.theme['text_tertiary']};")
        thanks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 感谢语无交互功能
        thanks.setCursor(Qt.CursorShape.ArrowCursor)
        content_layout.addWidget(thanks)
        
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        
        # ========== 底部按钮 ==========
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {self.theme['bg_secondary']}; border-top: 1px solid {self.theme['border']};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 16, 30, 16)
        footer_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(120)
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['primary_hover']};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        close_btn.clicked.connect(parent_dialog.show)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer)
        
        # 对话框关闭时显示设置对话框
        dialog.finished.connect(parent_dialog.show)
        
        dialog.exec()
    
    def _create_about_card(self) -> QFrame:
        """创建关于页面卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['bg_secondary']};
                border-radius: 12px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        return card
    
    def _copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
            # 显示简洁的提示信息
            QMessageBox.information(self, "复制成功", f"邮箱地址已复制到剪贴板：\n{text}")
    
    # ==================== 窗口关闭事件 ====================
    
    def closeEvent(self, a0):
        """窗口关闭事件处理（性能优化）"""
        # 停止所有Timer
        if self._rotation_timer.isActive():
            self._rotation_timer.stop()
        if self._update_timer.isActive():
            self._update_timer.stop()
        
        # 检查是否有正在运行的处理线程
        if self._process_thread_ref is not None:
            process_thread = self._process_thread_ref()
            if process_thread is not None and process_thread.isRunning():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理文件，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    process_thread.cancel()
                    process_thread.wait(3000)
                    if a0 is not None:
                        a0.accept()
                else:
                    if a0 is not None:
                        a0.ignore()
                    return
        
        # 清理缓存
        self.image_cache.clear()
        self.split_cache.clear()
        
        # 清理图像引用
        self.current_image = None
        self.current_pixmap = None
        self.original_pixmap_raw = None
        
        # 强制垃圾回收
        gc.collect()
        
        if a0 is not None:
            a0.accept()


# ==================== 程序入口 ====================
def main():
    """主函数"""
    import sys
    
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(AboutConfig.APP_NAME)
    app.setApplicationVersion(AboutConfig.VERSION)
    app.setOrganizationName("剪一剪团队")
    
    # 设置应用图标（如果存在）
    icon_path = os.path.join(os.getcwd(), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 创建主窗口
    window = MainWindowQt()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
"""
简化版智能裁剪对话框
只保留核心的智能裁剪功能，移除不必要的复杂设置和预览功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PIL import Image

# 动态导入检测器类，避免依赖问题
# from .smart_edge_detector import SmartEdgeDetector
# from .enhanced_edge_detector import EnhancedEdgeDetector
# from .dl_edge_detector import DLEdgeDetector
# from .adaptive_edge_detector import AdaptiveEdgeDetector
# from .enhanced_smart_edge_detector import EnhancedSmartEdgeDetector
# from .optimized_smart_edge_detector import OptimizedSmartEdgeDetector
# from .deep_learning_edge_detector import DeepLearningEdgeDetector


class SimpleSmartCropDialog(QDialog):
    """简化版智能裁剪对话框"""
    
    # 信号：裁剪完成
    crop_completed = pyqtSignal(object)  # PIL Image
    
    def __init__(self, image: Image.Image, detector_type: str = 'basic', parent=None):
        super().__init__(parent)
        self.original_image = image
        self.detector_type = detector_type
        self.detector = self._create_detector(detector_type)
        self.result_image = None
        
        self.setWindowTitle("智能裁剪")
        self.setFixedSize(400, 200)
        
        self._init_ui()
    
    def _create_detector(self, detector_type: str):
        """根据类型创建检测器"""
        # 动态导入检测器类
        try:
            if detector_type == 'basic':
                from .smart_edge_detector import SmartEdgeDetector
                return SmartEdgeDetector()
            elif detector_type == 'enhanced':
                from .enhanced_edge_detector import EnhancedEdgeDetector
                return EnhancedEdgeDetector()
            elif detector_type == 'dl':
                from .dl_edge_detector import DLEdgeDetector
                return DLEdgeDetector()
            elif detector_type == 'adaptive':
                from .adaptive_edge_detector import AdaptiveEdgeDetector
                return AdaptiveEdgeDetector()
            elif detector_type == 'enhanced_smart':
                from .enhanced_smart_edge_detector import EnhancedSmartEdgeDetector
                return EnhancedSmartEdgeDetector()
            elif detector_type == 'optimized_smart':
                from .optimized_smart_edge_detector import OptimizedSmartEdgeDetector
                return OptimizedSmartEdgeDetector()
            elif detector_type == 'deep_learning':
                from .deep_learning_edge_detector import DeepLearningEdgeDetector
                return DeepLearningEdgeDetector()
            else:
                from .smart_edge_detector import SmartEdgeDetector
                return SmartEdgeDetector()
        except ImportError as e:
            print(f"无法导入检测器 {detector_type}: {e}")
            # 回退到基础检测器
            from .smart_edge_detector import SmartEdgeDetector
            return SmartEdgeDetector()
    
    def _init_ui(self):
        """初始化简化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === 标题 ===
        title = QLabel("智能裁剪")
        title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #2196F3;
                text-align: center;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # === 说明文字 ===
        info_label = QLabel("此功能将自动检测并移除图片中的多余边缘线")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #666666;
                text-align: center;
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === 按钮区域 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 应用按钮
        apply_btn = QPushButton("应用")
        apply_btn.setFixedWidth(80)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self._apply_crop)
        button_layout.addWidget(apply_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _apply_crop(self):
        """应用裁剪"""
        try:
            # 使用默认的自动检测模式
            self.result_image = self.detector.detect_and_remove_edges(
                self.original_image, 'auto'
            )
            
            # 发送信号
            self.crop_completed.emit(self.result_image)
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"智能裁剪失败: {str(e)}")
"""
将智能边缘线检测功能集成到剪一剪应用的示例代码
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QComboBox, QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import numpy as np

from .smart_edge_detector import SmartEdgeDetector


class SmartCropDialog(QDialog):
    """智能裁剪对话框"""
    
    # 信号：裁剪完成
    crop_completed = pyqtSignal(object)  # PIL Image
    
    def __init__(self, image: Image.Image, parent=None):
        super().__init__(parent)
        self.original_image = image
        self.detector = SmartEdgeDetector()
        self.preview_image = None
        self.result_image = None
        
        self.setWindowTitle("智能边缘线检测")
        self.setMinimumSize(800, 600)
        
        self._init_ui()
        self._update_preview()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === 标题 ===
        title = QLabel("🎯 智能边缘线检测与移除")
        title.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #2196F3;
            }
        """)
        layout.addWidget(title)
        
        # === 预览区域 ===
        preview_group = QGroupBox("预览效果")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                min-height: 300px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(preview_group)
        
        # === 控制面板 ===
        control_group = QGroupBox("检测参数")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(12)
        
        # 检测模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("检测模式:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "自动检测 (推荐)",
            "激进模式 (移除更多)",
            "保守模式 (移除更少)",
            "AI优化模式",
            "深度学习模式",
            "自适应模式"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        control_layout.addLayout(mode_layout)
        
        # 敏感度调节
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("边缘检测敏感度:"))
        
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sensitivity_slider.setTickInterval(1)
        self.sensitivity_slider.valueChanged.connect(self._on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        self.sensitivity_value = QLabel("5")
        self.sensitivity_value.setStyleSheet("font-weight: bold;")
        sensitivity_layout.addWidget(self.sensitivity_value)
        control_layout.addLayout(sensitivity_layout)
        
        # 实时预览选项
        self.preview_checkbox = QCheckBox("显示检测边界框 (预览)")
        self.preview_checkbox.setChecked(True)
        self.preview_checkbox.stateChanged.connect(self._update_preview)
        control_layout.addWidget(self.preview_checkbox)
        
        layout.addWidget(control_group)
        
        # === 信息显示 ===
        self.info_label = QLabel("💡 提示：调整参数以获得最佳效果")
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 6px;
                padding: 10px;
                color: #1976D2;
            }
        """)
        layout.addWidget(self.info_label)
        
        # === 按钮区域 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 重置按钮
        reset_btn = QPushButton("🔄 重置")
        reset_btn.setFixedWidth(120)
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(120)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 应用按钮
        apply_btn = QPushButton("✅ 应用裁剪")
        apply_btn.setFixedWidth(120)
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
        
        layout.addLayout(button_layout)
    
    def _get_current_mode(self) -> str:
        """获取当前检测模式"""
        mode_map = {
            0: 'auto',
            1: 'aggressive',
            2: 'conservative',
            3: 'ai_optimized',
            4: 'dl_optimized',
            5: 'adaptive'
        }
        return mode_map.get(self.mode_combo.currentIndex(), 'auto')
    
    def _update_preview(self):
        """更新预览图"""
        try:
            if self.preview_checkbox.isChecked():
                # 显示检测边界框
                self.preview_image = self.detector.preview_detection(self.original_image)
            else:
                # 显示裁剪结果
                mode = self._get_current_mode()
                self.preview_image = self.detector.detect_and_remove_edges(
                    self.original_image, mode
                )
            
            # 转换为QPixmap显示
            self._display_image(self.preview_image)
            
            # 更新信息
            orig_size = self.original_image.size
            new_size = self.preview_image.size
            saved_percent = (1 - (new_size[0] * new_size[1]) / (orig_size[0] * orig_size[1])) * 100
            
            self.info_label.setText(
                f"📊 原始尺寸: {orig_size[0]}×{orig_size[1]} → "
                f"裁剪后: {new_size[0]}×{new_size[1]} "
                f"(节省 {saved_percent:.1f}% 空间)"
            )
            
        except Exception as e:
            self.info_label.setText(f"⚠️ 错误: {str(e)}")
    
    def _display_image(self, image: Image.Image):
        """将PIL图像显示到QLabel"""
        # 转换为QImage
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        if len(img_array.shape) == 3:
            # 转换为字节数据
            img_bytes = img_array.tobytes()
            bytes_per_line = 3 * w
            q_image = QImage(img_bytes, w, h, bytes_per_line, 
                           QImage.Format.Format_RGB888)
        else:
            # 转换为字节数据
            img_bytes = img_array.tobytes()
            bytes_per_line = w
            q_image = QImage(img_bytes, w, h, bytes_per_line,
                           QImage.Format.Format_Grayscale8)
        
        # 转换为QPixmap并缩放显示
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.preview_label.setPixmap(scaled_pixmap)
    
    def _on_mode_changed(self, index):
        """模式改变时"""
        self._update_preview()
    
    def _on_sensitivity_changed(self, value):
        """敏感度改变时"""
        self.sensitivity_value.setText(str(value))
        
        # 调整检测器参数
        # 敏感度越高，canny阈值越低
        self.detector.canny_low = max(10, 100 - value * 10)
        self.detector.canny_high = max(50, 200 - value * 15)
        
        self._update_preview()
    
    def _reset_settings(self):
        """重置所有设置"""
        self.mode_combo.setCurrentIndex(0)
        self.sensitivity_slider.setValue(5)
        self.preview_checkbox.setChecked(True)
        
        # 重置检测器参数
        self.detector.canny_low = 50
        self.detector.canny_high = 150
        
        self._update_preview()
    
    def _apply_crop(self):
        """应用裁剪"""
        try:
            mode = self._get_current_mode()
            self.result_image = self.detector.detect_and_remove_edges(
                self.original_image, mode
            )
            
            # 发送信号
            self.crop_completed.emit(self.result_image)
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            self.info_label.setText(f"⚠️ 应用失败: {str(e)}")


# ==================== 集成到主窗口的方法 ====================
"""
将以下代码添加到 MainWindowQt 类中：

1. 在 __init__ 方法中初始化检测器:
   self.edge_detector = SmartEdgeDetector()

2. 添加智能裁剪按钮（在现有裁剪按钮旁边）:
   smart_crop_btn = QPushButton("🎯 智能裁剪")
   smart_crop_btn.clicked.connect(self._open_smart_crop_dialog)
   # 添加到工具栏布局中

3. 添加对话框打开方法:
"""

def _open_smart_crop_dialog(self):
    """打开智能裁剪对话框（添加到MainWindowQt类中）"""
    if not self.current_image:
        QMessageBox.warning(self, "提示", "请先加载图片！")
        return
    
    # 创建对话框
    dialog = SmartCropDialog(self.current_image, self)
    
    # 连接完成信号
    dialog.crop_completed.connect(self._on_smart_crop_completed)
    
    # 显示对话框
    dialog.exec()

def _on_smart_crop_completed(self, result_image: Image.Image):
    """智能裁剪完成（添加到MainWindowQt类中）"""
    # 更新当前图像
    self.current_image = result_image
    
    # 清除旋转角度
    self.current_angle = 0
    
    # 更新显示
    self._update_preview()
    
    # 显示成功消息
    QMessageBox.information(self, "成功", "智能裁剪已完成！")


# ==================== 命令行工具版本 ====================
def cli_smart_crop():
    """命令行版本的智能裁剪工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能边缘线检测和移除工具")
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("-o", "--output", help="输出图片路径", default="output.png")
    parser.add_argument("-m", "--mode", 
                       choices=['auto', 'aggressive', 'conservative'],
                       default='auto',
                       help="检测模式")
    parser.add_argument("-p", "--preview", action="store_true",
                       help="生成预览图（显示检测框）")
    
    args = parser.parse_args()
    
    # 加载图片
    image = Image.open(args.input)
    
    # 创建检测器
    detector = SmartEdgeDetector()
    
    if args.preview:
        # 生成预览
        preview = detector.preview_detection(image)
        preview.save(args.output)
        print(f"✅ 预览图已保存到: {args.output}")
    else:
        # 处理图片
        result = detector.detect_and_remove_edges(image, args.mode)
        result.save(args.output)
        
        # 显示统计信息
        orig_size = image.size
        new_size = result.size
        saved_percent = (1 - (new_size[0] * new_size[1]) / (orig_size[0] * orig_size[1])) * 100
        
        print(f"✅ 处理完成！")
        print(f"   原始尺寸: {orig_size[0]}×{orig_size[1]}")
        print(f"   裁剪后: {new_size[0]}×{new_size[1]}")
        print(f"   节省空间: {saved_percent:.1f}%")
        print(f"   输出路径: {args.output}")


if __name__ == "__main__":
    cli_smart_crop()

"""
智能边缘线检测和删除模块
用于自动识别并移除图片中的多余边缘线
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List


class SmartEdgeDetector:
    """智能边缘线检测器"""
    
    def __init__(self):
        """初始化检测器参数"""
        # 边缘检测参数
        self.canny_low = 50
        self.canny_high = 150
        
        # 形态学参数
        self.morph_kernel_size = 5
        
        # 轮廓过滤参数
        self.min_area_ratio = 0.8  # 内容区域至少占总面积的80%
        self.edge_thickness_ratio = 0.05  # 边缘线厚度不超过图片宽/高的5%
    
    def detect_and_remove_edges(self, image: Image.Image, 
                                 mode: str = 'auto') -> Image.Image:
        """
        检测并移除图片边缘线
        
        Args:
            image: PIL图像对象
            mode: 检测模式
                - 'auto': 自动检测(推荐)
                - 'aggressive': 激进模式(移除更多)
                - 'conservative': 保守模式(移除更少)
        
        Returns:
            处理后的PIL图像
        """
        try:
            # 转换为OpenCV格式
            img_array = np.array(image)
            if len(img_array.shape) == 2:  # 灰度图
                gray = img_array
            else:  # 彩色图
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 根据模式调整参数
            if mode == 'aggressive':
                self.min_area_ratio = 0.7
                self.edge_thickness_ratio = 0.08
            elif mode == 'conservative':
                self.min_area_ratio = 0.9
                self.edge_thickness_ratio = 0.03
            
            # 检测边缘区域
            crop_box = self._detect_content_area(gray, img_array.shape)
            
            if crop_box is None:
                # 如果检测失败，返回原图
                return image
            
            # 裁剪图片
            x1, y1, x2, y2 = crop_box
            cropped = img_array[y1:y2, x1:x2]
            
            # 转换回PIL格式
            return Image.fromarray(cropped)
        except Exception as e:
            print(f"边缘检测失败: {e}")
            # 如果检测失败，返回原图
            return image
    
    def _detect_content_area(self, gray: np.ndarray, 
                            original_shape: Tuple) -> Optional[Tuple[int, int, int, int]]:
        """
        检测图片的实际内容区域
        
        Returns:
            (x1, y1, x2, y2) 内容区域坐标，如果检测失败返回None
        """
        h, w = gray.shape[:2]
        
        # === 方法1：边缘检测法 ===
        edges = cv2.Canny(gray, self.canny_low, self.canny_high)
        
        # 形态学闭运算，连接断裂的边缘
        kernel = np.ones((self.morph_kernel_size, self.morph_kernel_size), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # 找到最大的轮廓（假设为内容区域）
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w_cont, h_cont = cv2.boundingRect(largest_contour)
        
        # 检查是否为有效的内容区域
        content_area = w_cont * h_cont
        total_area = w * h
        
        if content_area / total_area < self.min_area_ratio:
            # 面积太小，尝试方法2
            return self._detect_by_border_analysis(gray)
        
        return (x, y, x + w_cont, y + h_cont)
    
    def _detect_by_border_analysis(self, gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        方法2：边界分析法
        从四个方向扫描，找到内容的边界
        """
        h, w = gray.shape
        
        # 计算每行/列的方差（内容区域方差大，边框区域方差小）
        row_var = np.var(gray, axis=1)
        col_var = np.var(gray, axis=0)
        
        # 设置阈值（自适应）
        row_threshold = np.percentile(row_var, 20)
        col_threshold = np.percentile(col_var, 20)
        
        # 从上往下扫描
        top = 0
        for i in range(h):
            if row_var[i] > row_threshold:
                top = i
                break
        
        # 从下往上扫描
        bottom = h - 1
        for i in range(h - 1, -1, -1):
            if row_var[i] > row_threshold:
                bottom = i
                break
        
        # 从左往右扫描
        left = 0
        for i in range(w):
            if col_var[i] > col_threshold:
                left = i
                break
        
        # 从右往左扫描
        right = w - 1
        for i in range(w - 1, -1, -1):
            if col_var[i] > col_threshold:
                right = i
                break
        
        # 检查边界是否有效
        max_edge_thickness = int(min(w, h) * self.edge_thickness_ratio)
        
        if (top >= max_edge_thickness or left >= max_edge_thickness or
            bottom <= h - max_edge_thickness or right <= w - max_edge_thickness):
            return None
        
        return (left, top, right + 1, bottom + 1)
    
    def preview_detection(self, image: Image.Image) -> Image.Image:
        """
        预览检测结果（在原图上绘制检测到的边界框）
        
        Returns:
            带有标记的预览图
        """
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        crop_box = self._detect_content_area(gray, img_array.shape)
        
        if crop_box is None:
            # 没有检测到，返回原图
            return image
        
        # 绘制检测框
        preview = img_array.copy()
        x1, y1, x2, y2 = crop_box
        
        # 绘制矩形框（绿色，粗线）
        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        # 绘制角点
        marker_size = 20
        cv2.line(preview, (x1, y1), (x1 + marker_size, y1), (255, 0, 0), 3)
        cv2.line(preview, (x1, y1), (x1, y1 + marker_size), (255, 0, 0), 3)
        
        cv2.line(preview, (x2, y1), (x2 - marker_size, y1), (255, 0, 0), 3)
        cv2.line(preview, (x2, y1), (x2, y1 + marker_size), (255, 0, 0), 3)
        
        cv2.line(preview, (x1, y2), (x1 + marker_size, y2), (255, 0, 0), 3)
        cv2.line(preview, (x1, y2), (x1, y2 - marker_size), (255, 0, 0), 3)
        
        cv2.line(preview, (x2, y2), (x2 - marker_size, y2), (255, 0, 0), 3)
        cv2.line(preview, (x2, y2), (x2, y2 - marker_size), (255, 0, 0), 3)
        
        return Image.fromarray(preview)
    
    def batch_process(self, images: List[Image.Image], 
                     mode: str = 'auto') -> List[Image.Image]:
        """
        批量处理多张图片
        
        Args:
            images: PIL图像列表
            mode: 检测模式
        
        Returns:
            处理后的图像列表
        """
        return [self.detect_and_remove_edges(img, mode) for img in images]


# ==================== 使用示例 ====================
def example_usage():
    """使用示例"""
    # 创建检测器
    detector = SmartEdgeDetector()
    
    # 加载图片
    image = Image.open("test_image.png")
    
    # === 方式1：直接处理 ===
    result = detector.detect_and_remove_edges(image, mode='auto')
    result.save("result_auto.png")
    
    # === 方式2：预览检测结果 ===
    preview = detector.preview_detection(image)
    preview.save("preview.png")
    
    # === 方式3：批量处理 ===
    images: List[Image.Image] = [Image.open(f"image_{i}.png") for i in range(5)]
    results = detector.batch_process(images, mode='aggressive')
    for i, result in enumerate(results):
        result.save(f"result_{i}.png")


if __name__ == "__main__":
    example_usage()

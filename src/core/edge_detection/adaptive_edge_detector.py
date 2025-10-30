"""
自适应边缘线检测和删除模块
根据图片特征自动调整检测参数
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List


class AdaptiveEdgeDetector:
    """自适应边缘线检测器"""
    
    def __init__(self):
        """初始化检测器参数"""
        # 基础参数
        self.base_canny_low = 50
        self.base_canny_high = 150
        self.base_morph_kernel_size = 5
        
        # 自适应参数
        self.adaptiveness = 0.8  # 自适应程度 (0-1)
        
        # 轮廓过滤参数
        self.min_area_ratio = 0.6  # 内容区域至少占总面积的60%
        self.max_area_ratio = 0.98  # 内容区域最多占总面积的98%
        self.edge_thickness_ratio = 0.1  # 边缘线厚度不超过图片宽/高的10%
        
        # 图片特征参数
        self.blur_threshold = 100  # 模糊度阈值
        self.texture_threshold = 50  # 纹理复杂度阈值
        self.contrast_threshold = 30  # 对比度阈值
    
    def detect_and_remove_edges(self, image: Image.Image, 
                                 mode: str = 'auto') -> Image.Image:
        """
        检测并移除图片边缘线（自适应版）
        
        Args:
            image: PIL图像对象
            mode: 检测模式
                - 'auto': 自动检测(推荐)
                - 'aggressive': 激进模式(移除更多)
                - 'conservative': 保守模式(移除更少)
                - 'adaptive': 自适应模式(根据图片特征调整参数)
        
        Returns:
            处理后的PIL图像
        """
        # 转换为OpenCV格式
        img_array = np.array(image)
        if len(img_array.shape) == 2:  # 灰度图
            gray = img_array
        else:  # 彩色图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # 根据模式调整参数
        if mode == 'aggressive':
            self.min_area_ratio = 0.5
            self.edge_thickness_ratio = 0.15
        elif mode == 'conservative':
            self.min_area_ratio = 0.75
            self.edge_thickness_ratio = 0.05
        elif mode == 'adaptive':
            # 自适应模式：根据图片特征调整参数
            self._adapt_parameters(gray)
        
        # 检测边缘区域
        crop_box = self._detect_content_area_adaptive(gray, img_array.shape)
        
        if crop_box is None:
            # 如果检测失败，返回原图
            return image
        
        # 裁剪图片
        x1, y1, x2, y2 = crop_box
        cropped = img_array[y1:y2, x1:x2]
        
        # 转换回PIL格式
        return Image.fromarray(cropped)
    
    def _adapt_parameters(self, gray: np.ndarray):
        """
        根据图片特征自适应调整参数
        
        Args:
            gray: 灰度图像
        """
        # 计算图片特征
        blur_score = self._calculate_blur_score(gray)
        texture_score = self._calculate_texture_score(gray)
        contrast_score = self._calculate_contrast_score(gray)
        
        # 根据特征调整参数
        # 模糊图片需要更敏感的边缘检测
        if blur_score < self.blur_threshold:
            self.base_canny_low = max(20, int(50 * (blur_score / self.blur_threshold)))
            self.base_canny_high = max(60, int(150 * (blur_score / self.blur_threshold)))
        
        # 纹理复杂的图片需要更大的形态学核
        if texture_score > self.texture_threshold:
            self.base_morph_kernel_size = min(9, int(5 + (texture_score / self.texture_threshold) * 2))
        
        # 对比度低的图片需要调整面积比例阈值
        if contrast_score < self.contrast_threshold:
            self.min_area_ratio = max(0.5, self.min_area_ratio * (contrast_score / self.contrast_threshold))
    
    def _calculate_blur_score(self, gray: np.ndarray) -> float:
        """
        计算图片模糊度得分
        
        Args:
            gray: 灰度图像
            
        Returns:
            模糊度得分 (越高越清晰)
        """
        # 使用拉普拉斯算子计算模糊度
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = laplacian.var()
        return blur_score
    
    def _calculate_texture_score(self, gray: np.ndarray) -> float:
        """
        计算图片纹理复杂度得分
        
        Args:
            gray: 灰度图像
            
        Returns:
            纹理复杂度得分
        """
        # 计算局部方差作为纹理复杂度
        kernel = np.ones((5, 5), np.float32) / 25
        smoothed = cv2.filter2D(gray, -1, kernel)
        texture = np.var(gray - smoothed)
        return texture
    
    def _calculate_contrast_score(self, gray: np.ndarray) -> float:
        """
        计算图片对比度得分
        
        Args:
            gray: 灰度图像
            
        Returns:
            对比度得分
        """
        # 计算直方图对比度
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        contrast_score = np.std(hist)
        return contrast_score
    
    def _detect_content_area_adaptive(self, gray: np.ndarray, 
                                     original_shape: Tuple) -> Optional[Tuple[int, int, int, int]]:
        """
        自适应内容区域检测
        
        Returns:
            (x1, y1, x2, y2) 内容区域坐标，如果检测失败返回None
        """
        h, w = gray.shape[:2]
        
        # 自适应边缘检测
        edges = self._adaptive_edge_detection(gray)
        
        # 自适应形态学处理
        kernel_size = max(3, min(9, self.base_morph_kernel_size))
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # 如果没有找到轮廓，使用边界分析法
            return self._detect_by_border_analysis_adaptive(gray)
        
        # 过滤轮廓
        filtered_contours = self._filter_contours_adaptive(contours, w, h)
        
        if not filtered_contours:
            # 如果没有合适的轮廓，使用边界分析法
            return self._detect_by_border_analysis_adaptive(gray)
        
        # 找到最可能的内容区域轮廓
        content_contour = self._find_content_contour_adaptive(filtered_contours, w, h)
        
        if content_contour is None:
            # 如果没有找到合适的内容轮廓，使用边界分析法
            return self._detect_by_border_analysis_adaptive(gray)
        
        x, y, w_cont, h_cont = cv2.boundingRect(content_contour)
        return (x, y, x + w_cont, y + h_cont)
    
    def _adaptive_edge_detection(self, gray: np.ndarray) -> np.ndarray:
        """
        自适应边缘检测
        
        Returns:
            边缘检测结果
        """
        # 根据图片特征调整Canny参数
        canny_low = self.base_canny_low
        canny_high = self.base_canny_high
        
        # Canny边缘检测
        canny_edges = cv2.Canny(gray, canny_low, canny_high)
        
        # Sobel边缘检测
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_edges = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_edges = np.uint8(sobel_edges > 50) * 255
        
        # 合并边缘检测结果
        combined_edges = np.zeros_like(canny_edges)
        combined_edges = np.logical_or(combined_edges, canny_edges).astype(np.uint8) * 255
        combined_edges = np.logical_or(combined_edges, sobel_edges).astype(np.uint8) * 255
        
        return combined_edges
    
    def _filter_contours_adaptive(self, contours: List, 
                                 width: int, height: int) -> List:
        """
        自适应轮廓过滤
        
        Args:
            contours: 轮廓列表
            width: 图片宽度
            height: 图片高度
            
        Returns:
            过滤后的轮廓列表
        """
        filtered = []
        total_area = width * height
        
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            area_ratio = area / total_area
            
            # 过滤面积过小或过大的轮廓
            if self.min_area_ratio <= area_ratio <= self.max_area_ratio:
                # 额外的自适应过滤条件
                if self._is_likely_content_area_adaptive(contour, width, height):
                    filtered.append(contour)
        
        return filtered
    
    def _is_likely_content_area_adaptive(self, contour: np.ndarray, 
                                        width: int, height: int) -> bool:
        """
        自适应判断轮廓是否可能是内容区域
        
        Args:
            contour: 轮廓
            width: 图片宽度
            height: 图片高度
            
        Returns:
            是否可能是内容区域
        """
        # 计算轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        
        # 计算长宽比
        aspect_ratio = max(w, h) / min(w, h)
        
        # 计算面积
        area = cv2.contourArea(contour)
        area_ratio = area / (width * height)
        
        # 内容区域通常具有合理的长宽比和面积
        if aspect_ratio > 8:  # 长宽比过大，可能是边缘线
            return False
        
        if area_ratio < 0.05:  # 面积过小，可能是噪点
            return False
        
        # 计算轮廓的复杂度（周长与面积的比值）
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            complexity = area / perimeter
            if complexity < 1:  # 复杂度过高，可能是边缘线
                return False
        
        return True
    
    def _find_content_contour_adaptive(self, contours: List, 
                                      width: int, height: int) -> Optional[np.ndarray]:
        """
        自适应内容轮廓查找
        
        Args:
            contours: 轮廓列表
            width: 图片宽度
            height: 图片高度
            
        Returns:
            最可能的内容区域轮廓，如果未找到返回None
        """
        if not contours:
            return None
        
        # 如果只有一个轮廓，直接返回
        if len(contours) == 1:
            return contours[0]
        
        # 计算图片中心
        center_x, center_y = width // 2, height // 2
        
        best_contour = None
        best_score = -1
        
        for contour in contours:
            # 计算轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 计算轮廓中心与图片中心的距离
            contour_center_x = x + w // 2
            contour_center_y = y + h // 2
            distance = np.sqrt((contour_center_x - center_x)**2 + (contour_center_y - center_y)**2)
            
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            
            # 计算长宽比得分
            aspect_ratio = max(w, h) / min(w, h)
            aspect_score = 1.0 if 0.3 <= aspect_ratio <= 3.0 else 0.5
            
            # 计算面积得分
            area_score = area / (width * height)
            
            # 计算位置得分（越居中得分越高）
            distance_score = 1 - (distance / np.sqrt((width/2)**2 + (height/2)**2))
            
            # 综合得分
            score = area_score * 0.5 + distance_score * 0.3 + aspect_score * 0.2
            
            if score > best_score:
                best_score = score
                best_contour = contour
        
        return best_contour
    
    def _detect_by_border_analysis_adaptive(self, gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        自适应边界分析法
        
        Args:
            gray: 灰度图像
            
        Returns:
            (left, top, right, bottom) 边界坐标，如果检测失败返回None
        """
        h, w = gray.shape
        
        # 使用梯度分析来检测边缘
        # 计算图像梯度
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 计算每行/列的梯度平均值
        row_grad = np.mean(gradient_magnitude, axis=1)
        col_grad = np.mean(gradient_magnitude, axis=0)
        
        # 设置阈值
        row_threshold = np.percentile(row_grad, 25)
        col_threshold = np.percentile(col_grad, 25)
        
        # 从上往下扫描
        top = 0
        for i in range(h):
            if row_grad[i] > row_threshold:
                top = i
                break
        
        # 从下往上扫描
        bottom = h - 1
        for i in range(h - 1, -1, -1):
            if row_grad[i] > row_threshold:
                bottom = i
                break
        
        # 从左往右扫描
        left = 0
        for i in range(w):
            if col_grad[i] > col_threshold:
                left = i
                break
        
        # 从右往左扫描
        right = w - 1
        for i in range(w - 1, -1, -1):
            if col_grad[i] > col_threshold:
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
        
        Args:
            image: PIL图像对象
            
        Returns:
            带有标记的预览图
        """
        img_array = np.array(image)
        if len(img_array.shape) == 2:  # 灰度图
            gray = img_array
        else:  # 彩色图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        crop_box = self._detect_content_area_adaptive(gray, img_array.shape)
        
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
    detector = AdaptiveEdgeDetector()
    
    # 加载图片
    image = Image.open("test_image.png")
    
    # === 方式1：标准处理 ===
    result = detector.detect_and_remove_edges(image, mode='auto')
    result.save("result_auto.png")
    
    # === 方式2：自适应处理 ===
    result_adaptive = detector.detect_and_remove_edges(image, mode='adaptive')
    result_adaptive.save("result_adaptive.png")
    
    # === 方式3：预览检测结果 ===
    preview = detector.preview_detection(image)
    preview.save("preview_adaptive.png")
    
    # === 方式4：批量处理 ===
    images = [Image.open(f"image_{i}.png") for i in range(5)]  # type: List[Image.Image]
    results = detector.batch_process(images, mode='adaptive')
    for i, result in enumerate(results):
        result.save(f"result_{i}_adaptive.png")


if __name__ == "__main__":
    example_usage()
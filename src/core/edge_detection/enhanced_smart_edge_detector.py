"""
增强版智能边缘线检测和删除模块
针对AI生成图片和复杂虚线优化的边缘检测算法
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List


class EnhancedSmartEdgeDetector:
    """增强版智能边缘线检测器"""
    
    def __init__(self):
        """初始化检测器参数"""
        # Canny边缘检测参数
        self.canny_low = 30
        self.canny_high = 100
        
        # Sobel边缘检测参数
        self.sobel_threshold = 50
        
        # Laplacian边缘检测参数
        self.laplacian_threshold = 20
        
        # 形态学参数
        self.morph_kernel_size = 3
        self.morph_iterations = 2
        
        # 轮廓过滤参数
        self.min_area_ratio = 0.6  # 内容区域至少占总面积的60%
        self.max_area_ratio = 0.98  # 内容区域最多占总面积的98%
        self.edge_thickness_ratio = 0.1  # 边缘线厚度不超过图片宽/高的10%
        
        # AI图片特殊处理参数
        self.ai_texture_threshold = 50  # AI纹理检测阈值
        self.ai_edge_sensitivity = 0.8  # AI边缘敏感度
        
        # 虚线处理参数
        self.dashed_line_kernel_size = 7  # 虚线连接核大小
        self.dashed_line_iterations = 3  # 虚线连接迭代次数
    
    def detect_and_remove_edges(self, image: Image.Image, 
                                 mode: str = 'auto') -> Image.Image:
        """
        检测并移除图片边缘线（增强版）
        
        Args:
            image: PIL图像对象
            mode: 检测模式
                - 'auto': 自动检测(推荐)
                - 'aggressive': 激进模式(移除更多)
                - 'conservative': 保守模式(移除更少)
                - 'ai_optimized': AI优化模式(针对AI生成图片)
                - 'dashed_lines': 虚线优化模式(针对复杂虚线)
        
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
        elif mode == 'ai_optimized':
            # AI优化模式参数
            self.min_area_ratio = 0.55
            self.edge_thickness_ratio = 0.12
            self.ai_edge_sensitivity = 0.9
        elif mode == 'dashed_lines':
            # 虚线优化模式参数
            self.dashed_line_kernel_size = 9
            self.dashed_line_iterations = 4
            self.morph_iterations = 3
        
        # 检测边缘区域
        crop_box = self._detect_content_area_enhanced(gray, img_array.shape, mode)
        
        if crop_box is None:
            # 如果检测失败，返回原图
            return image
        
        # 裁剪图片
        x1, y1, x2, y2 = crop_box
        cropped = img_array[y1:y2, x1:x2]
        
        # 转换回PIL格式
        return Image.fromarray(cropped)
    
    def _detect_content_area_enhanced(self, gray: np.ndarray, 
                                     original_shape: Tuple, 
                                     mode: str) -> Optional[Tuple[int, int, int, int]]:
        """
        增强版内容区域检测
        
        Returns:
            (x1, y1, x2, y2) 内容区域坐标，如果检测失败返回None
        """
        h, w = gray.shape[:2]
        
        # 方法1：多算法边缘检测
        edges = self._multi_algorithm_edge_detection(gray, mode)
        
        # 针对虚线的特殊处理
        if mode == 'dashed_lines':
            edges = self._enhance_dashed_lines(edges)
        
        # 形态学处理
        kernel = np.ones((self.morph_kernel_size, self.morph_kernel_size), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=self.morph_iterations)
        
        # 查找轮廓
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # 如果没有找到轮廓，使用边界分析法
            return self._detect_by_border_analysis_enhanced(gray, mode)
        
        # 过滤轮廓
        filtered_contours = self._filter_contours_enhanced(list(contours), w, h, mode)
        
        if not filtered_contours:
            # 如果没有合适的轮廓，使用边界分析法
            return self._detect_by_border_analysis_enhanced(gray, mode)
        
        # 找到最可能的内容区域轮廓
        content_contour = self._find_content_contour_enhanced(filtered_contours, w, h, mode)
        
        if content_contour is None:
            # 如果没有找到合适的内容轮廓，使用边界分析法
            return self._detect_by_border_analysis_enhanced(gray, mode)
        
        x, y, w_cont, h_cont = cv2.boundingRect(content_contour)
        return (x, y, x + w_cont, y + h_cont)
    
    def _multi_algorithm_edge_detection(self, gray: np.ndarray, mode: str) -> np.ndarray:
        """
        多算法边缘检测
        
        Returns:
            合并的边缘检测结果
        """
        # 高斯模糊减少噪声
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Canny边缘检测
        canny_edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
        
        # Sobel边缘检测
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        sobel_edges = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_edges = np.uint8(sobel_edges > self.sobel_threshold) * 255
        
        # Laplacian边缘检测
        laplacian_edges = cv2.Laplacian(blurred, cv2.CV_64F)
        laplacian_edges = np.uint8(np.abs(laplacian_edges) > self.laplacian_threshold) * 255
        
        # 合并边缘检测结果
        combined_edges = np.zeros_like(canny_edges)
        combined_edges = np.logical_or(combined_edges, canny_edges).astype(np.uint8) * 255
        combined_edges = np.logical_or(combined_edges, sobel_edges).astype(np.uint8) * 255
        combined_edges = np.logical_or(combined_edges, laplacian_edges).astype(np.uint8) * 255
        
        return combined_edges
    
    def _enhance_dashed_lines(self, edges: np.ndarray) -> np.ndarray:
        """
        增强虚线检测
        
        Args:
            edges: 原始边缘检测结果
            
        Returns:
            增强后的边缘检测结果
        """
        # 使用较大的结构元素连接虚线段
        kernel = np.ones((self.dashed_line_kernel_size, self.dashed_line_kernel_size), np.uint8)
        
        # 多次形态学闭运算连接虚线
        enhanced_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, 
                                        iterations=self.dashed_line_iterations)
        
        # 开运算去除噪声
        enhanced_edges = cv2.morphologyEx(enhanced_edges, cv2.MORPH_OPEN, kernel, 
                                        iterations=1)
        
        return enhanced_edges
    
    def _filter_contours_enhanced(self, contours: List, 
                        width: int, height: int, mode: str) -> List:
        """
        增强版轮廓过滤
        
        Args:
            contours: 轮廓列表
            width: 图片宽度
            height: 图片高度
            mode: 检测模式
            
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
                # 额外的AI图片过滤条件
                if mode == 'ai_optimized':
                    if self._is_likely_content_area_ai(contour, width, height):
                        filtered.append(contour)
                else:
                    filtered.append(contour)
        
        return filtered
    
    def _is_likely_content_area_ai(self, contour: np.ndarray, 
                                 width: int, height: int) -> bool:
        """
        判断轮廓是否可能是AI图片的内容区域
        
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
        
        # AI生成的图片内容区域通常具有合理的长宽比和面积
        # 这里是一些启发式规则
        if aspect_ratio > 5:  # 长宽比过大，可能是边缘线
            return False
        
        if area_ratio < 0.1:  # 面积过小，可能是噪点
            return False
        
        # 计算轮廓的复杂度（周长与面积的比值）
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            complexity = area / perimeter
            if complexity < 2:  # 复杂度过高，可能是边缘线
                return False
        
        return True
    
    def _find_content_contour_enhanced(self, contours: List[np.ndarray], 
                             width: int, height: int, 
                             mode: str) -> Optional[np.ndarray]:
        """
        增强版内容轮廓查找
        
        Args:
            contours: 轮廓列表
            width: 图片宽度
            height: 图片高度
            mode: 检测模式
            
        Returns:
            最可能的内容区域轮廓，如果未找到返回None
        """
        if not contours:
            return None
        
        # 如果只有一个轮廓，直接返回
        if len(contours) == 1:
            return contours[0]
        
        # 根据模式选择不同的策略
        if mode == 'ai_optimized':
            # AI优化模式：选择面积适中且位置居中的轮廓
            return self._find_ai_content_contour(contours, width, height)
        else:
            # 默认模式：选择面积最大的轮廓
            return max(contours, key=cv2.contourArea)
    
    def _find_ai_content_contour(self, contours: List[np.ndarray], 
                                width: int, height: int) -> Optional[np.ndarray]:
        """
        AI优化模式下的内容轮廓查找
        
        Args:
            contours: 轮廓列表
            width: 图片宽度
            height: 图片高度
            
        Returns:
            最可能的内容区域轮廓，如果未找到返回None
        """
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
            
            # 计算得分（面积越大得分越高，距离中心越近得分越高）
            area_score = area / (width * height)
            distance_score = 1 - (distance / np.sqrt((width/2)**2 + (height/2)**2))
            score = area_score * 0.7 + distance_score * 0.3
            
            if score > best_score:
                best_score = score
                best_contour = contour
        
        return best_contour
    
    def _detect_by_border_analysis_enhanced(self, gray: np.ndarray, 
                                           mode: str) -> Optional[Tuple[int, int, int, int]]:
        """
        增强版边界分析法
        
        Args:
            gray: 灰度图像
            mode: 检测模式
            
        Returns:
            (left, top, right, bottom) 边界坐标，如果检测失败返回None
        """
        h, w = gray.shape
        
        # AI优化模式使用特殊的边界分析
        if mode == 'ai_optimized':
            return self._detect_by_border_analysis_ai(gray)
        
        # 标准边界分析
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
    
    def _detect_by_border_analysis_ai(self, gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        AI优化模式的边界分析法
        
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
        row_threshold = np.percentile(row_grad, 30) * self.ai_edge_sensitivity
        col_threshold = np.percentile(col_grad, 30) * self.ai_edge_sensitivity
        
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
    
    def preview_detection(self, image: Image.Image, mode: str = 'auto') -> Image.Image:
        """
        预览检测结果（在原图上绘制检测到的边界框）
        
        Args:
            image: PIL图像对象
            mode: 检测模式
            
        Returns:
            带有标记的预览图
        """
        img_array = np.array(image)
        if len(img_array.shape) == 2:  # 灰度图
            gray = img_array
        else:  # 彩色图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        crop_box = self._detect_content_area_enhanced(gray, img_array.shape, mode)
        
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
    detector = EnhancedSmartEdgeDetector()
    
    # 加载图片
    image = Image.open("test_image.png")
    
    # === 方式1：标准处理 ===
    result = detector.detect_and_remove_edges(image, mode='auto')
    result.save("result_auto.png")
    
    # === 方式2：AI优化处理 ===
    result_ai = detector.detect_and_remove_edges(image, mode='ai_optimized')
    result_ai.save("result_ai.png")
    
    # === 方式3：虚线优化处理 ===
    result_dashed = detector.detect_and_remove_edges(image, mode='dashed_lines')
    result_dashed.save("result_dashed.png")
    
    # === 方式4：预览检测结果 ===
    preview = detector.preview_detection(image, mode='ai_optimized')
    preview.save("preview_ai.png")
    
    # === 方式5：批量处理 ===
    images = [Image.open(f"image_{i}.png") for i in range(5)]  # type: List[Image.Image]
    results = detector.batch_process(images, mode='ai_optimized')
    for i, result in enumerate(results):
        result.save(f"result_{i}_ai.png")


if __name__ == "__main__":
    example_usage()
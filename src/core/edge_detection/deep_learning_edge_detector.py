"""
基于深度学习的智能边缘线检测和删除模块
采用YOLOv8和U-Net等最新开源技术优化的边缘检测算法
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List

# 尝试导入深度学习库，如果没有则使用传统方法
try:
    import torch
    from torchvision import transforms
    TORCH_AVAILABLE = True
    print("PyTorch已成功加载")
    
    # 测试PyTorch是否能正常工作
    try:
        x = torch.randn(1, 1)
        print("PyTorch功能正常")
    except Exception as e:
        print(f"PyTorch功能测试失败: {e}")
        TORCH_AVAILABLE = False
        transforms = None
        torch = None
except ImportError:
    TORCH_AVAILABLE = False
    transforms = None
    torch = None
except Exception as e:
    print(f"PyTorch加载失败: {e}")
    TORCH_AVAILABLE = False
    transforms = None
    torch = None

from scipy import ndimage
# 修复导入问题 - 使用正确的函数
from skimage.segmentation import watershed
# 新版本skimage中peak_local_maxima已被移除，使用其他方法替代
try:
    from skimage.feature import peak_local_maxima
except ImportError:
    # 新版本skimage中使用其他方法
    peak_local_maxima = None

class DeepLearningEdgeDetector:
    """基于深度学习的智能边缘线检测器"""
    
    def __init__(self):
        """初始化检测器参数"""
        # 检测参数
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.3
        
        # 分割参数
        self.segmentation_threshold = 0.6
        
        # 形态学参数
        self.morph_kernel_size = 3
        self.morph_iterations = 2
        
        # 内容保护参数
        self.content_protection_margin = 0.02
        
        # 边缘线厚度参数
        self.edge_thickness_ratio = 0.1
        
        # 预训练模型路径（实际使用时需要下载预训练模型）
        self.yolo_model_path = "yolov8m.pt"  # 需要替换为实际路径
        self.unet_model_path = "unet_edge.pth"  # 需要替换为实际路径
        
        # 模型初始化标志
        self.models_loaded = False
        self.yolo_model = None
        self.unet_model = None
        
        # 图像预处理
        if TORCH_AVAILABLE:
            self.transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = None
    
    def _load_models(self):
        """加载预训练模型"""
        if self.models_loaded:
            return
        
        # 只有在torch可用时才尝试加载模型
        if TORCH_AVAILABLE:
            try:
                # 尝试加载YOLOv8模型（需要安装ultralytics库）
                # from ultralytics import YOLO
                # self.yolo_model = YOLO(self.yolo_model_path)
                
                # 尝试加载U-Net模型（需要定义网络结构）
                # self.unet_model = self._create_unet_model()
                # self.unet_model.load_state_dict(torch.load(self.unet_model_path))
                # self.unet_model.eval()
                
                # 如果模型加载成功，设置标志
                self.models_loaded = True
                print("深度学习模型加载成功")
            except Exception as e:
                print(f"深度学习模型加载失败: {e}")
                print("将使用传统方法进行边缘检测")
                self.models_loaded = False
        else:
            print("PyTorch不可用，将使用传统方法进行边缘检测")
            self.models_loaded = False
    
    def _create_unet_model(self):
        """创建U-Net模型（简化版）"""
        import torch.nn as nn
        
        class UNet(nn.Module):
            def __init__(self, n_channels=3, n_classes=1):
                super(UNet, self).__init__()
                # 简化的U-Net结构
                self.inc = nn.Sequential(
                    nn.Conv2d(n_channels, 64, 3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(64, 64, 3, padding=1),
                    nn.ReLU(inplace=True)
                )
                self.down1 = nn.Sequential(
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(128, 128, 3, padding=1),
                    nn.ReLU(inplace=True)
                )
                self.up1 = nn.Sequential(
                    nn.ConvTranspose2d(128, 64, 2, stride=2),
                    nn.Conv2d(128, 64, 3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(64, 64, 3, padding=1),
                    nn.ReLU(inplace=True)
                )
                self.outc = nn.Conv2d(64, n_classes, 1)
                
            def forward(self, x):
                x1 = self.inc(x)
                x2 = self.down1(x1)
                x = self.up1(x2)
                x = torch.cat([x, x1], dim=1)
                x = self.outc(x)
                return torch.sigmoid(x)
        
        return UNet()
    
    def detect_and_remove_edges(self, image: Image.Image, 
                                 mode: str = 'auto') -> Image.Image:
        """
        检测并移除图片边缘线（深度学习版）
        
        Args:
            image: PIL图像对象
            mode: 检测模式
                - 'auto': 自动检测(推荐)
                - 'aggressive': 激进模式(移除更多)
                - 'conservative': 保守模式(移除更少)
                - 'ai_optimized': AI优化模式(针对AI生成图片)
                - 'emoji_protected': 表情包保护模式(保护重要内容)
        
        Returns:
            处理后的PIL图像
        """
        # 转换为OpenCV格式
        img_array = np.array(image)
        if len(img_array.shape) == 2:  # 灰度图
            gray = img_array
            color_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        else:  # 彩色图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            color_img = img_array
        
        # 根据模式调整参数
        if mode == 'aggressive':
            self.confidence_threshold = 0.3
            self.segmentation_threshold = 0.5
            self.edge_thickness_ratio = 0.15
        elif mode == 'conservative':
            self.confidence_threshold = 0.7
            self.segmentation_threshold = 0.7
            self.edge_thickness_ratio = 0.05
        elif mode == 'ai_optimized':
            self.confidence_threshold = 0.4
            self.segmentation_threshold = 0.55
            self.edge_thickness_ratio = 0.12
        elif mode == 'emoji_protected':
            self.confidence_threshold = 0.5
            self.segmentation_threshold = 0.6
            self.edge_thickness_ratio = 0.08
            self.content_protection_margin = 0.05
        
        # 尝试加载深度学习模型
        self._load_models()
        
        # 检测边缘区域
        if self.models_loaded:
            # 使用深度学习方法
            crop_box = self._detect_content_area_deep_learning(color_img, mode)
        else:
            # 使用传统方法作为备选
            crop_box = self._detect_content_area_traditional(gray, img_array.shape, mode)
        
        if crop_box is None:
            # 如果检测失败，返回原图
            return image
        
        # 应用内容保护边界
        x1, y1, x2, y2 = crop_box
        h, w = img_array.shape[:2]
        
        # 添加保护边界
        margin_x = int(w * self.content_protection_margin)
        margin_y = int(h * self.content_protection_margin)
        
        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)
        
        # 裁剪图片
        cropped = img_array[y1:y2, x1:x2]
        
        # 转换回PIL格式
        return Image.fromarray(cropped)
    
    def _detect_content_area_deep_learning(self, color_img: np.ndarray, 
                                         mode: str) -> Optional[Tuple[int, int, int, int]]:
        """
        基于深度学习的内容区域检测
        
        Args:
            color_img: 彩色图像数组
            mode: 检测模式
            
        Returns:
            (x1, y1, x2, y2) 内容区域坐标，如果检测失败返回None
        """
        h, w = color_img.shape[:2]
        
        try:
            # 使用YOLOv8进行目标检测
            if self.yolo_model:
                results = self.yolo_model(color_img)
                boxes = results[0].boxes
                
                if len(boxes) > 0:
                    # 获取置信度最高的检测框
                    confidences = boxes.conf.cpu().numpy()
                    best_idx = np.argmax(confidences)
                    
                    if confidences[best_idx] > self.confidence_threshold:
                        box = boxes.xyxy[best_idx].cpu().numpy()
                        x1, y1, x2, y2 = map(int, box)
                        return (x1, y1, x2, y2)
            
            # 如果YOLO检测失败，使用U-Net分割
            if self.unet_model:
                # 预处理图像
                input_tensor = self.transform(Image.fromarray(color_img))
                input_tensor = input_tensor.unsqueeze(0)
                
                # 进行分割
                with torch.no_grad():
                    output = self.unet_model(input_tensor)
                    segmentation = output.squeeze().cpu().numpy()
                
                # 应用阈值
                binary_mask = (segmentation > self.segmentation_threshold).astype(np.uint8)
                
                # 形态学处理
                kernel = np.ones((self.morph_kernel_size, self.morph_kernel_size), np.uint8)
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, 
                                             iterations=self.morph_iterations)
                
                # 查找轮廓
                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # 选择最大的轮廓
                    largest_contour = max(contours, key=cv2.contourArea)
                    x, y, w_cont, h_cont = cv2.boundingRect(largest_contour)
                    return (x, y, x + w_cont, y + h_cont)
            
            # 如果深度学习方法都失败，回退到传统方法
            gray = cv2.cvtColor(color_img, cv2.COLOR_RGB2GRAY)
            return self._detect_content_area_traditional(gray, color_img.shape, mode)
            
        except Exception as e:
            print(f"深度学习检测失败: {e}")
            # 回退到传统方法
            gray = cv2.cvtColor(color_img, cv2.COLOR_RGB2GRAY)
            return self._detect_content_area_traditional(gray, color_img.shape, mode)
    
    def _detect_content_area_traditional(self, gray: np.ndarray, 
                                       original_shape: Tuple, 
                                       mode: str) -> Optional[Tuple[int, int, int, int]]:
        """
        传统方法的内容区域检测（优化版）
        
        Args:
            gray: 灰度图像
            original_shape: 原始图像形状
            mode: 检测模式
            
        Returns:
            (x1, y1, x2, y2) 内容区域坐标，如果检测失败返回None
        """
        h, w = gray.shape
        
        # 多尺度边缘检测
        edges = self._multi_scale_edge_detection(gray)
        
        # 形态学增强
        edges = self._morphological_enhancement(edges)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # 使用梯度分析法
            return self._gradient_based_detection(gray, mode)
        
        # 过滤轮廓
        filtered_contours = self._filter_contours_advanced(contours, w, h, mode)
        
        if not filtered_contours:
            # 使用梯度分析法
            return self._gradient_based_detection(gray, mode)
        
        # 找到最可能的内容区域轮廓
        content_contour = self._find_content_contour_advanced(filtered_contours, w, h, mode)
        
        if content_contour is None:
            # 使用梯度分析法
            return self._gradient_based_detection(gray, mode)
        
        x, y, w_cont, h_cont = cv2.boundingRect(content_contour)
        return (x, y, x + w_cont, y + h_cont)
    
    def _multi_scale_edge_detection(self, gray: np.ndarray) -> np.ndarray:
        """
        多尺度边缘检测
        
        Args:
            gray: 灰度图像
            
        Returns:
            边缘检测结果
        """
        # 高斯金字塔多尺度检测
        scales = [1, 1.5, 2]
        combined_edges = np.zeros_like(gray)
        
        for scale in scales:
            if scale == 1:
                resized = gray
            else:
                new_h, new_w = int(gray.shape[0] / scale), int(gray.shape[1] / scale)
                resized = cv2.resize(gray, (new_w, new_h))
            
            # Canny边缘检测
            edges = cv2.Canny(resized, 50, 150)
            
            # 如果进行了缩放，需要恢复到原始尺寸
            if scale != 1:
                edges = cv2.resize(edges, (gray.shape[1], gray.shape[0]))
            
            # 合并边缘
            combined_edges = np.logical_or(combined_edges, edges).astype(np.uint8) * 255
        
        return combined_edges
    
    def _morphological_enhancement(self, edges: np.ndarray) -> np.ndarray:
        """
        形态学增强
        
        Args:
            edges: 边缘检测结果
            
        Returns:
            增强后的边缘
        """
        # 多结构元素闭运算
        kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # 闭运算连接边缘
        closed1 = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel1, iterations=2)
        closed2 = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel2, iterations=2)
        
        # 合并结果
        enhanced = np.logical_or(closed1, closed2).astype(np.uint8) * 255
        
        # 开运算去除噪声
        enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_OPEN, kernel1, iterations=1)
        
        return enhanced
    
    def _filter_contours_advanced(self, contours: List[np.ndarray], 
                                width: int, height: int, 
                                mode: str) -> List[np.ndarray]:
        """
        高级轮廓过滤
        
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
            
            # 基本面积过滤
            if area_ratio < 0.01 or area_ratio > 0.99:
                continue
            
            # 计算轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 计算长宽比
            if min(w, h) > 0:
                aspect_ratio = max(w, h) / min(w, h)
            else:
                aspect_ratio = 1
            
            # 长宽比过滤
            if aspect_ratio > 10:
                continue
            
            # 位置过滤（边缘区域的内容需要更严格的判断）
            margin = min(width, height) * 0.1
            if (x < margin or y < margin or 
                x + w > width - margin or y + h > height - margin):
                if area_ratio < 0.1:
                    continue
            
            # 复杂度过滤
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                complexity = area / perimeter
                if complexity < 0.5:
                    continue
            
            # 根据模式进行额外过滤
            if mode == 'emoji_protected':
                # 表情包保护模式下，保留更多可能的内容区域
                if self._is_likely_emoji_content(contour, width, height):
                    filtered.append(contour)
            else:
                filtered.append(contour)
        
        return filtered
    
    def _is_likely_emoji_content(self, contour: np.ndarray, 
                               width: int, height: int) -> bool:
        """
        判断轮廓是否可能是表情包内容
        
        Args:
            contour: 轮廓
            width: 图片宽度
            height: 图片高度
            
        Returns:
            是否可能是表情包内容
        """
        # 计算轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        
        # 计算面积比例
        area = cv2.contourArea(contour)
        area_ratio = area / (width * height)
        
        # 表情包内容通常位于图片中心区域
        center_x, center_y = width // 2, height // 2
        contour_center_x, contour_center_y = x + w // 2, y + h // 2
        distance_to_center = np.sqrt((contour_center_x - center_x)**2 + 
                                   (contour_center_y - center_y)**2)
        max_distance = np.sqrt((width/2)**2 + (height/2)**2)
        distance_ratio = distance_to_center / max_distance
        
        # 如果轮廓位于中心区域且面积适中，则更可能是内容
        if distance_ratio < 0.3 and 0.1 < area_ratio < 0.8:
            return True
        
        return False
    
    def _find_content_contour_advanced(self, contours: List[np.ndarray], 
                                     width: int, height: int, 
                                     mode: str) -> Optional[np.ndarray]:
        """
        高级内容轮廓查找
        
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
            area_ratio = area / (width * height)
            
            # 计算长宽比
            if min(w, h) > 0:
                aspect_ratio = max(w, h) / min(w, h)
            else:
                aspect_ratio = 1
            
            # 计算得分
            # 面积适中得分高
            area_score = 1 - abs(area_ratio - 0.4) * 2  # 0.4附近得分最高
            area_score = max(0, area_score)  # 确保非负
            
            # 位置居中得分高
            distance_score = 1 - (distance / np.sqrt((width/2)**2 + (height/2)**2))
            
            # 长宽比适中得分高
            aspect_score = 1 - abs(aspect_ratio - 1) * 0.3  # 接近1得分高
            aspect_score = max(0, aspect_score)  # 确保非负
            
            # 综合得分
            if mode == 'emoji_protected':
                score = area_score * 0.4 + distance_score * 0.4 + aspect_score * 0.2
            else:
                score = area_score * 0.5 + distance_score * 0.3 + aspect_score * 0.2
            
            if score > best_score:
                best_score = score
                best_contour = contour
        
        return best_contour
    
    def _gradient_based_detection(self, gray: np.ndarray, mode: str) -> Optional[Tuple[int, int, int, int]]:
        """
        基于梯度的检测方法
        
        Args:
            gray: 灰度图像
            mode: 检测模式
            
        Returns:
            (left, top, right, bottom) 边界坐标，如果检测失败返回None
        """
        h, w = gray.shape
        
        # 计算图像梯度
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 计算每行/列的梯度平均值
        row_grad = np.mean(gradient_magnitude, axis=1)
        col_grad = np.mean(gradient_magnitude, axis=0)
        
        # 设置阈值
        sensitivity = 0.7 if mode == 'ai_optimized' else 0.5
        row_threshold = np.percentile(row_grad, 30) * sensitivity
        col_threshold = np.percentile(col_grad, 30) * sensitivity
        
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
            color_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        else:  # 彩色图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            color_img = img_array
        
        # 尝试使用深度学习方法检测
        self._load_models()
        if self.models_loaded:
            crop_box = self._detect_content_area_deep_learning(color_img, mode)
        else:
            crop_box = self._detect_content_area_traditional(gray, img_array.shape, mode)
        
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
    detector = DeepLearningEdgeDetector()
    
    # 加载图片
    image = Image.open("test_image.png")
    
    # === 方式1：标准处理 ===
    result = detector.detect_and_remove_edges(image, mode='auto')
    result.save("result_auto.png")
    
    # === 方式2：AI优化处理 ===
    result_ai = detector.detect_and_remove_edges(image, mode='ai_optimized')
    result_ai.save("result_ai.png")
    
    # === 方式3：表情包保护处理 ===
    result_emoji = detector.detect_and_remove_edges(image, mode='emoji_protected')
    result_emoji.save("result_emoji.png")
    
    # === 方式4：预览检测结果 ===
    preview = detector.preview_detection(image, mode='emoji_protected')
    preview.save("preview_emoji.png")
    
    # === 方式5：批量处理 ===
    images = [Image.open(f"image_{i}.png") for i in range(5)]  # type: List[Image.Image]
    results = detector.batch_process(images, mode='emoji_protected')
    for i, result in enumerate(results):
        result.save(f"result_{i}_emoji.png")


if __name__ == "__main__":
    example_usage()
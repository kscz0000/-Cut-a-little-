"""
图像处理核心模块
提供图片旋转、分割、预览生成等功能
"""
from PIL import Image, ImageTk
from typing import List, Tuple, Optional
import math
import os


class ImageProcessor:
    """图像处理器"""
    
    @staticmethod
    def load_image(file_path: str) -> Optional[Image.Image]:
        """
        加载图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"图片文件不存在: {file_path}")
                return None
            
            # 检查文件是否为支持的图片格式
            supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif')
            if not file_path.lower().endswith(supported_formats):
                print(f"不支持的图片格式: {file_path}")
                return None
                
            image = Image.open(file_path)
            
            # 验证图片是否有效
            image.verify()
            
            # 重新打开图片（verify会关闭文件）
            image = Image.open(file_path)
            
            return image
        except Exception as e:
            print(f"加载图片失败: {file_path}, 错误: {e}")
            return None
    
    @staticmethod
    def rotate_image(image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
        """
        旋转图片
        
        Args:
            image: 原始图片
            angle: 旋转角度（度）
            expand: 是否扩展画布以容纳旋转后的图片
            
        Returns:
            旋转后的图片
        """
        try:
            # 确保角度在合理范围内
            angle = angle % 360
            
            # 如果角度为0，直接返回原图副本
            if angle == 0:
                return image.copy()
            
            # 使用高质量重采样旋转
            return image.rotate(-angle, expand=expand, resample=Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"旋转图片失败: {e}")
            # 如果旋转失败，返回原图副本
            return image.copy()
    
    @staticmethod
    def create_thumbnail(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """
        创建缩略图
        
        Args:
            image: 原始图片
            max_size: 最大尺寸 (宽, 高)
            
        Returns:
            缩略图
        """
        # 复制图片以避免修改原图
        thumb = image.copy()
        thumb.thumbnail(max_size, Image.Resampling.LANCZOS)
        return thumb
    
    @staticmethod
    def generate_split_lines(rows: int, cols: int, width: int, height: int) -> Tuple[List[int], List[int]]:
        """
        生成均匀分割线坐标
        
        Args:
            rows: 行数
            cols: 列数
            width: 图片宽度
            height: 图片高度
            
        Returns:
            (横向分割线Y坐标列表, 纵向分割线X坐标列表)
        """
        # 横向分割线（水平线）
        h_lines = []
        if rows > 1:
            step_y = height / rows
            h_lines = [int(step_y * i) for i in range(1, rows)]
        
        # 纵向分割线（垂直线）
        v_lines = []
        if cols > 1:
            step_x = width / cols
            v_lines = [int(step_x * i) for i in range(1, cols)]
        
        return h_lines, v_lines
    
    @staticmethod
    def crop_by_lines(image: Image.Image, rows: int, cols: int, 
                      h_lines: Optional[List[int]] = None, 
                      v_lines: Optional[List[int]] = None) -> List[Image.Image]:
        """
        根据分割线坐标裁剪图片
        
        Args:
            image: 原始图片
            rows: 行数
            cols: 列数
            h_lines: 横向分割线Y坐标列表（可选，None则均匀分割）
            v_lines: 纵向分割线X坐标列表（可选，None则均匀分割）
            
        Returns:
            裁剪后的图片列表
        """
        width, height = image.size
        
        # 如果没有指定分割线，生成均匀分割线
        if h_lines is None or v_lines is None:
            h_lines, v_lines = ImageProcessor.generate_split_lines(rows, cols, width, height)
        
        # 构建所有Y坐标（包括顶部和底部）
        y_coords = [0] + h_lines + [height]
        
        # 构建所有X坐标（包括左边和右边）
        x_coords = [0] + v_lines + [width]
        
        # 裁剪图片
        cropped_images = []
        for i in range(rows):
            for j in range(cols):
                box = (x_coords[j], y_coords[i], x_coords[j+1], y_coords[i+1])
                cropped = image.crop(box)
                cropped_images.append(cropped)
        
        return cropped_images
    
    @staticmethod
    def detect_grid_type(width: int, height: int) -> str:
        """
        自动检测宫格类型
        
        Args:
            width: 图片宽度
            height: 图片高度
            
        Returns:
            宫格类型: "4grid" 或 "9grid"
        """
        ratio = width / height if height > 0 else 1
        
        # 正方形或接近正方形 -> 九宫格
        if 0.9 <= ratio <= 1.1 and min(width, height) >= 300:
            return "9grid"
        
        # 横向矩形或纵向矩形 -> 四宫格
        elif (1.8 <= ratio <= 2.2) or (0.45 <= ratio <= 0.55):
            return "4grid"
        
        # 默认四宫格
        return "4grid"
    
    @staticmethod
    def calculate_thumbnail_grid_size(total_count: int, max_width: int, max_height: int, 
                                      min_thumb_size: int = 50) -> Tuple[int, int]:
        """
        计算缩略图网格的单个缩略图尺寸
        
        Args:
            total_count: 总缩略图数量
            max_width: 可用最大宽度
            max_height: 可用最大高度
            min_thumb_size: 最小缩略图尺寸
            
        Returns:
            (缩略图宽度, 缩略图高度)
        """
        # 计算网格布局
        cols = math.ceil(math.sqrt(total_count))
        rows = math.ceil(total_count / cols)
        
        # 计算单个缩略图尺寸
        thumb_width = max_width // cols
        thumb_height = max_height // rows
        
        # 确保不小于最小尺寸
        thumb_width = max(thumb_width, min_thumb_size)
        thumb_height = max(thumb_height, min_thumb_size)
        
        return thumb_width, thumb_height
    
    @staticmethod
    def pil_to_tkimage(pil_image: Image.Image) -> ImageTk.PhotoImage:
        """
        将PIL图像转换为Tkinter图像
        
        Args:
            pil_image: PIL图像对象
            
        Returns:
            Tkinter PhotoImage对象
        """
        return ImageTk.PhotoImage(pil_image)
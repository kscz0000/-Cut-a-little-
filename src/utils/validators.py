"""
参数验证工具模块
提供各种参数校验功能
"""
from typing import Tuple, Optional


class Validators:
    """参数验证器"""
    
    @staticmethod
    def validate_grid_size(rows: int, cols: int) -> Tuple[bool, Optional[str]]:
        """
        验证行列数是否合法
        
        Args:
            rows: 行数
            cols: 列数
            
        Returns:
            (是否合法, 错误信息)
        """
        # 检查范围
        if not (1 <= rows <= 18):
            return False, f"行数必须在 1-18 之间，当前值: {rows}"
        
        if not (1 <= cols <= 18):
            return False, f"列数必须在 1-18 之间，当前值: {cols}"
        
        # 检查是否同时为1
        if rows == 1 and cols == 1:
            return False, "行列数不能同时为 1，至少为 2×1 或 1×2"
        
        return True, None
    
    @staticmethod
    def validate_file_count(count: int, max_count: int = 10) -> Tuple[bool, Optional[str]]:
        """
        验证文件数量是否合法
        
        Args:
            count: 文件数量
            max_count: 最大允许数量
            
        Returns:
            (是否合法, 错误信息)
        """
        if count < 1:
            return False, "至少需要添加 1 个文件"
        
        if count > max_count:
            return False, f"已达文件数量上限（{max_count}个），无法继续添加"
        
        return True, None
    
    @staticmethod
    def validate_image_size(width: int, height: int, min_size: int = 100) -> Tuple[bool, Optional[str]]:
        """
        验证图片尺寸是否合适
        
        Args:
            width: 图片宽度
            height: 图片高度
            min_size: 最小尺寸
            
        Returns:
            (是否合法, 警告信息)
        """
        if width < min_size or height < min_size:
            return False, f"图片尺寸过小（{width}x{height}px），分割后效果可能不佳"
        
        return True, None
    
    @staticmethod
    def validate_rotation_angle(angle: float) -> Tuple[bool, Optional[str]]:
        """
        验证旋转角度是否合法
        
        Args:
            angle: 旋转角度
            
        Returns:
            (是否合法, 错误信息)
        """
        # Tkinter 支持任意角度，无需限制
        return True, None
    
    @staticmethod
    def validate_file_format(file_path: str, supported_formats: Optional[list] = None) -> Tuple[bool, Optional[str]]:
        """
        验证文件格式是否支持
        
        Args:
            file_path: 文件路径
            supported_formats: 支持的格式列表
            
        Returns:
            (是否合法, 错误信息)
        """
        if supported_formats is None:
            supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'webp']
        
        ext = file_path.split('.')[-1].lower()
        
        if ext not in supported_formats:
            return False, f"不支持的文件格式: .{ext}，请选择 {'/'.join(supported_formats).upper()} 文件"
        
        return True, None

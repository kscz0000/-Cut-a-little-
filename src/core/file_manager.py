"""
文件管理模块
负责文件保存、命名、文件夹管理等操作
"""
import os
from typing import List, Tuple
from PIL import Image
import shutil


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def create_output_folder(base_path: str, folder_name: str) -> Tuple[bool, str]:
        """
        创建输出文件夹
        
        Args:
            base_path: 基础路径
            folder_name: 文件夹名称
            
        Returns:
            (是否成功, 文件夹完整路径或错误信息)
        """
        try:
            output_path = os.path.join(base_path, folder_name)
            os.makedirs(output_path, exist_ok=True)
            return True, output_path
        except Exception as e:
            return False, f"无法创建输出文件夹: {str(e)}"
    
    @staticmethod
    def generate_filename(index: int, original_name: str, extension: str) -> str:
        """
        生成输出文件名（序号前缀格式）
        
        Args:
            index: 序号（从1开始）
            original_name: 原文件名（不含扩展名）
            extension: 文件扩展名（如 'png' 或 'jpg'）
            
        Returns:
            格式化的文件名，如 "001_emoji.png"
        """
        # 三位数序号
        seq = str(index).zfill(3)
        return f"{seq}_{original_name}.{extension.lower()}"
    
    @staticmethod
    def save_split_images(images: List[Image.Image], output_folder: str, 
                         original_filename: str, output_format: str = "PNG") -> Tuple[int, List[str]]:
        """
        保存分割后的图片
        
        Args:
            images: 分割后的图片列表
            output_folder: 输出文件夹路径
            original_filename: 原文件名（含扩展名）
            output_format: 输出格式 "PNG" 或 "JPG"
            
        Returns:
            (成功保存数量, 失败文件列表)
        """
        success_count = 0
        failed_files = []
        
        # 获取原文件名（不含扩展名）
        base_name = os.path.splitext(original_filename)[0]
        ext = "png" if output_format == "PNG" else "jpg"
        
        for i, image in enumerate(images, start=1):
            filename = FileManager.generate_filename(i, base_name, ext)
            try:
                file_path = os.path.join(output_folder, filename)
                
                # JPG 格式需要转换为 RGB
                if output_format == "JPG" and image.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    # 如果有透明通道，使用它作为 mask
                    if image.mode == 'RGBA':
                        rgb_image.paste(image, mask=image.split()[3])
                    else:
                        rgb_image.paste(image)
                    rgb_image.save(file_path, quality=95)
                else:
                    image.save(file_path)
                
                success_count += 1
            except Exception as e:
                failed_files.append(f"{filename}: {str(e)}")
        
        return success_count, failed_files
    
    @staticmethod
    def get_output_path(file_path: str, custom_path: str = "", use_custom: bool = False) -> str:
        """
        获取输出路径
        
        Args:
            file_path: 原文件路径
            custom_path: 自定义输出路径
            use_custom: 是否使用自定义路径
            
        Returns:
            输出基础路径
        """
        if use_custom and custom_path:
            return custom_path
        else:
            return os.path.dirname(file_path)
    
    @staticmethod
    def generate_output_folder_name(original_filename: str) -> str:
        """
        生成输出文件夹名称
        
        Args:
            original_filename: 原文件名（含扩展名）
            
        Returns:
            文件夹名称，如 "emoji_split"
        """
        base_name = os.path.splitext(original_filename)[0]
        return f"{base_name}_split"
    
    @staticmethod
    def check_disk_space(path: str, required_mb: int = 100) -> bool:
        """
        检查磁盘空间是否足够
        
        Args:
            path: 检查路径
            required_mb: 需要的空间（MB）
            
        Returns:
            是否有足够空间
        """
        try:
            import shutil
            stat = shutil.disk_usage(path)
            available_mb = stat.free / (1024 * 1024)
            return available_mb >= required_mb
        except:
            return True  # 无法检查时假设有足够空间
    
    @staticmethod
    def clean_history(base_path: str, pattern: str = "*_split") -> Tuple[int, List[str]]:
        """
        清理历史输出文件夹
        
        Args:
            base_path: 基础路径
            pattern: 匹配模式
            
        Returns:
            (删除数量, 失败列表)
        """
        import glob
        
        deleted_count = 0
        failed_list = []
        
        # 查找匹配的文件夹
        pattern_path = os.path.join(base_path, pattern)
        folders = glob.glob(pattern_path)
        
        for folder in folders:
            if os.path.isdir(folder):
                try:
                    shutil.rmtree(folder)
                    deleted_count += 1
                except Exception as e:
                    failed_list.append(f"{os.path.basename(folder)}: {str(e)}")
        
        return deleted_count, failed_list

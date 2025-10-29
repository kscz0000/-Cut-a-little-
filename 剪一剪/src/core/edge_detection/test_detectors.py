"""
测试不同边缘检测器的效果
"""

import cv2
import numpy as np
from PIL import Image
import os
from smart_edge_detector import SmartEdgeDetector
from enhanced_edge_detector import EnhancedEdgeDetector
from dl_edge_detector import DLEdgeDetector
from adaptive_edge_detector import AdaptiveEdgeDetector


def load_test_image(image_path: str) -> Image.Image:
    """加载测试图片"""
    if not os.path.exists(image_path):
        # 创建一个测试图片
        img = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        # 添加一些边缘线
        img[0:10, :] = [255, 255, 255]  # 上边
        img[-10:, :] = [255, 255, 255]  # 下边
        img[:, 0:10] = [255, 255, 255]  # 左边
        img[:, -10:] = [255, 255, 255]  # 右边
        return Image.fromarray(img)
    return Image.open(image_path)


def test_all_detectors(image_path: str | None = None):
    """测试所有检测器"""
    # 加载测试图片
    image = load_test_image(image_path) if image_path else load_test_image("test_image.png")
    
    # 创建检测器实例
    detectors = {
        "基础检测器": SmartEdgeDetector(),
        "增强检测器": EnhancedEdgeDetector(),
        "深度学习检测器": DLEdgeDetector(),
        "自适应检测器": AdaptiveEdgeDetector()
    }
    
    print("开始测试各种边缘检测器...")
    print(f"图片尺寸: {image.size}")
    
    # 测试各种模式
    modes = ['auto', 'aggressive', 'conservative']
    
    # 特殊模式
    special_modes = {
        "增强检测器": ['ai_optimized'],
        "深度学习检测器": ['dl_optimized'],
        "自适应检测器": ['adaptive']
    }
    
    for name, detector in detectors.items():
        print(f"\n=== 测试 {name} ===")
        
        # 测试标准模式
        for mode in modes:
            try:
                result = detector.detect_and_remove_edges(image, mode)
                print(f"  {mode} 模式: {result.size}")
                
                # 保存结果
                result.save(f"result_{name.replace(' ', '_')}_{mode}.png")
            except Exception as e:
                print(f"  {mode} 模式失败: {str(e)}")
        
        # 测试特殊模式
        if name in special_modes:
            for mode in special_modes[name]:
                try:
                    result = detector.detect_and_remove_edges(image, mode)
                    print(f"  {mode} 模式: {result.size}")
                    
                    # 保存结果
                    result.save(f"result_{name.replace(' ', '_')}_{mode}.png")
                except Exception as e:
                    print(f"  {mode} 模式失败: {str(e)}")
        
        # 生成预览图
        try:
            preview = detector.preview_detection(image)
            preview.save(f"preview_{name.replace(' ', '_')}.png")
            print(f"  预览图已保存")
        except Exception as e:
            print(f"  预览图生成失败: {str(e)}")
    
    print("\n测试完成！结果已保存到当前目录。")


def compare_performance(image_path: str | None = None):
    """比较不同检测器的性能"""
    import time
    
    # 加载测试图片
    image = load_test_image(image_path) if image_path else load_test_image("test_image.png")
    
    # 创建检测器实例
    detectors = {
        "基础检测器": SmartEdgeDetector(),
        "增强检测器": EnhancedEdgeDetector(),
        "深度学习检测器": DLEdgeDetector(),
        "自适应检测器": AdaptiveEdgeDetector()
    }
    
    print("性能测试开始...")
    
    for name, detector in detectors.items():
        print(f"\n测试 {name} 性能:")
        
        # 测试处理时间
        start_time = time.time()
        for _ in range(10):  # 重复10次
            try:
                result = detector.detect_and_remove_edges(image, 'auto')
            except Exception as e:
                print(f"  处理失败: {str(e)}")
                break
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        print(f"  平均处理时间: {avg_time:.4f} 秒")
        
        # 测试内存使用（简化）
        try:
            result = detector.detect_and_remove_edges(image, 'auto')
            print(f"  处理后图片尺寸: {result.size}")
        except Exception as e:
            print(f"  尺寸获取失败: {str(e)}")


if __name__ == "__main__":
    # 运行测试
    test_all_detectors()
    
    # 运行性能测试
    compare_performance()
    
    print("\n所有测试完成！")
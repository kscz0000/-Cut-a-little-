from cx_Freeze import setup, Executable
import sys
import os

# 构建选项 - 修复版本（排除更多可能导致冲突的模块）
build_exe_options = {
    "packages": ["ui", "core", "utils"],  # 明确包含所有包
    "includes": [
        "ui.main_window_qt",
        "ui.main_window",
        "core.settings_manager",
        "core.language_manager", 
        "core.image_processor",
        "core.file_manager",
        "utils.validators"
    ],  # 包含具体模块
    "include_files": [
        ("src/ui", "ui"),  # 复制整个 ui 文件夹
        ("src/core", "core"),  # 复制整个 core 文件夹
        ("src/utils", "utils"),  # 复制整个 utils 文件夹
        ("assets", "assets"),
        ("config.json", "config.json")
    ],
    "excludes": [
        "PySide6", 
        "tkinter", 
        "unittest",
        "pytest",
        "PIL.PySide6",
        "PIL.PyQt5",
        "PIL.PyQt6",
        "matplotlib",
        "numpy.random._pickle"
    ],
}

setup(
    name="剪一剪表情包分割器",
    version="2.0",
    description="专业表情包分割工具",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "src/main_qt.py",
            base="Win32GUI" if sys.platform == "win32" else None,
            target_name="剪一剪.exe",
            icon="assets/app_icon.png"
        )
    ]
)

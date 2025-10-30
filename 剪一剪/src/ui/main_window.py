"""
主窗口模块
实现应用程序的主界面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings_manager import SettingsManager
from core.image_processor import ImageProcessor
from core.file_manager import FileManager
from utils.validators import Validators
import threading
import time
from datetime import datetime


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.settings = SettingsManager()
        self.image_processor = ImageProcessor()
        self.file_manager = FileManager()
        self.validators = Validators()
        
        # 状态变量
        self.selected_files = []
        self.current_file_index = -1
        self.rotation_angles = {}  # 存储每个文件的旋转角度
        self.current_image = None
        self.current_thumbnail = None
        self.preview_images = []  # 分割预览图片列表
        self.processing = False  # 是否正在处理
        self.last_output_folder = None  # 最后的输出文件夹
        
        # Canvas相关变量
        self.original_canvas = None
        self.original_canvas_image = None
        self.drag_start = None  # 拖动起始位置
        self.last_angle = 0  # 上次的旋转角度
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("剪一剪 - 表情包分割器 V2.0")
        
        # 设置窗口大小
        window_size = self.settings.get("window_size", "1000x750")
        self.root.geometry(window_size)
        self.root.minsize(800, 650)
        
        # 设置图标
        try:
            # 首先尝试加载PNG格式的图标
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "app_icon.png")
            if not os.path.exists(icon_path):
                # 如果PNG图标不存在，尝试加载旧的ICO格式图标
                icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 创建界面
        self.create_ui()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        """创建用户界面（基于PCUI规范）"""
        # 设置主题色系
        self.theme_colors = {
            'bg_primary': '#FAFBFC',
            'bg_secondary': '#FFFFFF',
            'bg_accent': '#F6F8FA',
            'primary': '#0969DA',
            'primary_hover': '#0860CA',
            'success': '#1A7F37',
            'danger': '#CF222E',
            'warning': '#9A6700',
            'text_primary': '#24292F',
            'text_secondary': '#57606A',
            'text_tertiary': '#8B949E',
            'border': '#D0D7DE',
            'shadow': '#0001',
        }
        
        # 主背景
        self.root.config(bg=self.theme_colors['bg_primary'])
        
        # 顶部导航栏（玻璃拟态）
        self.create_modern_navbar()
        
        # 主容器（三栏布局）
        self.create_main_layout()
    
    def create_modern_navbar(self):
        """创建现代化导航栏（玻璃拟态效果）"""
        navbar = tk.Frame(self.root, bg='#FFFFFF', height=56)
        navbar.pack(fill='x', side='top')
        navbar.pack_propagate(False)
        
        # 添加底部边框阴影
        separator = tk.Frame(navbar, bg='#E5E7EB', height=1)
        separator.pack(side='bottom', fill='x')
        
        # 左侧：Logo和标题
        left_frame = tk.Frame(navbar, bg='#FFFFFF')
        left_frame.pack(side='left', padx=24, pady=12)
        
        tk.Label(
            left_frame,
            text="✂️ 剪一剪",
            font=('微软雅黑', 16, 'bold'),
            fg=self.theme_colors['text_primary'],
            bg='#FFFFFF'
        ).pack(side='left')
        
        tk.Label(
            left_frame,
            text="表情包分割器 V2.0",
            font=('微软雅黑', 10),
            fg=self.theme_colors['text_tertiary'],
            bg='#FFFFFF'
        ).pack(side='left', padx=(8, 0))
        
        # 右侧：状态指示器
        right_frame = tk.Frame(navbar, bg='#FFFFFF')
        right_frame.pack(side='right', padx=24, pady=12)
        
        self.status_indicator = tk.Label(
            right_frame,
            text="● 就绪",
            font=('微软雅黑', 9),
            fg=self.theme_colors['success'],
            bg='#FFFFFF'
        )
        self.status_indicator.pack()
    
    def create_main_layout(self):
        """创建三栏主布局"""
        container = tk.Frame(self.root, bg=self.theme_colors['bg_primary'])
        container.pack(fill='both', expand=True, padx=16, pady=16)
        
        # 左侧栏：文件管理 (固定宽度 280px)
        left_panel = tk.Frame(container, bg=self.theme_colors['bg_secondary'], width=280)
        left_panel.pack(side='left', fill='y', padx=(0, 12))
        left_panel.pack_propagate(False)
        self.create_file_panel(left_panel)
        
        # 中间栏：预览与设置 (自适应)
        center_panel = tk.Frame(container, bg=self.theme_colors['bg_primary'])
        center_panel.pack(side='left', fill='both', expand=True, padx=(0, 12))
        self.create_preview_panel(center_panel)
        
        # 右侧栏：操作与日志 (固定宽度 300px)
        right_panel = tk.Frame(container, bg=self.theme_colors['bg_secondary'], width=300)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False)
        self.create_action_panel(right_panel)
    
    def create_file_panel(self, parent):
        """创建文件管理面板（左侧栏）"""
        # 添加内边距容器
        content = tk.Frame(parent, bg=self.theme_colors['bg_secondary'])
        content.pack(fill='both', expand=True, padx=16, pady=16)
        
        # 标题
        tk.Label(
            content,
            text="📁 文件管理",
            font=('微软雅黑', 12, 'bold'),
            fg=self.theme_colors['text_primary'],
            bg=self.theme_colors['bg_secondary']
        ).pack(anchor='w', pady=(0, 12))
        
        self.create_file_section(content)
    
    def create_file_section(self, parent):
        """创建文件选择区（现代化风格）"""
        # 文件列表卡片
        list_card = tk.Frame(parent, bg='#F9FAFB', relief='solid', bd=1)
        list_card.pack(fill='both', expand=True, pady=(0, 12))
        
        # 内部内容
        list_content = tk.Frame(list_card, bg='#F9FAFB')
        list_content.pack(fill='both', expand=True, padx=8, pady=8)
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_content)
        scrollbar.pack(side='right', fill='y')
        
        # 文件列表
        self.file_listbox = tk.Listbox(
            list_content,
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            font=('微软雅黑', 9),
            height=10,
            bg='#FFFFFF',
            fg=self.theme_colors['text_primary'],
            selectbackground=self.theme_colors['primary'],
            selectforeground='#FFFFFF',
            relief='flat',
            highlightthickness=0
        )
        self.file_listbox.pack(side='left', fill='both', expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 文件计数
        self.file_count_label = tk.Label(
            parent,
            text="已选择 0 个文件 / 最多10个",
            font=('微软雅黑', 8),
            fg=self.theme_colors['text_tertiary'],
            bg=self.theme_colors['bg_secondary']
        )
        self.file_count_label.pack(anchor='w', pady=(0, 12))
        
        # 操作按钮组
        self.create_modern_button(
            parent, "➕ 添加文件", 
            self.add_files, 
            'primary'
        ).pack(fill='x', pady=(0, 8))
        
        self.create_modern_button(
            parent, "❌ 删除选中", 
            self.remove_selected, 
            'danger'
        ).pack(fill='x', pady=(0, 8))
        
        self.create_modern_button(
            parent, "🗑️ 清空列表", 
            self.clear_files, 
            'secondary'
        ).pack(fill='x')
    
    def create_modern_button(self, parent, text, command, style='primary'):
        """创建现代化按钮（微交互效果）"""
        colors = {
            'primary': {'bg': self.theme_colors['primary'], 'hover': self.theme_colors['primary_hover'], 'fg': '#FFFFFF'},
            'success': {'bg': self.theme_colors['success'], 'hover': '#18762E', 'fg': '#FFFFFF'},
            'danger': {'bg': self.theme_colors['danger'], 'hover': '#B91C1C', 'fg': '#FFFFFF'},
            'secondary': {'bg': '#6B7280', 'hover': '#4B5563', 'fg': '#FFFFFF'},
        }
        
        btn_style = colors.get(style, colors['primary'])
        
        btn = tk.Button(
            parent,
            text=text,
            font=('微软雅黑', 9, 'bold'),
            bg=btn_style['bg'],
            fg=btn_style['fg'],
            activebackground=btn_style['hover'],
            activeforeground='#FFFFFF',
            relief='flat',
            bd=0,
            cursor='hand2',
            command=command,
            padx=16,
            pady=10
        )
        
        # 添加悬停效果
        def on_enter(e):
            btn.config(bg=btn_style['hover'])
        
        def on_leave(e):
            btn.config(bg=btn_style['bg'])
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def create_preview_panel(self, parent):
        """创建预览面板（中间栏）"""
        # 预览区卡片
        preview_card = tk.Frame(parent, bg=self.theme_colors['bg_secondary'])
        preview_card.pack(fill='both', expand=True, pady=(0, 12))
        
        # 内部内容
        content = tk.Frame(preview_card, bg=self.theme_colors['bg_secondary'])
        content.pack(fill='both', expand=True, padx=16, pady=16)
        
        # 标题
        tk.Label(
            content,
            text="🔍 预览与设置",
            font=('微软雅黑', 12, 'bold'),
            fg=self.theme_colors['text_primary'],
            bg=self.theme_colors['bg_secondary']
        ).pack(anchor='w', pady=(0, 16))
        
        self.create_preview_section(content)
        
        # 分割线
        tk.Frame(content, bg=self.theme_colors['border'], height=1).pack(fill='x', pady=16)
        
        self.create_settings_section(content)
    
    def create_action_panel(self, parent):
        """创建操作面板（右侧栏）"""
        # 内部内容
        content = tk.Frame(parent, bg=self.theme_colors['bg_secondary'])
        content.pack(fill='both', expand=True, padx=16, pady=16)
        
        # 标题
        tk.Label(
            content,
            text="⚙️ 操作控制",
            font=('微软雅黑', 12, 'bold'),
            fg=self.theme_colors['text_primary'],
            bg=self.theme_colors['bg_secondary']
        ).pack(anchor='w', pady=(0, 16))
        
        # 进度显示
        progress_frame = tk.Frame(content, bg='#F9FAFB', relief='solid', bd=1)
        progress_frame.pack(fill='x', pady=(0, 16))
        
        progress_content = tk.Frame(progress_frame, bg='#F9FAFB')
        progress_content.pack(fill='both', expand=True, padx=12, pady=12)
        
        tk.Label(
            progress_content,
            text="📋 处理进度",
            font=('微软雅黑', 9, 'bold'),
            fg=self.theme_colors['text_secondary'],
            bg='#F9FAFB'
        ).pack(anchor='w', pady=(0, 8))
        
        self.progress_label = tk.Label(
            progress_content,
            text="准备就绪...",
            font=('微软雅黑', 8),
            fg=self.theme_colors['text_tertiary'],
            bg='#F9FAFB'
        )
        self.progress_label.pack(anchor='w', pady=(0, 6))
        
        self.progress_bar = ttk.Progressbar(
            progress_content,
            mode='determinate',
            length=260
        )
        self.progress_bar.pack(fill='x')
        
        # 主要操作按钮
        self.process_btn = self.create_modern_button(
            content,
            "▶️ 开始处理",
            self.start_processing,
            'success'
        )
        self.process_btn.pack(fill='x', pady=(0, 8))
        
        self.create_modern_button(
            content,
            "📂 打开输出目录",
            self.open_output_folder,
            'primary'
        ).pack(fill='x', pady=(0, 16))
        
        # 分割线
        tk.Frame(content, bg=self.theme_colors['border'], height=1).pack(fill='x', pady=(0, 16))
        
        # 日志区
        tk.Label(
            content,
            text="📜 处理日志",
            font=('微软雅黑', 10, 'bold'),
            fg=self.theme_colors['text_primary'],
            bg=self.theme_colors['bg_secondary']
        ).pack(anchor='w', pady=(0, 12))
        
        # 日志文本框
        log_container = tk.Frame(content, bg='#1F2937', relief='solid', bd=1)
        log_container.pack(fill='both', expand=True, pady=(0, 8))
        
        log_scroll = tk.Scrollbar(log_container)
        log_scroll.pack(side='right', fill='y')
        
        self.log_text = tk.Text(
            log_container,
            font=('Consolas', 8),
            yscrollcommand=log_scroll.set,
            wrap=tk.WORD,
            bg='#1F2937',
            fg='#D1D5DB',
            height=15,
            relief='flat',
            highlightthickness=0
        )
        self.log_text.pack(side='left', fill='both', expand=True, padx=8, pady=8)
        log_scroll.config(command=self.log_text.yview)
        
        # 清空日志按钮
        self.create_modern_button(
            content,
            "🗑️ 清空日志",
            self.clear_log,
            'secondary'
        ).pack(fill='x')
    
    def create_preview_section(self, parent):
        """创建预览区（Phase 2 完整版本 - 现代化风格）"""
        # 预览容器
        preview_container = tk.Frame(parent, bg=self.theme_colors['bg_secondary'])
        preview_container.pack(fill='both', expand=True)
        
        # 左右分栏
        left_preview = tk.Frame(preview_container, bg='#F9FAFB', width=280)
        left_preview.pack(side='left', fill='y', padx=(0, 12))
        left_preview.pack_propagate(False)
        
        right_preview = tk.Frame(preview_container, bg='#F9FAFB')
        right_preview.pack(side='right', fill='both', expand=True)
        
        # === 左侧：原图预览 ===
        left_content = tk.Frame(left_preview, bg='#F9FAFB')
        left_content.pack(fill='both', expand=True, padx=12, pady=12)
        
        tk.Label(
            left_content,
            text="🖼️ 原图预览",
            font=('微软雅黑', 9, 'bold'),
            fg=self.theme_colors['text_secondary'],
            bg='#F9FAFB'
        ).pack(pady=(0, 8))
        
        # Canvas容器
        canvas_container = tk.Frame(left_content, bg='#FFFFFF', relief='solid', bd=1)
        canvas_container.pack(fill='both', expand=True, pady=(0, 8))
        
        self.original_canvas = tk.Canvas(
            canvas_container,
            width=250,
            height=250,
            bg='#FAFBFC',
            highlightthickness=0
        )
        self.original_canvas.pack(expand=True, padx=4, pady=4)
        
        # 绑定鼠标事件
        self.original_canvas.bind('<Button-1>', self.on_canvas_press)
        self.original_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.original_canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # 旋转控制
        rotate_frame = tk.Frame(left_content, bg='#F9FAFB')
        rotate_frame.pack(pady=(0, 8))
        
        self.create_icon_button(rotate_frame, "↶ -90°", lambda: self.rotate_quick(-90)).pack(side='left', padx=2)
        self.create_icon_button(rotate_frame, "↷ +90°", lambda: self.rotate_quick(90)).pack(side='left', padx=2)
        self.create_icon_button(rotate_frame, "🔄 重置", self.reset_rotation).pack(side='left', padx=2)
        
        # 图片信息
        self.image_info_label = tk.Label(
            left_content,
            text="角度: 0° | 尺寸: --\n格式: --",
            font=('微软雅黑', 8),
            fg=self.theme_colors['text_tertiary'],
            bg='#F9FAFB',
            justify='center'
        )
        self.image_info_label.pack()
        
        # === 右侧：分割预览 ===
        right_content = tk.Frame(right_preview, bg='#F9FAFB')
        right_content.pack(fill='both', expand=True, padx=12, pady=12)
        
        tk.Label(
            right_content,
            text="✂️ 分割后预览",
            font=('微软雅黑', 9, 'bold'),
            fg=self.theme_colors['text_secondary'],
            bg='#F9FAFB'
        ).pack(pady=(0, 8))
        
        # 分割预览容器
        split_container = tk.Frame(right_content, bg='#FFFFFF', relief='solid', bd=1)
        split_container.pack(fill='both', expand=True, pady=(0, 8))
        
        split_scroll = tk.Scrollbar(split_container)
        split_scroll.pack(side='right', fill='y')
        
        self.split_canvas = tk.Canvas(
            split_container,
            bg='#FAFBFC',
            yscrollcommand=split_scroll.set,
            highlightthickness=0
        )
        self.split_canvas.pack(side='left', fill='both', expand=True)
        split_scroll.config(command=self.split_canvas.yview)
        
        self.split_preview_frame = tk.Frame(self.split_canvas, bg='#FAFBFC')
        self.split_canvas.create_window((0, 0), window=self.split_preview_frame, anchor='nw')
        
        # 分割信息
        self.split_info_label = tk.Label(
            right_content,
            text="分割: -- | 总数: --",
            font=('微软雅黑', 8),
            fg=self.theme_colors['text_tertiary'],
            bg='#F9FAFB'
        )
        self.split_info_label.pack()
        
        # 提示标签
        self.preview_hint = tk.Label(
            preview_container,
            text="📷 请添加文件并选择以查看预览",
            font=('微软雅黑', 11),
            fg=self.theme_colors['text_tertiary'],
            bg=self.theme_colors['bg_secondary']
        )
        self.preview_hint.pack_forget()
    
    def create_icon_button(self, parent, text, command):
        """创建小型图标按钮"""
        btn = tk.Button(
            parent,
            text=text,
            font=('微软雅黑', 8),
            bg='#E5E7EB',
            fg=self.theme_colors['text_primary'],
            activebackground='#D1D5DB',
            relief='flat',
            bd=0,
            cursor='hand2',
            command=command,
            padx=8,
            pady=4
        )
        
        def on_enter(e):
            btn.config(bg='#D1D5DB')
        
        def on_leave(e):
            btn.config(bg='#E5E7EB')
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def create_settings_section(self, parent):
        """创建分割设置区（现代化风格）"""
        # 设置卡片
        settings_card = tk.Frame(parent, bg='#F9FAFB', relief='solid', bd=1)
        settings_card.pack(fill='x')
        
        content = tk.Frame(settings_card, bg='#F9FAFB')
        content.pack(fill='both', expand=True, padx=16, pady=12)
        
        # 标题
        tk.Label(
            content,
            text="⚙️ 分割设置",
            font=('微软雅黑', 10, 'bold'),
            fg=self.theme_colors['text_secondary'],
            bg='#F9FAFB'
        ).pack(anchor='w', pady=(0, 12))
        
        # 分割模式
        mode_frame = tk.Frame(content, bg='#F9FAFB')
        mode_frame.pack(fill='x', pady=(0, 12))
        
        tk.Label(
            mode_frame,
            text="分割模式：",
            font=('微软雅黑', 9),
            fg=self.theme_colors['text_primary'],
            bg='#F9FAFB'
        ).pack(side='left', padx=(0, 12))
        
        self.grid_mode = tk.StringVar(value="auto")
        
        tk.Radiobutton(
            mode_frame,
            text="自动检测",
            variable=self.grid_mode,
            value="auto",
            font=('微软雅黑', 9),
            bg='#F9FAFB',
            fg=self.theme_colors['text_primary'],
            selectcolor='#F9FAFB',
            activebackground='#F9FAFB'
        ).pack(side='left', padx=(0, 12))
        
        tk.Radiobutton(
            mode_frame,
            text="自定义",
            variable=self.grid_mode,
            value="custom",
            font=('微软雅黑', 9),
            bg='#F9FAFB',
            fg=self.theme_colors['text_primary'],
            selectcolor='#F9FAFB',
            activebackground='#F9FAFB'
        ).pack(side='left')
        
        # 自定义行列数
        grid_frame = tk.Frame(content, bg='#F9FAFB')
        grid_frame.pack(fill='x', pady=(0, 12))
        
        tk.Label(
            grid_frame,
            text="行数：",
            font=('微软雅黑', 9),
            fg=self.theme_colors['text_primary'],
            bg='#F9FAFB'
        ).pack(side='left', padx=(0, 8))
        
        self.rows_var = tk.StringVar(value="3")
        tk.Spinbox(
            grid_frame,
            from_=1,
            to=18,
            textvariable=self.rows_var,
            width=6,
            font=('微软雅黑', 9),
            relief='solid',
            bd=1
        ).pack(side='left', padx=(0, 16))
        
        tk.Label(
            grid_frame,
            text="列数：",
            font=('微软雅黑', 9),
            fg=self.theme_colors['text_primary'],
            bg='#F9FAFB'
        ).pack(side='left', padx=(0, 8))
        
        self.cols_var = tk.StringVar(value="3")
        tk.Spinbox(
            grid_frame,
            from_=1,
            to=18,
            textvariable=self.cols_var,
            width=6,
            font=('微软雅黑', 9),
            relief='solid',
            bd=1
        ).pack(side='left')
        
        tk.Label(
            grid_frame,
            text="范围: 1-18",
            font=('微软雅黑', 8),
            fg=self.theme_colors['text_tertiary'],
            bg='#F9FAFB'
        ).pack(side='left', padx=(12, 0))
        
        # 输出格式
        format_frame = tk.Frame(content, bg='#F9FAFB')
        format_frame.pack(fill='x')
        
        tk.Label(
            format_frame,
            text="输出格式：",
            font=('微软雅黑', 9),
            fg=self.theme_colors['text_primary'],
            bg='#F9FAFB'
        ).pack(side='left', padx=(0, 12))
        
        self.output_format = tk.StringVar(value="PNG")
        
        tk.Radiobutton(
            format_frame,
            text="PNG (透明)",
            variable=self.output_format,
            value="PNG",
            font=('微软雅黑', 9),
            bg='#F9FAFB',
            fg=self.theme_colors['text_primary'],
            selectcolor='#F9FAFB',
            activebackground='#F9FAFB'
        ).pack(side='left', padx=(0, 12))
        
        tk.Radiobutton(
            format_frame,
            text="JPG (小文件)",
            variable=self.output_format,
            value="JPG",
            font=('微软雅黑', 9),
            bg='#F9FAFB',
            fg=self.theme_colors['text_primary'],
            selectcolor='#F9FAFB',
            activebackground='#F9FAFB'
        ).pack(side='left')
        
        # 绑定参数变化事件
        self.grid_mode.trace('w', lambda *args: self.on_settings_change())
        self.rows_var.trace('w', lambda *args: self.on_settings_change())
        self.cols_var.trace('w', lambda *args: self.on_settings_change())
    
    def on_settings_change(self):
        """设置变更时更新预览"""
        if self.current_image and self.current_file_index != -1:
            # 延迟更新（防抖）
            if hasattr(self, '_update_timer'):
                self.root.after_cancel(self._update_timer)
            self._update_timer = self.root.after(300, self.update_preview)
    
    # ========== 事件处理方法 ==========
    
    def add_files(self):
        """添加文件"""
        # 检查文件数量限制
        current_count = len(self.selected_files)
        if current_count >= 10:
            messagebox.showwarning("提示", "已达文件数量上限（10个），无法继续添加")
            return
        
        # 打开文件对话框
        initial_dir = self.settings.get("last_directory", os.path.expanduser("~/Pictures"))
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("所有文件", "*.*")
            ],
            initialdir=initial_dir
        )
        
        if not files:
            return
        
        # 验证并添加文件
        added_count = 0
        for file_path in files:
            if len(self.selected_files) >= 10:
                messagebox.showwarning("提示", f"已达文件数量上限（10个），成功添加 {added_count} 个文件")
                break
            
            # 验证文件格式
            valid, error_msg = self.validators.validate_file_format(file_path)
            if not valid:
                self.add_log(f"[错误] {error_msg}")
                continue
            
            # 避免重复添加
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                added_count += 1
        
        # 更新界面
        self.update_file_listbox()
        
        # 保存最后使用的目录
        if files:
            self.settings.set("last_directory", os.path.dirname(files[0]))
        
        # 自动选中第一个文件
        if self.current_file_index == -1 and self.selected_files:
            self.file_listbox.selection_set(0)
            self.on_file_select(None)
        
        self.add_log(f"已添加 {added_count} 个文件")
    
    def remove_selected(self):
        """删除选中的文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.selected_files.pop(index)
        self.update_file_listbox()
        
        # 清除预览
        if not self.selected_files:
            self.current_file_index = -1
            self.preview_hint.pack(expand=True)
        
        self.add_log(f"已删除文件")
    
    def clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.rotation_angles.clear()
        self.current_file_index = -1
        self.update_file_listbox()
        self.preview_hint.pack(expand=True)
        self.add_log("已清空文件列表")
    
    def update_file_listbox(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        for i, file_path in enumerate(self.selected_files):
            self.file_listbox.insert(tk.END, f" 🖼️ {i+1}. {os.path.basename(file_path)}")
        
        count = len(self.selected_files)
        max_count = 10
        
        # 更新状态显示
        if count >= max_count:
            self.file_count_label.config(
                text=f"✅ 已选择 {count} 个文件 (已达上限)",
                fg=self.theme_colors['warning']
            )
        else:
            self.file_count_label.config(
                text=f"📊 已选择 {count} 个文件 / 最多{max_count}个",
                fg=self.theme_colors['text_tertiary']
            )
    
    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.current_file_index = index
        file_path = self.selected_files[index]
        
        # 加载图片
        self.current_image = self.image_processor.load_image(file_path)
        if self.current_image:
            self.preview_hint.pack_forget()
            
            # 获取或初始化旋转角度
            if file_path not in self.rotation_angles:
                self.rotation_angles[file_path] = 0
            
            # 更新预览
            self.update_preview()
            
            # 验证图片尺寸
            width, height = self.current_image.size
            valid, warning = self.validators.validate_image_size(width, height)
            if not valid:
                self.add_log(f"[警告] {warning}")
            
            self.add_log(f"已选中: {os.path.basename(file_path)} ({width}x{height}px)")
        else:
            self.add_log(f"[错误] 无法加载图片: {os.path.basename(file_path)}")
    
    def start_processing(self):
        """开始处理（Phase 3 完整版本）"""
        if not self.selected_files:
            messagebox.showwarning("提示", "请先添加图片文件！")
            return
        
        if self.processing:
            return
        
        # 验证行列数
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的行列数")
            return
        
        valid, error_msg = self.validators.validate_grid_size(rows, cols)
        if not valid:
            messagebox.showerror("错误", error_msg)
            return
        
        # 开始处理
        self.processing = True
        self.process_btn.config(text="处理中...", state='disabled')
        
        # 使用多线程避免UI冻结
        thread = threading.Thread(target=self.process_files_thread, daemon=True)
        thread.start()
    
    def process_files_thread(self):
        """批量处理文件（工作线程）"""
        try:
            total = len(self.selected_files)
            success_count = 0
            fail_count = 0
            start_time = time.time()
            
            for i, file_path in enumerate(self.selected_files):
                # 更新进度
                progress = int((i / total) * 100)
                filename = os.path.basename(file_path)
                
                self.root.after(0, lambda p=progress, f=filename: self.update_progress(p, f"处理中: {i+1}/{total} - {f}"))
                self.root.after(0, lambda f=filename: self.add_log(f"[处理] {f}"))
                
                # 处理单个文件
                success = self.process_single_file(file_path)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            
            # 完成
            elapsed = time.time() - start_time
            self.root.after(0, lambda: self.update_progress(100, "处理完成！"))
            self.root.after(0, lambda: self.on_processing_complete(success_count, fail_count, elapsed))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_log(f"[错误] 处理异常: {str(e)}"))
        finally:
            self.processing = False
            self.root.after(0, lambda: self.process_btn.config(text="开始处理", state='normal'))
    
    def process_single_file(self, file_path: str) -> bool:
        """处理单个文件"""
        try:
            # 加载图片
            image = self.image_processor.load_image(file_path)
            if not image:
                self.root.after(0, lambda: self.add_log(f"  [失败] 无法加载图片"))
                return False
            
            # 应用旋转
            angle = self.rotation_angles.get(file_path, 0)
            if angle != 0:
                image = self.image_processor.rotate_image(image, angle)
            
            # 获取分割参数
            if self.grid_mode.get() == "auto":
                grid_type = self.image_processor.detect_grid_type(*image.size)
                rows, cols = (3, 3) if grid_type == "9grid" else (2, 2)
            else:
                rows = int(self.rows_var.get())
                cols = int(self.cols_var.get())
            
            # 分割图片
            split_images = self.image_processor.crop_by_lines(image, rows, cols)
            
            # 创建输出文件夹
            base_path = self.file_manager.get_output_path(file_path)
            folder_name = self.file_manager.generate_output_folder_name(os.path.basename(file_path))
            
            success, output_path = self.file_manager.create_output_folder(base_path, folder_name)
            if not success:
                self.root.after(0, lambda msg=output_path: self.add_log(f"  [失败] {msg}"))
                return False
            
            # 保存图片
            output_format = self.output_format.get()
            saved_count, failed_files = self.file_manager.save_split_images(
                split_images,
                output_path,
                os.path.basename(file_path),
                output_format
            )
            
            if failed_files:
                for error in failed_files:
                    self.root.after(0, lambda e=error: self.add_log(f"  [失败] {e}"))
            
            self.last_output_folder = output_path
            self.root.after(0, lambda c=saved_count, p=output_path: 
                           self.add_log(f"  [成功] 已保存 {c} 张图片 -> {os.path.basename(p)}"))
            
            return saved_count > 0
            
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self.add_log(f"  [异常] {msg}"))
            return False
    
    def update_progress(self, value: int, text: str):
        """更新进度显示"""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)
    
    def on_processing_complete(self, success: int, fail: int, elapsed: float):
        """处理完成回调"""
        total = success + fail
        elapsed_str = f"{elapsed:.1f}秒" if elapsed < 60 else f"{int(elapsed//60)}分{int(elapsed%60)}秒"
        
        message = f"处理完成！\n\n成功: {success} 个\n失败: {fail} 个\n总耗时: {elapsed_str}"
        
        self.add_log("=" * 40)
        self.add_log(f"处理完成！成功 {success} 个，失败 {fail} 个，共耗时 {elapsed_str}")
        self.add_log("=" * 40)
        
        messagebox.showinfo("处理完成", message)
    
    def open_output_folder(self):
        """打开输出文件夹"""
        folder_to_open = self.last_output_folder
        
        if not folder_to_open and self.selected_files:
            # 尝试打开第一个文件的输出位置
            first_file = self.selected_files[0]
            base_path = os.path.dirname(first_file)
            folder_name = self.file_manager.generate_output_folder_name(os.path.basename(first_file))
            folder_to_open = os.path.join(base_path, folder_name)
        
        if folder_to_open and os.path.exists(folder_to_open):
            os.startfile(folder_to_open)
            self.add_log(f"已打开文件夹: {folder_to_open}")
        else:
            messagebox.showinfo("提示", "没有可打开的输出文件夹。\n请先完成图片处理。")
    
    def add_log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("日志已清空")
    
    def on_closing(self):
        """关闭窗口事件"""
        # 保存窗口大小
        self.settings.set("window_size", self.root.geometry())
        self.root.destroy()
    
    # ========== 预览相关方法 ==========
    
    def update_preview(self):
        """更新预览显示"""
        if not self.current_image or self.current_file_index == -1:
            return
        
        file_path = self.selected_files[self.current_file_index]
        angle = self.rotation_angles.get(file_path, 0)
        
        # 获取旋转后的图片
        if angle != 0:
            rotated = self.image_processor.rotate_image(self.current_image, angle)
        else:
            rotated = self.current_image
        
        # 更新原图预览
        self.update_original_preview(rotated, angle)
        
        # 更新分割预览
        self.update_split_preview(rotated)
    
    def update_original_preview(self, image, angle):
        """更新原图预览"""
        # 检查Canvas是否存在
        if not self.original_canvas:
            return
            
        # 创建缩略图
        thumb = self.image_processor.create_thumbnail(image, (260, 260))
        photo = self.image_processor.pil_to_tkimage(thumb)
        
        # 更新Canvas
        self.original_canvas.delete('all')
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        
        # 居中显示
        x = canvas_width // 2 if canvas_width > 1 else 140
        y = canvas_height // 2 if canvas_height > 1 else 140
        
        self.original_canvas_image = self.original_canvas.create_image(x, y, image=photo)
        # 保持引用以防止垃圾回收
        if not hasattr(self, '_canvas_images'):
            self._canvas_images = []
        self._canvas_images.append(photo)
        
        # 更新信息
        width, height = image.size
        fmt = os.path.splitext(self.selected_files[self.current_file_index])[1].upper().replace('.', '')
        self.image_info_label.config(
            text=f"角度: {int(angle)}° | 尺寸: {width}x{height}px\n格式: {fmt}"
        )
    
    def update_split_preview(self, image):
        """更新分割预览"""
        # 获取行列数
        if self.grid_mode.get() == "auto":
            # 自动检测
            grid_type = self.image_processor.detect_grid_type(*image.size)
            rows, cols = (3, 3) if grid_type == "9grid" else (2, 2)
        else:
            # 自定义
            try:
                rows = int(self.rows_var.get())
                cols = int(self.cols_var.get())
            except ValueError:
                rows, cols = 3, 3
        
        # 验证行列数
        valid, error_msg = self.validators.validate_grid_size(rows, cols)
        if not valid:
            self.split_info_label.config(text=f"错误: {error_msg}", fg='#e74c3c')
            return
        
        # 分割图片
        split_images = self.image_processor.crop_by_lines(image, rows, cols)
        
        # 清空之前的预览
        for widget in self.split_preview_frame.winfo_children():
            widget.destroy()
        
        # 计算缩略图尺寸
        total_count = len(split_images)
        thumb_size = self.image_processor.calculate_thumbnail_grid_size(
            total_count, 450, 400, min_thumb_size=60
        )
        
        # 显示分割后的图片
        self.preview_images = []
        for i, img in enumerate(split_images):
            # 创建缩略图
            thumb = self.image_processor.create_thumbnail(img, thumb_size)
            photo = self.image_processor.pil_to_tkimage(thumb)
            self.preview_images.append(photo)
            
            # 创建显示容器
            item_frame = tk.Frame(self.split_preview_frame, bg='#FFFFFF', relief='solid', bd=1)
            item_frame.grid(row=i // 6, column=i % 6, padx=3, pady=3)
            
            # 图片
            img_label = tk.Label(item_frame, image=photo, bg='#FFFFFF')
            img_label.pack(padx=2, pady=2)
            
            # 尺寸信息
            w, h = img.size
            tk.Label(
                item_frame,
                text=f"{i+1}\n{w}x{h}",
                font=('微软雅黑', 7),
                bg='#FFFFFF',
                fg='#7f8c8d'
            ).pack()
        
        # 更新信息
        self.split_info_label.config(
            text=f"✂️ 分割: {rows}×{cols} | 总数: {total_count}张",
            fg=self.theme_colors['text_tertiary']
        )
        
        # 更新滚动区域
        self.split_preview_frame.update_idletasks()
        self.split_canvas.config(scrollregion=self.split_canvas.bbox('all'))
    
    # ========== 旋转相关方法 ==========
    
    def on_canvas_press(self, event):
        """鼠标按下事件"""
        if not self.current_image or not self.original_canvas:
            return
        self.drag_start = (event.x, event.y)
        canvas_center = (self.original_canvas.winfo_width() // 2, self.original_canvas.winfo_height() // 2)
        file_path = self.selected_files[self.current_file_index]
        self.last_angle = self.rotation_angles.get(file_path, 0)
    
    def on_canvas_drag(self, event):
        """鼠标拖动事件（旋转）"""
        if not self.current_image or not self.drag_start or not self.original_canvas:
            return
        
        # 计算旋转角度
        canvas_center_x = self.original_canvas.winfo_width() // 2
        canvas_center_y = self.original_canvas.winfo_height() // 2
        
        import math
        
        # 起始角度
        angle1 = math.atan2(self.drag_start[1] - canvas_center_y, self.drag_start[0] - canvas_center_x)
        # 当前角度
        angle2 = math.atan2(event.y - canvas_center_y, event.x - canvas_center_x)
        
        # 角度差（弧度转角度）
        delta_angle = math.degrees(angle2 - angle1)
        
        # 更新旋转角度
        file_path = self.selected_files[self.current_file_index]
        new_angle = (self.last_angle + delta_angle) % 360
        self.rotation_angles[file_path] = new_angle
        
        # 更新预览
        self.update_preview()
    
    def on_canvas_release(self, event):
        """鼠标释放事件"""
        self.drag_start = None
    
    def rotate_quick(self, angle):
        """快捷旋转"""
        if not self.current_image or self.current_file_index == -1:
            return
        
        file_path = self.selected_files[self.current_file_index]
        current_angle = self.rotation_angles.get(file_path, 0)
        new_angle = (current_angle + angle) % 360
        self.rotation_angles[file_path] = new_angle
        
        self.update_preview()
        self.add_log(f"旋转 {angle}° -> 当前角度: {int(new_angle)}°")
    
    def reset_rotation(self):
        """重置旋转"""
        if not self.current_image or self.current_file_index == -1:
            return
        
        file_path = self.selected_files[self.current_file_index]
        self.rotation_angles[file_path] = 0
        
        self.update_preview()
        self.add_log("已重置旋转角度")
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

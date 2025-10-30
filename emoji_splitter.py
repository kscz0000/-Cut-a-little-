# 表情包分割器 - 微调优化版
# 作者：Gemini
# 功能：移除固定高度，优化按钮间距，解决控件显示不全的问题

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox
import os
import threading
import json
import sys

class Settings:
    """设置管理"""
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(self.app_dir, "settings.json")
        self.default_settings = {
            "last_directory": os.path.expanduser("~/Pictures"),
            "output_format": "PNG", "auto_detect_grid": True, "default_grid_type": "4grid",
            "window_size": "800x680", "custom_output_path": "", "use_custom_output": False
        }
        self.settings = self.load_settings()
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
            else: return self.default_settings.copy()
        except Exception: return self.default_settings.copy()
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception: pass
    def get(self, key, default=None): return self.settings.get(key, default)
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

class EmojiSplitter:
    """表情包分割器主程序"""
    def __init__(self):
        self.settings = Settings()
        self.selected_files = []
        self.processing = False
        self.last_output_folder = None
        self.create_window()
        self.grid_type = tk.StringVar(value=self.settings.get("default_grid_type", "auto"))
        self.auto_detect = tk.BooleanVar(value=self.settings.get("auto_detect_grid", True))
        self.output_format = tk.StringVar(value=self.settings.get("output_format", "PNG"))
        self.custom_output_path = tk.StringVar(value=self.settings.get("custom_output_path", ""))
        self.use_custom_output = tk.BooleanVar(value=self.settings.get("use_custom_output", False))
        self.create_interface()
        self.add_log("表情包分割器已启动")
        self.add_log("支持四宫格和九宫格自动检测")
        self.add_log("请选择图片文件开始处理")

    def create_window(self):
        self.root = tk.Tk()
        self.root.title("表情包分割器")
        self.root.geometry(self.settings.get("window_size", "800x680"))
        self.root.minsize(750, 650)
        self.root.configure(bg='#F5F5DC')
        try:
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            icon_path = os.path.join(base_path, "app_icon.png")
            self.root.iconbitmap(icon_path)
        except: pass
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_interface(self):
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=70)
        title_frame.pack(fill='x', side='top')
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="表情包分割器", font=('微软雅黑', 20, 'bold'), fg='white', bg='#2c3e50').pack(expand=True)
        
        main_content = tk.Frame(self.root, bg=self.root.cget('bg'), padx=15, pady=10)
        main_content.pack(fill='both', expand=True)

        # 修正: 移除文件选择区的固定高度
        file_frame = tk.LabelFrame(main_content, text=" 文件选择 ", font=('微软雅黑', 11, 'bold'), bg='#FAEBD7', padx=15, pady=10)
        file_frame.pack(fill='x', side='top', pady=(0, 10))
        # file_frame.pack_propagate(False) # 不再需要
        self.create_file_section(file_frame)
        
        # 修正: 移除分割设置区的固定高度
        settings_frame = tk.LabelFrame(main_content, text=" 分割设置 ", font=('微软雅黑', 11, 'bold'), bg='#FAEBD7', padx=15, pady=10)
        settings_frame.pack(fill='x', side='top')
        # settings_frame.pack_propagate(False) # 不再需要
        self.create_settings_section(settings_frame)
        
        bottom_frame = tk.Frame(main_content, bg=self.root.cget('bg'))
        bottom_frame.pack(fill='both', expand=True, side='top', pady=(10, 0))
        
        log_container = tk.LabelFrame(bottom_frame, text=" 处理日志 ", font=('微软雅黑', 11, 'bold'), bg='#FAEBD7', padx=10, pady=10)
        log_container.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.create_log_section(log_container)
        
        action_container = tk.LabelFrame(bottom_frame, text=" 操作 ", font=('微软雅黑', 11, 'bold'), bg='#FAEBD7', width=200, padx=15, pady=10)
        action_container.pack(side='right', fill='y')
        action_container.pack_propagate(False)
        self.create_action_section(action_container)

    def create_file_section(self, parent):
        # 增加一个固定高度的容器，确保文件列表框不会过大
        list_container = tk.Frame(parent, bg=parent.cget('bg'), height=120)
        list_container.pack(fill='x')
        list_container.pack_propagate(False)

        list_frame = tk.Frame(list_container, bg=parent.cget('bg'))
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.file_listbox = Listbox(list_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, font=('微软雅黑', 9))
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        btn_frame = tk.Frame(list_container, bg=parent.cget('bg'), width=150)
        btn_frame.pack(side='right', fill='y')
        btn_frame.pack_propagate(False)

        tk.Button(btn_frame, text="添加文件", font=('微软雅黑', 10, 'bold'), bg='#3498db', fg='white', relief='flat', command=self.select_files, cursor="hand2").pack(fill='x', pady=5)
        tk.Button(btn_frame, text="删除选中", font=('微软雅黑', 10, 'bold'), bg='#e67e22', fg='white', relief='flat', command=self.remove_selected_files, cursor="hand2").pack(fill='x', pady=5)
        tk.Button(btn_frame, text="清空列表", font=('微软雅黑', 10, 'bold'), bg='#e74c3c', fg='white', relief='flat', command=self.clear_files, cursor="hand2").pack(fill='x', pady=5)
        self.file_count_label = tk.Label(btn_frame, text="已选择 0 个文件", font=('微软雅黑', 9), bg=parent.cget('bg'), fg='#7f8c8d')
        self.file_count_label.pack(side='bottom', fill='x', pady=5)
        
    def create_settings_section(self, parent):
        mode_card = tk.LabelFrame(parent, text=" 分割模式 ", font=('微软雅黑', 10), bg=parent.cget('bg'), bd=1, relief='solid', padx=15, pady=10)
        mode_card.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        auto_check = tk.Checkbutton(mode_card, text="自动检测宫格类型 (推荐)", variable=self.auto_detect, font=('微软雅黑', 9), bg=parent.cget('bg'), command=self.on_auto_detect_change)
        auto_check.pack(anchor='w')
        
        ttk.Separator(mode_card, orient='horizontal').pack(fill='x', pady=5)
        
        manual_frame = tk.Frame(mode_card, bg=parent.cget('bg'))
        manual_frame.pack(anchor='w', fill='x')
        
        self.grid_radios = []
        radio1 = tk.Radiobutton(manual_frame, text="四宫格 (2x2)", variable=self.grid_type, value="4grid", font=('微软雅黑', 9), bg=parent.cget('bg'))
        radio1.pack(anchor='w')
        self.grid_radios.append(radio1)
        radio2 = tk.Radiobutton(manual_frame, text="九宫格 (3x3)", variable=self.grid_type, value="9grid", font=('微软雅黑', 9), bg=parent.cget('bg'))
        radio2.pack(anchor='w')
        self.grid_radios.append(radio2)

        output_card = tk.LabelFrame(parent, text=" 输出设置 ", font=('微软雅黑', 10), bg=parent.cget('bg'), bd=1, relief='solid', padx=15, pady=10)
        output_card.pack(side='right', fill='both', expand=True)

        tk.Radiobutton(output_card, text="PNG (支持透明)", variable=self.output_format, value="PNG", font=('微软雅黑', 9), bg=parent.cget('bg')).pack(anchor='w')
        tk.Radiobutton(output_card, text="JPG (文件较小)", variable=self.output_format, value="JPG", font=('微软雅黑', 9), bg=parent.cget('bg')).pack(anchor='w')
        
        ttk.Separator(output_card, orient='horizontal').pack(fill='x', pady=5)

        tk.Checkbutton(output_card, text="自定义输出路径", variable=self.use_custom_output, font=('微软雅黑', 9), bg=parent.cget('bg'), command=self.on_custom_output_toggle).pack(anchor='w')
        
        self.path_entry = tk.Entry(output_card, textvariable=self.custom_output_path, font=('微软雅黑', 8))
        self.path_entry.pack(fill='x', pady=(0, 5))
        self.browse_btn = tk.Button(output_card, text="浏览...", font=('微软雅黑', 8), bg='#95a5a6', fg='white', relief='flat', command=self.select_output_path, cursor="hand2")
        self.browse_btn.pack(fill='x')
        
        self.on_auto_detect_change()
        self.on_custom_output_toggle()
        
    def create_log_section(self, parent):
        text_frame = tk.Frame(parent, bg='white')
        text_frame.pack(fill='both', expand=True)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        self.log_text = tk.Text(text_frame, font=('Consolas', 9), yscrollcommand=scrollbar.set, wrap=tk.WORD, bg='#f8f9fa', relief='solid', bd=1)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)

    def create_action_section(self, parent):
        self.progress_label = tk.Label(parent, text="准备就绪", font=('微软雅黑', 9), bg=parent.cget('bg'), fg='#7f8c8d')
        self.progress_label.pack(pady=(0, 5), fill='x')
        self.progress_bar = ttk.Progressbar(parent, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # 修正：调整按钮间距(pady)
        self.process_btn = tk.Button(parent, text="开始处理", font=('微软雅黑', 12, 'bold'), bg='#27ae60', fg='white', relief='flat', pady=10, command=self.start_processing, cursor="hand2")
        self.process_btn.pack(fill='x', pady=(0, 8))
        tk.Button(parent, text="打开输出文件夹", font=('微软雅黑', 10, 'bold'), bg='#3498db', fg='white', relief='flat', pady=7, command=self.open_output_folder, cursor="hand2").pack(fill='x', pady=(0, 8))
        tk.Button(parent, text="清空日志", font=('微软雅黑', 10, 'bold'), bg='#95a5a6', fg='white', relief='flat', pady=7, command=self.clear_log, cursor="hand2").pack(fill='x')

    # --- 以下是功能逻辑代码 (与之前版本完全一致) ---
    def on_auto_detect_change(self):
        state = 'disabled' if self.auto_detect.get() else 'normal'
        for radio in self.grid_radios: radio.configure(state=state)
        if self.auto_detect.get(): self.grid_type.set("auto")
        else: self.grid_type.set("4grid")

    def on_custom_output_toggle(self):
        state = 'normal' if self.use_custom_output.get() else 'disabled'
        self.path_entry.config(state=state)
        self.browse_btn.config(state=state)

    def select_files(self):
        initial_dir = self.settings.get("last_directory", os.path.expanduser("~/Pictures"))
        files = filedialog.askopenfilenames(title="选择图片文件", filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"), ("所有文件", "*.*")], initialdir=initial_dir)
        if files:
            for f in files:
                if f not in self.selected_files: self.selected_files.append(f)
            self.update_file_listbox()
            if files: self.settings.set("last_directory", os.path.dirname(files[0]))

    def remove_selected_files(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        for i in sorted(selected_indices, reverse=True): self.selected_files.pop(i)
        self.update_file_listbox()

    def clear_files(self):
        self.selected_files.clear()
        self.update_file_listbox()

    def update_file_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files: self.file_listbox.insert(tk.END, os.path.basename(file_path))
        count = len(self.selected_files)
        self.file_count_label.config(text=f"已选择 {count} 个文件")

    def select_output_path(self):
        initial_dir = self.custom_output_path.get() or os.path.expanduser("~/Pictures")
        folder_path = filedialog.askdirectory(title="选择输出文件夹", initialdir=initial_dir)
        if folder_path:
            self.custom_output_path.set(folder_path)
            self.settings.set("custom_output_path", folder_path)
            self.add_log(f"输出路径：{folder_path}")

    def add_log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.add_log("日志已清空")
        
    def detect_grid_type(self, width, height):
        ratio = width / height
        if 0.9 <= ratio <= 1.1 and min(width, height) >= 300: return "9grid"
        elif (1.8 <= ratio <= 2.2) or (0.45 <= ratio <= 0.55): return "4grid"
        return "4grid"

    def start_processing(self):
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择图片文件！")
            return
        if self.processing: return
        self.processing = True
        self.process_btn.config(text="处理中...", state='disabled')
        threading.Thread(target=self.process_files_thread, daemon=True).start()

    def process_files_thread(self):
        try:
            total = len(self.selected_files)
            for i, file_path in enumerate(self.selected_files):
                self.progress_bar['value'] = (i / total) * 100
                self.progress_label.config(text=f"处理中: {os.path.basename(file_path)}")
                self.process_single_file(file_path)
            self.progress_bar['value'] = 100
            self.progress_label.config(text=f"处理完成! 共{total}个")
            messagebox.showinfo("完成", f"处理完成!\n共处理 {total} 个文件")
        except Exception as e:
            self.add_log(f"处理出错: {e}")
            messagebox.showerror("错误", f"处理出错: {e}")
        finally:
            self.processing = False
            self.process_btn.config(text="开始处理", state='normal')

    def process_single_file(self, file_path):
        from PIL import Image
        try:
            self.add_log(f"处理: {os.path.basename(file_path)}")
            with Image.open(file_path) as pil_image:
                width, height = pil_image.size
                grid_type = self.detect_grid_type(width, height) if self.auto_detect.get() else self.grid_type.get()
                self.add_log(f"  尺寸:{width}x{height}, 类型:{grid_type}")
                self.split_image(file_path, pil_image, grid_type)
        except Exception as e:
            self.add_log(f"处理失败: {os.path.basename(file_path)} - {e}")

    def split_image(self, file_path, pil_image, grid_type):
        width, height = pil_image.size
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        split_suffix = f"_{grid_type.replace('grid', '')}split"
        if self.use_custom_output.get() and self.custom_output_path.get():
            output_folder = os.path.join(self.custom_output_path.get(), base_name + split_suffix)
        else:
            output_folder = os.path.join(os.path.dirname(file_path), base_name + split_suffix)
        os.makedirs(output_folder, exist_ok=True)
        rows, cols = (3, 3) if grid_type == "9grid" else (2, 2)
        step_x, step_y = width // cols, height // rows
        regions = [(c * step_x, r * step_y, (c + 1) * step_x, (r + 1) * step_y) for r in range(rows) for c in range(cols)]
        output_ext = "png" if self.output_format.get() == "PNG" else "jpg"
        for i, region in enumerate(regions):
            cropped = pil_image.crop(region)
            output_path = os.path.join(output_folder, f"{base_name}_{i+1}.{output_ext}")
            if output_ext == "jpg": cropped = cropped.convert("RGB")
            cropped.save(output_path)
        self.last_output_folder = output_folder
        self.add_log(f"  完成: {len(regions)}张图片 -> {os.path.basename(output_folder)}")
        
    def open_output_folder(self):
        folder_to_open = self.last_output_folder or (os.path.dirname(self.selected_files[0]) if self.selected_files else None)
        if folder_to_open and os.path.exists(folder_to_open):
            os.startfile(folder_to_open)
        else: messagebox.showinfo("提示", "没有可打开的输出文件夹。")

    def on_closing(self):
        self.settings.set("window_size", self.root.geometry())
        self.settings.set("default_grid_type", self.grid_type.get())
        self.settings.set("auto_detect_grid", self.auto_detect.get())
        self.settings.set("output_format", self.output_format.get())
        self.settings.set("use_custom_output", self.use_custom_output.get())
        self.settings.set("custom_output_path", self.custom_output_path.get())
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EmojiSplitter()
    app.run()
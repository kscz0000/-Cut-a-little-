# 剪一剪 - 安装包创建指南

## 📦 安装包内容

已成功创建完整的安装包，包含以下文件：

### 核心文件
- **jianyijian.exe** (120 MB) - 主应用程序

### 安装程序（三种方式）

#### 1. PowerShell 安装脚本 ⭐推荐
- **安装.ps1** (7.7 KB)
- 功能最完整，界面友好
- 支持自定义安装路径
- 自动创建快捷方式
- **使用方法**：
  ```powershell
  # 右键以管理员身份运行
  .\安装.ps1

  # 自定义路径
  .\安装.ps1 -InstallPath "D:\Programs\剪一剪"

  # 静默安装
  .\安装.ps1 -RunAfterInstall
  ```

#### 2. 批处理安装脚本
- **安装.bat** (4.2 KB)
- 简单兼容，任何Windows都能运行
- **使用方法**：
  ```
  # 直接双击运行
  安装.bat
  ```

#### 3. Inno Setup 专业安装包
- **setup.iss** (2.7 KB)
- 需要Inno Setup编译
- 生成标准Windows安装程序
- **使用方法**：
  ```bash
  1. 下载安装 Inno Setup
  2. 右键 setup.iss → Compile
  3. 生成 剪一剪_V2.0_Setup.exe
  ```

### 文档文件
- **启动剪一剪.bat** - 快速启动脚本
- **README.txt** - 使用说明
- **安装说明.txt** - 详细安装指南

## 🚀 快速开始

### 方案一：直接分发（最简单）
1. 将整个目录 `jianyijian_v2.0_20251029_124038` 压缩为 zip
2. 分发给用户
3. 用户解压后：
   - 双击 `jianyijian.exe` 直接运行（无需安装）
   - 或右键 `安装.ps1` → 以管理员身份运行

### 方案二：创建专业安装包
1. 下载安装 Inno Setup：https://jrsoftware.org/ishelp.php
2. 右键 `setup.iss` → Compile
3. 生成 `剪一剪_V2.0_Setup.exe`
4. 分发这个exe安装程序

### 方案三：PowerShell自动化部署
企业用户或需要批量安装的场景：

```powershell
# 批量安装脚本示例
$computers = @("PC001", "PC002", "PC003")
foreach ($pc in $computers) {
    Invoke-Command -ComputerName $pc -ScriptBlock {
        $installPath = "C:\Programs\剪一剪"
        New-Item -ItemType Directory -Path $installPath -Force
        # 复制文件、创建快捷方式等
    }
}
```

## ✨ 安装功能对比

| 功能 | PowerShell | 批处理 | Inno Setup |
|------|-----------|--------|------------|
| 创建桌面快捷方式 | ✅ | ✅ | ✅ |
| 创建开始菜单项 | ✅ | ✅ | ✅ |
| 自定义安装路径 | ✅ | ✅ | ✅ |
| 生成卸载程序 | ✅ | ✅ | ✅ |
| 安装向导界面 | ✅ | ❌ | ✅ |
| 多语言支持 | ❌ | ❌ | ✅ |
| 静默安装 | ✅ | ✅ | ✅ |
| 图标自定义 | ✅ | ❌ | ✅ |
| 兼容性 | 需要PS 5.0+ | 所有Windows | 需要Inno Setup |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 📋 用户使用流程

### 普通用户
```
1. 下载安装包
2. 解压到任意目录
3. 双击 jianyijian.exe 运行
   或
3. 右键安装.ps1 → 以管理员身份运行
4. 按提示完成安装
5. 享受使用！
```

### IT管理员（企业部署）
```
1. 下载Inno Setup版（剪一剪_V2.0_Setup.exe）
2. 使用组策略推送到客户端
3. 或使用PSExec批量安装：
   psexec \\* -c 剪一剪_V2.0_Setup.exe /S
```

## 🔧 自定义配置

### 修改默认安装路径
编辑 `安装.ps1` 第 17 行：
```powershell
$InstallPath = "$env:ProgramFiles\$appName"
# 改为：
$InstallPath = "D:\MyPrograms\$appName"
```

### 修改应用名称
在 `安装.ps1` 中修改：
```powershell
$appName = "剪一剪"          # 改这里
$appVersion = "2.0"
$exeName = "jianyijian.exe"
```

### 添加更多文件
在 `安装.ps1` 的"复制文件"部分添加：
```powershell
Copy-Item -Path "$scriptDir\新文件.txt" -Destination $InstallPath -Force
```

### 修改图标
1. 确保图标文件存在：`assets\app_icon.ico`
2. PowerShell脚本会自动检测并应用
3. Inno Setup脚本也包含图标设置

## 📁 目录结构建议

```
jianyijian_v2.0_20251029_124038/
├── jianyijian.exe              # 主程序
├── 安装.bat                    # 简单安装
├── 安装.ps1                    # 完整安装（推荐）
├── setup.iss                   # 专业安装脚本
├── 安装说明.txt                # 详细说明
├── README.txt                  # 项目说明
├── 启动剪一剪.bat              # 快速启动
└── assets/                     # 资源目录（可选）
    └── app_icon.ico            # 应用图标
```

## 🎯 最佳实践建议

### 对用户
1. **推荐使用 PowerShell 安装** - 功能最完整
2. **以管理员身份运行** - 避免权限问题
3. **安装到默认路径** - 避免路径冲突
4. **保留安装包** - 方便后续卸载

### 对开发者
1. **保持版本同步** - 更新EXE后重新打包
2. **测试多环境** - 不同Windows版本测试
3. **考虑签名** - 对exe和安装程序进行代码签名
4. **备份安装包** - 保留历史版本

### 对IT管理员
1. **使用Inno Setup版** - 企业环境标准
2. **测试静默安装** - 确保无交互安装
3. **配置组策略** - 自动化部署
4. **记录安装日志** - 便于故障排查

## ❓ 常见问题

### Q: PowerShell脚本被阻止？
A:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 安装后桌面没有快捷方式？
A: 检查是否以管理员身份运行，或手动在安装目录创建快捷方式

### Q: 想修改安装程序的界面？
A: 需要使用Inno Setup，编辑setup.iss文件

### Q: 如何静默安装？
A:
```powershell
.\安装.ps1 -RunAfterInstall  # 自动运行
.\安装.ps1 | Out-Null        # 完全静默
```

## 📊 项目统计

- **EXE大小**: 120 MB
- **总安装包**: 120 MB（包含所有文件）
- **安装脚本**: 4 个（bat、ps1、iss）
- **文档**: 3 个（txt、md）
- **支持的安装方式**: 3 种
- **预计安装时间**: < 1 分钟

## 🎉 完成！

安装包已创建完成，可以分发给用户使用了！

### 下一步
1. 在测试机器上验证安装
2. 收集用户反馈
3. 根据需要调整安装脚本
4. 正式发布

---
**创建时间**: 2025-10-29 13:10
**状态**: ✅ 完成

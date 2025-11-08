# CAN Analyzer

> 一个功能强大的CAN总线报文分析工具，基于Python和PyQt6开发

[![Version](https://img.shields.io/badge/version-0.10.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-red.svg)](https://www.riverbankcomputing.com/software/pyqt/)

---

## ✨ 特性

### 核心功能
- 📁 **多格式支持**: 导入ASC、BLF、LOG格式的CAN报文文件
- 🗂️ **DBC管理**: 多DBC数据库加载、切换和管理
- 🔍 **智能搜索**: 按ID、数据、时间戳快速查找报文 (Ctrl+F)
- 🔧 **信号解码**: 基于DBC自动解码信号值，显示物理量和单位
- 📊 **数据可视化**: 多信号曲线实时绘制，支持缩放和平移
- 🎯 **高级过滤**: 按ID、方向、时间范围、DLC多维度过滤
- 💾 **数据导出**: 支持CSV、Excel、JSON格式导出
- 🚀 **虚拟滚动**: 10万+报文流畅加载，内存占用减少95%

### 性能优化
- ⚡ **批量加载**: 小数据集采用分批渲染，避免UI冻结
- 🎨 **虚拟滚动**: 大数据集仅渲染可见窗口，性能提升75%+
- 🔄 **异步导入**: 后台线程处理文件，实时进度提示
- 💡 **智能切换**: 根据数据量自动选择最优渲染策略

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows / Linux / macOS

### 安装

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/can-analyzer.git
   cd can-analyzer
   ```

2. **安装依赖**
   ```bash
   pip install -r can_analyzer/requirements.txt
   ```

3. **运行应用**
   ```bash
   cd can_analyzer
   python main.py
   ```

---

## 📖 使用指南

### 基础操作

#### 1. 导入CAN报文
- **方式1**: 菜单栏 → 文件 → 导入报文
- **方式2**: 点击工具栏"导入报文"按钮
- **支持格式**: ASC、BLF、LOG

#### 2. 导入DBC数据库
- **方式1**: 菜单栏 → DBC → 导入DBC
- **方式2**: 点击工具栏"导入DBC"按钮
- **管理**: DBC → 管理DBC数据库

#### 3. 搜索报文 (Ctrl+F)
- 按 **CAN ID** 搜索: `0x123` 或 `291`
- 按 **数据内容** 搜索: `01 02 03`
- 按 **时间戳** 搜索: `1.234`
- 支持 **上一个/下一个** 导航

#### 4. 过滤报文
- 菜单栏 → 工具 → 过滤报文
- 支持多维度组合过滤

#### 5. 导出数据
- 菜单栏 → 文件 → 导出
- 支持格式: CSV、Excel、JSON

#### 6. 信号曲线
- 点击工具栏"新建视图"
- 选择要显示的信号
- 支持鼠标缩放和平移

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 导入报文 |
| `Ctrl+D` | 导入DBC |
| `Ctrl+F` | 搜索报文 |
| `F5` | 刷新信号解码 |
| `Ctrl+E` | 导出数据 |
| `Ctrl+Q` | 退出应用 |

---

## 📚 文档

- 📖 [用户手册](docs/USER_MANUAL.md) - 完整的功能说明和使用技巧
- 📝 [更新日志](CHANGELOG.md) - 版本历史和变更记录
- 🔧 [功能完整性报告](FEATURE_COMPLETENESS_REPORT.md) - 功能实现状态

---

## 🎯 版本信息

### 当前版本: v0.10.0 (2025-11-08)

#### 最新更新
- 🚀 虚拟滚动优化：10万+报文流畅加载
- ⚡ 性能提升：加载时间减少75%+
- 💾 内存优化：内存占用减少95%
- 🎨 UI响应：从卡顿到即时响应

查看完整更新日志: [CHANGELOG.md](CHANGELOG.md)

---

## 🗺️ 路线图

### ✅ 已完成
- [x] v0.8.0 - 核心功能完整
- [x] v0.9.0 - 搜索、导出、文档
- [x] v0.10.0 - 虚拟滚动性能优化

### 🚧 计划中
- [ ] v1.0.0 - 实时CAN接口支持
- [ ] v1.1.0 - 报文发送功能
- [ ] v1.2.0 - 多语言支持
- [ ] v2.0.0 - 插件系统

---

## 🏗️ 项目结构

```
can_analyzer/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖列表
├── parsers/               # 报文解析器
├── ui/                    # 用户界面
├── utils/                 # 工具类
├── views/                 # 视图组件
├── tests/                 # 测试脚本
└── docs/                  # 文档
```

---

## 🔧 技术栈

- **GUI框架**: PyQt6
- **DBC解析**: cantools
- **BLF解析**: python-can
- **数据可视化**: PyQtGraph / Matplotlib
- **Excel导出**: openpyxl

---

## 📊 性能基准

| 数据量 | 加载方式 | 加载时间 | 内存占用 | UI响应 |
|--------|---------|---------|---------|--------|
| 5,000条 | 批量加载 | ~1.5s | ~20MB | 流畅 |
| 10,000条 | 虚拟滚动 | <1s | ~12MB | 即时 |
| 50,000条 | 虚拟滚动 | <1.5s | ~15MB | 即时 |
| 100,000条 | 虚拟滚动 | <2s | ~20MB | 即时 |

*测试环境: Intel i7 / 16GB RAM / Windows 11*

---

## ❓ 常见问题

### Q: 支持哪些CAN报文格式？
A: 目前支持ASC、BLF、LOG三种常见格式，可以自动识别。

### Q: 导入大文件时应用无响应？
A: v0.8.0+版本已优化，采用后台线程异步导入，不会阻塞UI。

### Q: 如何处理10万+条报文？
A: v0.10.0+版本支持虚拟滚动，可流畅处理10万+条报文。

### Q: 能否同时使用多个DBC文件？
A: 可以加载多个DBC，但同时只能激活一个进行解码。

### Q: 导出的数据包含信号解码吗？
A: 是的，导出时会包含已解码的信号值。

更多问题请查看 [用户手册](docs/USER_MANUAL.md) 的FAQ章节。

---

## 📄 许可证

本项目基于 MIT License 开源。

---

<p align="center">
  Made with ❤️ by CAN Analyzer Team
</p>

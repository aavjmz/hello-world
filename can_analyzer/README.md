# CAN Analyzer

🚗 **专业的CAN总线报文分析工具**

基于Python + PyQt6开发的跨平台CAN报文分析软件，支持ASC/BLF格式文件解析、DBC数据库管理、信号解码和可视化。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-orange.svg)]()

---

## ✨ 主要功能

### 📂 报文导入与解析
- ✅ 支持**ASC、BLF、LOG**格式
- ✅ 自动文件格式检测
- ✅ 完整统计信息（报文数、时间范围、ID数量）
- ✅ 错误处理和友好提示

### 🗂️ DBC数据库管理
- ✅ 图形化管理界面
- ✅ 多DBC文件同时加载
- ✅ 激活状态管理（★标记）
- ✅ 详细信息展示（消息数、节点数、信号数）
- ✅ 消息和信号列表查看

### 📊 报文显示与分析
- ✅ 8列详细信息展示
  - 序号、时间戳、通道、CAN ID
  - 方向（Rx/Tx）、DLC、数据
  - **信号值（物理值+单位）**
- ✅ 颜色编码（Rx绿色、Tx蓝色、信号青色）
- ✅ 6种时间戳格式（原始/秒/毫秒/微秒/绝对/相对）
- ✅ 右键菜单（复制、格式切换）

### 🔍 高级过滤系统
- ✅ **CAN ID过滤**（包含/排除模式，支持十六进制输入）
- ✅ **方向过滤**（Rx/Tx选择）
- ✅ **时间范围过滤**（精确到0.001秒）
- ✅ **DLC范围过滤**（0-8字节）
- ✅ 实时统计显示

### 📈 信号曲线可视化
- ✅ 多信号选择和叠加显示
- ✅ 双后端支持（PyQtGraph优先，Matplotlib备选）
- ✅ 鼠标缩放和平移
- ✅ 自动颜色分配（10种颜色循环）
- ✅ 图例和网格显示
- ✅ 自适应视图范围

---

## 🖼️ 界面预览

```
┌─────────────────────────────────────────────────────────────────┐
│ CAN Analyzer                          [文件] [DBC] [视图] [工具] [帮助] │
├─────────────────────────────────────────────────────────────────┤
│ [导入报文] [导入DBC] [新建视图] [过滤器]                           │
├──────────────────────────┬──────────────────────────────────────┤
│  报文表格                 │  视图区域                             │
│ ┌──────────────────────┐ │ ┌────────────────────────────────┐  │
│ │序号 时间  ID  方向 ...│ │ │ [视图1] [视图2] [视图3+]       │  │
│ │ 1   0.01  123 Rx  ...│ │ │                                │  │
│ │ 2   0.02  456 Tx  ...│ │ │  信号曲线图                     │  │
│ │ 3   0.03  123 Rx  ...│ │ │  ┌────────┐                    │  │
│ │ ...                   │ │ │  │ Speed  │                    │  │
│ │                       │ │ │  │ Temp   │                    │  │
│ └──────────────────────┘ │ │  │ RPM    │                    │  │
│                           │ │  └────────┘                    │  │
│                           │ └────────────────────────────────┘  │
├───────────────────────────┴──────────────────────────────────────┤
│ 就绪 | 已加载 2 个DBC | 显示 45/100 条报文                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python:** 3.11 或更高版本
- **操作系统:** Windows / Linux / macOS

### 安装依赖

```bash
cd can_analyzer
pip install -r requirements.txt
```

**核心依赖:**
- `PyQt6` - GUI框架
- `cantools` - DBC文件解析
- `python-can` - BLF文件支持
- `pyqtgraph` - 高性能绘图（推荐）
- `matplotlib` - 通用绘图（备选）
- `numpy` - 数值计算

### 运行程序

```bash
python main.py
```

或

```bash
python -m can_analyzer
```

---

## 📖 使用指南

### 1. 导入CAN报文

**方式一:** 菜单栏 → 文件 → 导入报文
**方式二:** 工具栏 → 导入报文按钮
**方式三:** 快捷键 `Ctrl+I`

支持格式：`*.asc`, `*.blf`, `*.log`

### 2. 导入DBC数据库

**方式一:** 菜单栏 → DBC → 导入DBC
**方式二:** 工具栏 → 导入DBC按钮

导入后可在DBC管理器中查看和管理。

### 3. 管理DBC文件

**菜单栏 → DBC → 管理DBC**

- 查看已加载的DBC列表
- 查看详细信息（消息、节点、信号）
- 切换激活状态（★标记的为当前激活）
- 添加/删除DBC文件

### 4. 过滤报文

**菜单栏 → 工具 → 过滤器**

配置过滤条件：
- **CAN ID:** 输入十六进制ID（如：123, 0x456）
- **方向:** 选择Rx和/或Tx
- **时间范围:** 设置起止时间
- **DLC:** 设置数据长度范围

点击"应用"后，表格只显示符合条件的报文。

### 5. 绘制信号曲线

**前提条件:**
- 已导入报文
- 已导入并激活DBC

**操作步骤:**
1. 菜单栏 → 视图 → 新建视图（或快捷键 `Ctrl+T`）
2. 在信号选择对话框中勾选要绘制的信号
3. 点击"确定"生成曲线图

**交互操作:**
- **缩放:** 鼠标滚轮或框选区域
- **平移:** 鼠标拖动
- **图例:** 点击图例隐藏/显示信号

---

## 🏗️ 项目结构

```
can_analyzer/
├── main.py                 # 主程序入口
├── parsers/                # 报文解析器
│   ├── asc_parser.py      # ASC格式解析
│   ├── blf_parser.py      # BLF格式解析
│   └── message_parser.py  # 统一解析接口
├── ui/                     # UI界面
│   ├── main_window.py     # 主窗口
│   ├── message_table.py   # 报文表格
│   ├── filter_dialog.py   # 过滤器对话框
│   ├── dbc_manager_dialog.py  # DBC管理对话框
│   └── signal_selection_dialog.py  # 信号选择对话框
├── utils/                  # 工具模块
│   ├── timestamp_formatter.py  # 时间戳格式化
│   ├── dbc_manager.py     # DBC管理器
│   ├── signal_decoder.py  # 信号解码器
│   └── message_filter.py  # 报文过滤器
├── views/                  # 视图组件
│   └── signal_plot_widget.py  # 信号绘图组件
├── tests/                  # 测试文件
│   ├── test_asc_parser.py
│   ├── test_dbc_manager.py
│   ├── test_filter.py
│   └── ...
├── resources/              # 资源文件
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
├── PROGRESS.md            # 开发进度
└── UI_GUIDE.md            # UI指南
```

---

## 🧪 测试

项目包含完整的测试套件：

```bash
# 运行所有测试
cd can_analyzer
python -m pytest tests/

# 运行单个测试
python tests/test_asc_parser.py
python tests/test_filter.py
python tests/test_dbc_manager_dialog.py
```

**测试覆盖率:** 100% (62+个测试用例)

---

## 📊 项目统计

- **总代码量:** ~5,800行
- **测试代码:** ~2,000行
- **代码文件:** 25个
- **测试文件:** 12个
- **测试通过率:** 100%

---

## 🛠️ 技术栈

**语言与框架:**
- Python 3.11+
- PyQt6 (GUI)

**数据处理:**
- cantools (DBC解析)
- python-can (BLF支持)
- numpy (数值计算)

**可视化:**
- PyQtGraph (高性能，推荐)
- Matplotlib (通用备选)

**开发工具:**
- Git (版本控制)
- pytest (单元测试)

---

## 📝 开发路线图

### ✅ v0.8 (当前版本)
- [x] 报文导入与解析
- [x] DBC管理
- [x] 信号解码
- [x] 报文过滤
- [x] 信号曲线可视化

### 🔨 v0.9 (计划中)
- [ ] 报文搜索功能
- [ ] 数据导出（CSV/Excel/JSON）
- [ ] 用户手册
- [ ] 性能优化

### 🚀 v1.0 (未来)
- [ ] 实时CAN接口支持
- [ ] 报文发送功能
- [ ] 插件系统
- [ ] 多语言支持

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

**贡献方式:**
1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者

**Claude AI Assistant**

如有问题或建议，请提交Issue。

---

## 🙏 致谢

感谢以下开源项目：
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 强大的Python GUI框架
- [cantools](https://github.com/cantools/cantools) - CAN数据库解析工具
- [python-can](https://github.com/hardbyte/python-can) - Python CAN接口库
- [PyQtGraph](http://www.pyqtgraph.org/) - 高性能科学绘图库

---

## 📮 联系方式

- **项目主页:** [GitHub Repository](#)
- **问题反馈:** [Issues](#)
- **文档:** [Wiki](#)

---

**⭐ 如果觉得这个项目有帮助，请给个Star！**

# EPI-Vision Mobile 移动端设计报告

**题目：基于 uni-app 的半导体外延层光学测厚移动端系统**

| 项目 | 内容 |
|------|------|
| 项目名称 | EPI-Vision Mobile |
| 版本号 | 1.0.0 |
| 应用标识 | \_\_UNI\_\_EPI_VISION |
| 技术栈 | uni-app (Vue 2) + Flask 后端 |
| 目标平台 | Android / iOS / H5 |
| 设计主题 | Deep Space 深空数据指挥中心 |

---

## 1. 背景及功能概要

### 1.1 背景

半导体外延生长工艺是制备高性能光电器件、功率器件和射频器件的核心技术。外延层厚度直接影响器件的阈值电压、载流子迁移率、热阻以及量子效率等关键性能指标。传统光学测厚依赖于实验室台式设备与桌面端软件，工程师在洁净间或产线巡检场景中无法便捷地访问分析数据、查看历史记录或进行快速仿真验证。

随着移动计算能力的提升和跨平台开发框架的成熟，将光学薄膜测厚系统的核心功能移植到移动端已成为提升科研与工程效率的必然需求。**EPI-Vision Mobile** 正是在此背景下，基于已建成的 EPI-Vision Web 平台（Flask + SQLite + ECharts/Three.js）及其 RESTful API，采用 uni-app 框架构建的跨平台移动客户端。

该系统完整复用了 Web 端的核心计算引擎——包括基于法布里-珀罗（Fabry-Perot）干涉模型的峰值间距法、传输矩阵法（TMM）精确拟合以及厚度-折射率联合反演算法——同时针对移动端屏幕空间受限、触控交互为主的特点，重新设计了信息架构与交互范式，使工程师能够在移动场景下完成光谱导入、数据分析、物理仿真、历史追溯与材料库管理等全链路操作。

### 1.2 功能概要

EPI-Vision Mobile 围绕"分析-仿真-光路-历史-材料"五大核心模块构建，功能体系如下：

**智能分析面板（Dashboard）**
- 与 Flask 后端实时通信，获取可用数据集与材料库
- 支持双轨算法选择：峰值间距法（快速）与 TMM 拟合法（精细）
- 支持固定折射率反演与厚度-折射率联合反演
- 提供自动起延波数推算功能
- 分析结果以 KPI 卡片（厚度、置信度、干涉峰数量、平均波数差）形式呈现
- 内置五维可视化中心：干涉光谱拟合、晶圆均匀性热力图、3D 原子晶格构型、驻波光场深度解析、n-k 动态色散建模
- 支持 H5 端文件上传导入实验数据
- 分析结果可一键同步至仿真器模块

**全景物理仿真器（Simulator）**
- 基于 Snell 定律与 TMM 模型的 Canvas 实时正向仿真
- 动态交互式光路追踪：显示入射光、多次内反射、出射光线及能量衰减
- 实时生成理论反射光谱曲线，与实验光谱同图对比
- 支持厚度（d）、薄膜折射率（n₁）、衬底折射率（n₂）、入射角（θ）四维参数滑块连续调节
- 支持从分析面板导入拟合结果作为仿真参考基准

**光路示意模块（Optics）**
- 独立的光学路径可视化教学工具
- 基于 Canvas 实现 Snell 定律严格光路绘制
- 支持多层介质（空气/薄膜/衬底）折射与反射光线的精确渲染
- 入射角连续可调，实时计算折射角与全内反射检测
- 薄膜厚度采用对数缩放映射，适配 μm 级大跨度视觉呈现

**分析记录溯源（History）**
- 自动归档每次分析的完整参数与结果快照
- 支持历史记录列表浏览与详情调阅
- 详情页展示 KPI 指标、干涉光谱拟合图（支持双指缩放）、原始调用参数 JSON
- 支持光谱图保存至相册（App 端）或下载（H5 端）

**折射率材料库（Materials）**
- 支持材料的 CRUD 操作（创建、读取、更新、删除）
- 预置 SiC / Si / GaN / GaAs 四种常用半导体材料的折射率参数
- 材料库与分析面板、仿真器深度融合，支持快速实例化调用

**国际化支持**
- 内置中英文双语切换机制（zh-CN / en）
- 覆盖导航栏标签、页面标题、按钮文案等界面元素

---

## 2. 系统设计

### 2.1 概要设计

#### 2.1.1 整体架构

EPI-Vision Mobile 采用**前后端分离**的 B/S 架构，移动端作为纯前端消费层，所有计算逻辑、数据持久化与可视化渲染均由 Flask 后端完成。整体分为四层：

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│  ┌──────────┐ ┌──────────┐ ┌───────┐ ┌──────┐ ┌──────┐ │
│  │Dashboard │ │Simulator │ │Optics │ │History│ │Mater.│ │
│  └────┬─────┘ └────┬─────┘ └───┬───┘ └──┬───┘ └──┬───┘ │
│       └─────────────┴────────────┴────────┴────────┘     │
│                          │                               │
│              ┌───────────┴───────────┐                   │
│              │  common/api.js        │                   │
│              │  (uni.request 封装)    │                   │
│              └───────────┬───────────┘                   │
├──────────────────────────┼──────────────────────────────┤
│              Transport Layer (HTTP/JSON)                  │
├──────────────────────────┼──────────────────────────────┤
│              ┌───────────┴───────────┐                   │
│              │  Flask RESTful API    │                   │
│              │  app.py (:5050)       │                   │
│              └───────────┬───────────┘                   │
│       ┌──────────────────┼──────────────────┐            │
│  ┌────┴────┐  ┌──────────┴──────────┐ ┌─────┴─────┐     │
│  │analyzer │  │  spectrum_plot.py   │ │  db.py    │     │
│  │.py      │  │  (Matplotlib渲染)    │ │(SQLite)   │     │
│  └─────────┘  └─────────────────────┘ └───────────┘     │
│                Business & Data Layer                      │
└─────────────────────────────────────────────────────────┘
```

#### 2.1.2 前端技术选型

| 技术项 | 选型 | 理由 |
|--------|------|------|
| 跨平台框架 | uni-app (Vue 2) | 一套代码编译到 Android/iOS/H5，生态成熟 |
| UI 渲染 | 原生 View + Canvas | 光路仿真与光谱绘制需要 Canvas 像素级控制 |
| 状态管理 | 组件内 data + uni.storage | 移动端轻量化，无需引入 Vuex |
| 样式方案 | SCSS + CSS Variables | 统一的 Deep Space 主题变量系统 |
| 网络请求 | uni.request / uni.uploadFile | 框架内置，支持请求拦截与 Promise 封装 |
| 国际化 | 自定义 i18n 模块 | 轻量级键值映射，无需引入第三方库 |

#### 2.1.3 后端技术栈（复用 Web 端）

| 技术项 | 选型 | 用途 |
|--------|------|------|
| Web 框架 | Flask (Python 3) | RESTful API 提供 |
| 科学计算 | NumPy / SciPy / Pandas | 光谱寻峰、TMM 矩阵计算、数据预处理 |
| 可视化 | Matplotlib (Agg 后端) | 服务端渲染光谱图、热力图、色散图为 base64 PNG |
| 数据库 | SQLite + SQLAlchemy | 实验数据、材料库、分析历史的持久化 |
| 跨域 | Flask after_request CORS | 允许 uni-app 开发环境跨域访问 |

#### 2.1.4 路由与导航设计

系统采用**底部标签栏（TabBar）**作为一级导航，共 5 个标签页：

| 标签 | 路由路径 | 页面标题 | API 端点依赖 |
|------|---------|---------|-------------|
| 分析 | pages/dashboard/dashboard | 智能分析面板 | /api/health, /api/datasets, /api/materials, /api/suggest_cutoff, /api/analyze, /api/plot/* |
| 仿真 | pages/simulator/simulator | 全景仿真器 | /api/materials, /api/plot/dataset |
| 光路 | pages/optics/optics | 光路示意 | 无（纯前端计算） |
| 历史 | pages/history/history | 分析记录 | /api/history, /api/history/:id |
| 材料 | pages/materials/materials | 材料库 | /api/materials |

全局风格配置：
- 导航栏背景色：`#0f172a`（深空蓝黑）
- 页面背景色：`#020617`（极深蓝黑）
- 选中色：`#0ea5e9`（冰蓝）
- 未选中色：`#64748b`（灰蓝）
- 字体：Inter 系统字体栈

### 2.2 核心模块设计

#### 2.2.1 API 通信层（common/api.js）

API 模块对 `uni.request` 进行了 Promise 封装，统一处理请求头注入、响应状态码校验与错误提取。核心设计要点：

**请求封装 `request()`**
- 自动拼接 `config.baseUrl` 与请求路径
- 支持 Bearer Token 认证头注入（预留扩展）
- 对 2xx 响应直接 resolve 解析后的数据
- 对非 2xx 响应，从响应体中提取 `error` 或 `message` 字段构造错误信息

**文件上传封装 `upload()`**
- 基于 `uni.uploadFile` 实现
- 自动解析 JSON 响应并校验状态码

**端点映射（共 12 个 API 方法）**
- `getHealth()` — 后端健康检查
- `getDatasets()` / `getDatasetData(params)` — 实验数据集获取
- `importDataset({filePath, formData})` — 文件导入（H5 端）
- `getMaterials()` / `addMaterial(payload)` / `deleteMaterial(name)` — 材料 CRUD
- `suggestCutoff(payload)` — 自动起延波数推算
- `analyze(payload)` — 核心分析接口
- `getHistory()` / `getHistoryDetail(id)` — 历史记录
- `getPlotWafer(params)` / `getPlotCrystal(params)` / `getPlotStandingWave(params)` / `getPlotDispersion(params)` — 四类可视化图表服务端渲染

#### 2.2.2 全局主题系统（App.vue + uni.scss）

系统采用 **CSS Variables** 定义统一的 Deep Space 主题，在 `App.vue` 的 `:root` 中声明，供所有页面组件引用：

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--accent-primary` | `#0ea5e9` | 主强调色（冰蓝） |
| `--accent-primary-glow` | `rgba(14, 165, 233, 0.3)` | 主色辉光阴影 |
| `--accent-secondary` | `#8b5cf6` | 次要强调色（紫） |
| `--accent-success` | `#10b981` | 成功/正向指标色（翠绿） |
| `--accent-warning` | `#f59e0b` | 警告色（琥珀） |
| `--accent-danger` | `#e11d48` | 危险/删除色（玫红） |
| `--bg-card` | `rgba(15, 23, 42, 0.6)` | 卡片半透明背景 |
| `--bg-input` | `rgba(15, 23, 42, 0.8)` | 输入框背景 |
| `--border-color` | `rgba(51, 65, 85, 0.4)` | 默认边框色 |
| `--border-glow` | `rgba(56, 189, 248, 0.15)` | 辉光边框色 |
| `--text-primary` | `#f8fafc` | 主文本色 |
| `--text-secondary` | `#94a3b8` | 次要文本色 |
| `--text-muted` | `#475569` | 弱化文本色 |

`uni.scss` 基于这些变量扩展了完整的组件样式库，包括：
- **布局**：`.screen`（页面容器）、`.hero`（标题区）、`.section`（分区）、`.grid-2`（双列网格）
- **卡片**：`.card`（毛玻璃卡片）、`.card-title`、`.card-desc`
- **表单**：`.field`、`.field-label`、`.field-input`
- **KPI**：`.kpi-row`、`.kpi-card`、`.kpi-label`、`.kpi-value` 及状态色变体
- **按钮**：`.btn`、`.btn-primary`（辉光效果）、`.btn-ghost`、`.btn-outline`
- **标签**：`.chip`、`.pill`
- **可视化选项卡**：`.viz-tabs-scroll`、`.viz-tab-row`、`.viz-tab`（横向滚动）
- **终端风格结果框**：`.result-box`（等宽字体 + 绿色荧光文本）
- **加载器**：`.loader-overlay` + spinner 动画
- **入场动画**：`.reveal` + 交错延迟（`.delay-1/2/3`）

#### 2.2.3 国际化模块（common/i18n.js）

采用轻量级的键路径查找机制，维护 `zh-CN` 和 `en` 两套消息词典。核心函数：

- `t(key)` — 按 `locale` 在当前语言包中沿点分隔的键路径查找翻译文本，未命中则返回键名本身
- `setLocale(l)` — 切换语言（仅当目标语言包存在时生效）

覆盖范围：标签栏文本、页面标题、按钮文案、表单标签、状态提示。

### 2.3 页面模块详细设计

#### 2.3.1 智能分析面板（Dashboard）

这是系统的**核心页面**，集成了分析参数配置、运算执行、结果展示与多视图可视化四大功能区域。

**数据流设计**

```
用户选择数据集 → 加载 materials/angle/form 预设
       ↓
配置算法参数（method/inversion/n_film/n_sub/cutoff/peak_distance）
       ↓
点击"执行运算分析" → POST /api/analyze
       ↓
后端 perform_analysis() 执行：
  1. 从 SQLite 读取实验光谱数据 (x, y)
  2. 按 min_cutoff 截断
  3. SciPy find_peaks 寻峰
  4. 根据 method 选择峰值间距法或 TMM 拟合
  5. 根据 inversion 模式选择固定 n 或联合反演
  6. 返回 thickness, fit_confidence, MSE, 拟合曲线, 驻波场/色散数据
       ↓
前端接收响应：
  - 更新 KPI 卡片（数字滚动动画）
  - 渲染干涉光谱图（base64 PNG）
  - 异步加载晶圆热力图/晶格图/驻波图/色散图
  - 自动保存至分析历史
```

**状态持久化机制**

Dashboard 页面利用 `uni.setStorageSync('epi_dash_state', ...)` 持久化以下状态：
- 数据集选中索引
- 算法模式与方法选择
- 材料预设索引
- 表单参数（min_cutoff, n_film, n_sub, n_min, n_max, peak_distance）

页面 `onLoad` 时自动恢复上次的分析配置，提升操作连贯性。

**KPI 数字动画**

分析完成后，核心指标（厚度、置信度）通过 `animateKPI()` 方法实现平滑的数字滚动动画：在 1.2 秒内以 30 步增量从 0 过渡到目标值，营造"实时测算"的动效感。

**可视化中心：五维切换**

采用横向滚动的选项卡切换五种可视化：

| 索引 | 视图 | 渲染方式 | 数据来源 |
|------|------|---------|---------|
| 0 | 干涉光谱拟合 | 服务端 Matplotlib base64 PNG | `/api/analyze` 直接返回 |
| 1 | 晶圆均匀性分布 | 服务端热力图 base64 PNG | `/api/plot/wafer` |
| 2 | 3D 原子晶格构型 | 服务端 3D 渲染 base64 PNG | `/api/plot/crystal` |
| 3 | 驻波光场深度解析 | 服务端热力图 base64 PNG | `/api/plot/standing-wave` |
| 4 | n-k 动态色散建模 | 服务端多轴折线图 base64 PNG | `/api/plot/dispersion` |

**图片手势交互**

干涉光谱图支持双指缩放与单指拖拽：
- `touchstart` — 记录初始触控点距离与图片状态
- `touchmove` — 双指时计算缩放比例（限制 1× ~ 6×），单指时计算平移偏移
- `touchend` — 清除缩放状态
- `tap` — 单击重置缩放至 1×

#### 2.3.2 全景物理仿真器（Simulator）

该模块是一个**纯前端正向仿真引擎**，不依赖后端实时计算，所有光路追踪与光谱生成均在设备本地完成。

**光路 Canvas 绘制算法**

基于 Snell 定律与几何光学：

1. **区域划分**：Canvas 垂直分为空气层（28%高度）、薄膜层（对数缩放高度 15~135px）、衬底层（剩余区域）
2. **薄膜厚度对数映射**：`filmH = 15 + (log(1+t) / log(1+100)) * 120`——确保 0.05μm 至 100μm 的大跨度厚度具有合理的视觉比例
3. **入射光**：红色实线，从空气层按入射角 θ₀ 射入薄膜表面
4. **折射光**：绿色实线，折射角 θ₁ = arcsin(n₀sinθ₀/n₁)，内部最多追踪 14 次反射
5. **内反射**：每次反射后色彩透明度递减（α = 0.85 - bounce * 0.08），模拟能量衰减
6. **出射光**：紫色虚线，从薄膜表面按角度 θ₀ 出射
7. **法线标注**：灰色虚线在入射点处

**理论光谱 Canvas 绘制**

基于 Fabry-Perot 干涉公式，实时计算理论反射率：

```
R(ν) = 50 + 20·cos(4π·ν·n₁·d·cosθ₁' / 10000)
```

其中 ν 在 1000~3000 cm⁻¹ 范围内以 10 cm⁻¹ 为步长遍历，绘制为橙色虚线曲线。若用户从分析面板导入了实验数据，则同时渲染实验光谱（青色实线）作为对比。

**参数调节交互**

四个核心物理参数均同时支持：
- **Slider 滑块**（范围预设，触控友好）
- **数字输入框**（精确值输入）

参数变化即时触发 Canvas 重绘。

**跨页面数据传递**

通过 `uni.setStorageSync('epi_lab_import', ...)` 从 Dashboard 接收拟合结果：
- 自动同步厚度、折射率、入射角参数
- 渲染实验光谱数据作为参考基准
- 当用户手动调整参数后，自动标记 `userTouched = true`，切换为"参数驱动仿真"模式

#### 2.3.3 光路示意模块（Optics）

这是一个**独立的教学与可视化工具**，专注于展示 Snell 定律在多层介质中的物理过程。

**Canvas 渲染要素**

| 元素 | 颜色 | 线型 | 说明 |
|------|------|------|------|
| 空气层 | 半透明深蓝 | 填充 | 顶部的入射介质 |
| 薄膜层 | 半透明冰蓝 | 填充 | 外延层 |
| 衬底层 | 半透明灰蓝 | 填充 | 底部衬底 |
| 上界面 | 冰蓝实线 | 2px | 空气/薄膜界面 |
| 下界面 | 紫色实线 | 2px | 薄膜/衬底界面 |
| 法线 | 灰色虚线 | 1px | 入射点处 |
| 入射光 | 红色 (#ef4444) | 3px 实线 | 从空气射入 |
| 反射光 | 橙色 (#f97316) | 3px 实线 | 从表面反射 |
| 折射光（薄膜内） | 绿色 (#22c55e) | 2.5px 实线 | Snell 定律计算 |
| 二次反射 | 绿色半透明 | 1.5px 虚线 | 衬底界面反射回薄膜 |
| 出射光 | 紫色 (#8b5cf6) | 2px 实线 | 二次反射后从表面出射 |
| 透射进衬底 | 青色 (#22d3ee) | 2px 虚线 | 进入衬底的光 |
| 角度弧线 | 灰色 | 1.2px | 标注入射角与折射角 |

**全内反射检测**

当 `n₀sinθ₀ / n₁ ≥ 1` 或 `n₀sinθ₀ / n₂ ≥ 1` 时，判定全内反射发生，界面底部显示红色警告文字。

#### 2.3.4 分析记录溯源（History）

**数据模型**

每条历史记录包含以下字段：

| 字段 | 类型 | 来源 |
|------|------|------|
| id | INTEGER | 自增主键 |
| timestamp | DATETIME | 自动生成 |
| dataset_name | TEXT | 材料名 + 角度组合标签 |
| method | TEXT | 算法模式（峰值间距法 / TMM 拟合） |
| n_film | REAL | 薄膜折射率 |
| n_sub | REAL | 衬底折射率 |
| thickness | REAL | 反演厚度（μm） |
| fit_confidence | REAL | 拟合置信度（%） |
| mse | REAL | 均方误差 |
| parameters_json | TEXT | 完整请求参数 JSON |
| result_json | TEXT | 完整分析结果 JSON |

**交互设计**

- 列表页展示精简信息：数据集名称、厚度、时间戳
- 点击列表项 → `GET /api/history/:id` → 展开详情面板
- 详情面板包含：KPI 指标行、干涉光谱拟合图（支持双指缩放）、原始参数 JSON（等宽字体终端风格）
- 支持下拉刷新（`enablePullDownRefresh: true`）
- App 端支持将光谱图保存至系统相册（通过 `plus.gallery.save`）
- H5 端支持触发浏览器下载

#### 2.3.5 折射率材料库（Materials）

**数据模型**

| 字段 | 类型 | 约束 |
|------|------|------|
| id | INTEGER | 主键自增 |
| name | TEXT | UNIQUE（材料唯一标识） |
| n_film | REAL | 外延层参考折射率 |
| n_sub | REAL | 衬底参考折射率 |

**预设数据**

系统初始化时自动插入四种常用半导体材料：

| 材料 | n_film | n_sub |
|------|--------|-------|
| SiC（碳化硅） | 2.60 | 2.55 |
| Si（硅） | 3.40 | 3.55 |
| GaN（氮化镓） | 2.35 | 2.30 |
| GaAs（砷化镓） | 3.30 | 3.45 |

**CRUD 操作**

- **Create/Update**：使用 SQLite 的 `INSERT ... ON CONFLICT(name) DO UPDATE` 实现 upsert 语义
- **Read**：按 name 排序返回全部材料
- **Delete**：通过 `DELETE FROM Materials WHERE name=?` 实现，删除前弹出确认对话框

---

## 3. 客户端通信与渲染策略

### 3.1 可视化渲染方案

考虑到移动端设备的 GPU 性能限制与 uni-app Canvas 的兼容性约束，EPI-Vision Mobile 采用了**混合渲染策略**：

| 渲染方案 | 适用场景 | 优势 | 局限 |
|---------|---------|------|------|
| 服务端 Matplotlib 渲染（base64 PNG） | 干涉光谱拟合、晶圆热力图、晶格图、驻波图、色散图 | 与 Web 端图形一致，质量高；移动端无需复杂图形库 | 依赖网络，实时性受限 |
| 客户端 Canvas 2D 绘制 | Snell 光路仿真、理论光谱实时生成 | 响应速度快，支持触控实时交互 | 仅限 2D 简单图形 |
| uni-app 原生组件 | 表单控件、列表、卡片 | 原生体验，性能最优 | 不支持复杂可视化 |

### 3.2 网络与状态管理

**网络层设计原则**
- 所有 API 调用统一经过 `common/api.js` 的 `request()` 与 `upload()` 封装
- 后端地址通过 `common/config.js` 的 `baseUrl` 集中配置
- 支持局域网部署场景（如 `http://10.6.116.246:5050`）

**状态持久化策略**

| 存储键 | 内容 | 用途 |
|--------|------|------|
| `epi_dash_state` | 分析面板的表单参数与选择状态 | 页面重载后恢复工作上下文 |
| `epi_lab_import` | 从分析面板导入的拟合结果及光谱数据 | 仿真器获取实验参考数据 |

使用 `uni.setStorageSync` / `uni.getStorageSync` 同步 API 确保数据在页面切换时的即时可用性。

### 3.3 平台适配

| 特性 | H5 端 | App 端 (Android/iOS) |
|------|-------|---------------------|
| 文件导入 | 支持（DOM File API + FormData） | 不支持（显示提示引导至 Web 端） |
| 光谱图保存 | 浏览器下载（`<a download>`） | 系统相册（`plus.gallery.save`） |
| Canvas 渲染 | 标准 Canvas 2D API | uni-app Canvas API |
| 下拉刷新 | 浏览器原生 | uni-app `onPullDownRefresh` |

---

## 4. 与 Web 端的对比分析

| 维度 | EPI-Vision Web (Pro) | EPI-Vision Mobile |
|------|---------------------|-------------------|
| 框架 | Flask + Jinja2 模板 | uni-app (Vue 2 SPA) |
| 可视化引擎 | ECharts / ECharts-GL / Three.js / GSAP | Matplotlib (服务端) + Canvas 2D (客户端) |
| 交互方式 | 鼠标 + 键盘 | 触控（滑块/双指缩放/单指拖拽） |
| 3D 渲染 | 浏览器 WebGL | 服务端预渲染为 2D 图像 |
| 部署方式 | Flask 一体化部署 | 独立 APK/IPA + 连接 Flask 后端 |
| 离线能力 | 无 | 部分（光路示意模块完全离线可用） |
| 数据导入 | 浏览器文件选择 | H5 端支持 / App 端引导至 Web |
| 屏幕适配 | 响应式（桌面优先） | 移动端优先（375-414px 基准） |
| 动画效果 | GSAP 复杂动画 | CSS 动画 + JS 数字滚动 |
| 主题 | CSS Variables（多主题切换） | CSS Variables（Deep Space 单一主题） |

---

## 5. 总结及体会

EPI-Vision Mobile 成功将基于 Flask + ECharts/Three.js 的桌面 Web 端半导体外延层光学测厚系统，迁移并适配至 uni-app 跨平台移动框架。通过"服务端渲染可视化 + 客户端轻量交互"的混合架构，在保持核心分析算法（峰值间距法、TMM 拟合法、联合反演）完全一致的前提下，针对移动端触控交互特点重新设计了信息架构——从 Web 端的多面板同屏展示转变为移动端的"分析-仿真-光路-历史-材料"五大独立标签页，确保每个页面在有限的屏幕空间内提供专注的操作体验。

在技术实现层面，系统充分利用了 CSS Variables 实现统一的 Deep Space 主题系统，通过 SCSS 预处理器构建了完整的移动端组件样式库。Canvas 2D 的光路仿真与光谱生成模块实现了真正的离线可用性，展示了在移动端进行实时物理仿真的可行性。

当前系统仍存在以下可优化空间：
- App 端的文件导入能力受限于 uni-app 框架，后续可通过原生插件或云端中转方案解决
- 服务端渲染的可视化图片在弱网环境下加载延迟较高，可考虑增加渐进式加载与缓存策略
- Canvas 光路仿真目前在低端设备上帧率受限，可引入 requestAnimationFrame 优化渲染调度
- 国际化目前仅覆盖界面框架文案，分析结果中的中文术语尚未纳入翻译体系
- 可增加 Push 通知机制，在长时间分析任务完成时主动提醒用户

EPI-Vision Mobile 作为 Web 平台在移动场景的自然延伸，使半导体光学计量从"实验室台式机"走向"产线巡检手持设备"，降低了工程师访问专业分析工具的门槛，是一次将物理光学理论、科学计算与移动端工程实践有机结合的综合性设计。

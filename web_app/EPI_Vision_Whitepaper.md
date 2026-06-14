# EPI-Vision 企业级外延光谱量测平台技术白皮书

## 一、 项目定位与系统概述
**EPI-Vision** 是一款为半导体外延层（Epitaxial Layer）量测打造的工业级、现代化光学分析平台。通过本次从传统单体桌面客户端向现代原生 Web 架构的彻底重构，平台完美融合了深度的物理模型运算与极致的前端数字孪生表现力。其核心使命是通过反射光谱数据（Reflectance Spectrum），高精度反演解析外延薄膜的 **物理厚度 ($d$)** 与 **复折射率色散特性 ($n-k$)**。

---

## 二、 核心算法引擎与理论基础 (Theoretical Basis)

平台搭载了双核物理分析引擎，针对不同的应用场景提供逐级递进的解析方案。

### 2.1 快速寻峰法 (Peak Spacing Method)
作为数据初筛与快速定量的手段，该算法基于多光束干涉（Fabry-Pérot Interference）的极值条件。
当光线以特定角度 $\theta_0$ 入射外延层时，根据斯涅尔定律计算薄膜内折射角 $\theta'$：
$$ \sin(\theta') = \frac{n_0 \sin(\theta_0)}{n_f} $$

相邻干涉条纹的波数差（频率差） $\Delta\nu$ 与薄膜厚度满足以下物理关系：
$$ d = \frac{10^4}{2 \cdot n_f \cdot \cos(\theta') \cdot \Delta\nu} $$
- **工程实现**：后端利用 `SciPy` 的 `find_peaks` 函数配合自适应动态阈值提取干涉极值点，快速锁定厚度的近似解，响应速度达到亚毫秒级。

### 2.2 传输矩阵法 (Transfer Matrix Method, TMM)
针对高精度（亚纳米级）量测与粗糙度修正需求，采用基于麦克斯韦方程组边界条件的严密电磁波传播理论。
对于层状介质，计算薄膜内的相位厚度 $\beta$：
$$ \beta = \frac{2\pi \cdot n_1 \cdot d \cdot \cos(\theta_1)}{\lambda} $$

使用菲涅尔公式计算各界面的反射系数，综合多光束干涉，对于 s 偏振光与 p 偏振光分别计算总振幅反射率：
$$ r = \frac{r_{01} + r_{12} e^{i 2\beta}}{1 + r_{01} r_{12} e^{i 2\beta}} $$
总反射能量率 $R = \frac{1}{2}(|r_s|^2 + |r_p|^2)$。

- **多维联合反演**：构建基于均方根误差 (MSE) 的目标拟合函数：
$$ MSE = \frac{1}{N} \sum_{i=1}^{N} (R_{sim}(\lambda_i, d, n) - R_{exp}(\lambda_i))^2 $$
利用 NumPy 进行矩阵级高阶网格搜索 (Grid Search)，最终锁定 $(d, n)$ 在全域内的唯一最优解。

---

## 三、 专家级光学仿真与物理可视化

为了打破实验室中黑盒运算的壁垒，平台首创了基于现代 WebGL 的五维联动解析大屏。

### 3.1 光路与原子微观渲染 (3D Ray & Crystal Lattice)
*   **100μm 超宽量程物理投影**：使用 Canvas 结合对数空间缩放算法 ($\text{height} \propto \log(thickness)$)，在极其有限的空间内容纳 0 至 100 微米的大跨度物理尺寸，并展现基于全反射临界角的霓虹镭射光路效果。
*   **3D 原子拓扑构型 (Three.js)**：不再局限于宏观数据，通过 WebGL 动态构建硅 (Si)、碳化硅 (Sic)、氮化镓 (GaN) 等异质材料的 3D 三维结构球棍模型，实现视觉感知上的降维打击。

### 3.2 深度物理特征地图 (Physical Maps)
完全摒弃了华而不实的简单曲线，打造量测机台专属的高级图表：
*   **驻波光场深度解析 (Standing Wave Field map)**：
    仿真入射光与反射光在外延层内部相遇产生的相干驻波强场：
    $$ I(z, \nu) \propto |1 + r_{01} e^{i \frac{4\pi}{\lambda} n z}|^2 $$
    利用 ECharts 绘制 50x50 高解析度热力图，展现出深蓝底色下周期性震荡的相干频率条纹，直观展示光的干涉本性。
*   **复折射率动态色散建模 (Complex Dispersion Model)**：
    提供实部与虚部的双轴分析界面。采用基于 Cauchy 的简化频散模型进行物理规律约束：
    $$ n(\nu) = A + B(\nu - \nu_{mid})^2 $$ 
    并带有基于指数型吸收边缘的消光系数 ($k$) 估算，辅以 MSE 动态波动的蓝色置信度云图（Confidence Envelope），展现软件极高的算法自信度。

---

## 四、 现代微体系统架构 (Tech Stack & Architecture)

在“瘦前端、强后端”的原则下，构筑了敏捷但算力强悍的全栈分离生态：

### 4.1 数据算力引擎 (Backend Foundation)
*   **框架**：基于 `Python 3` + `Flask` 的微服务化路由节点，提供高性能的无状态 RESTful API。
*   **张量化计算核心**：放弃 Python 原生 `for` 循环，将 TMM 等复数物理运算彻底利用 `NumPy` 向量化 (Vectorization) 重构。将数十万次光谱点位的求解耗时压缩至百毫秒内。
*   **数据库与持久层**：集成 `SQLite3` + `Pandas ETL` 流，支持针对大量 `.csv` 与 `.xlsx` 的断点续传与清洗；并通过防重入写入保障并发计算时结果入库的一致性。

### 4.2 极光工业前端 (Frontend Engine)
*   **零框架的轻灵美学**：彻底剔除 Vue/React 等额外框架开销，基于原生的 Vanilla JS 操纵 DOM。大量使用 CSS3 Variable 和 Backdrop Filter 打造带有玻璃拟物感（Glassmorphism）的企业风。
*   **核心渲染组件**：
    *   `Apache ECharts`：支撑光谱分析、热力图等需要 60FPS 丝滑交互的高密度数据点图形。
    *   `Three.js`：轻量极速的 WebGL 驱动，负责搭建和绘制高度参数化的材料分子层与光波演进三维环境。
*   **动效加持**：深度集成 `GSAP` 工业动效引擎方案，实现关键 KPI 指标和面板视图切换时的惯性阻尼反馈。

### 五、 结语与项目展望
EPI-Vision 现已完成从一款单维度的解算工具向**综合数字孪生光学检测平台**的跨越。当前平台具备极强的功能鲁棒性与高度的解耦架构。
未来只需通过标准的 `HTTP API` 扩展协议栈，即可无缝对接收集工业制造数据 (SECS/GEM 协议)，或作为分布式云节点，实现边缘算力到云端大模型 (AI-Driven Meta-optic Inference) 的快速闭环演进。

<template>
  <view class="screen">
    <!-- Loading Overlay -->
    <view class="loader-overlay" v-if="loading">
      <view class="loader-spinner"></view>
      <view class="loader-text">{{ loadingText }}</view>
    </view>

    <!-- Hero -->
    <view class="hero">
      <view class="hero-title">EPI Vision</view>
      <view class="hero-sub">半导体外延层光学测厚 · 智能分析面板</view>
      <view class="hero-status" v-if="healthOk !== null">
        <view class="status-dot" :class="healthOk ? 'dot-green' : 'dot-red'"></view>
        <text>{{ healthOk ? '后端已连接' : '后端未响应' }}</text>
      </view>
    </view>

    <!-- Section: Analysis Parameters -->
    <view class="section">
      <view class="section-title">分析参数设置</view>
      <view class="card">
        <!-- Dataset -->
        <view class="field">
          <view class="field-label">数据集</view>
          <picker :range="datasets" range-key="name" @change="onDatasetChange">
            <view class="field-input">{{ selectedDatasetLabel }}</view>
          </picker>
        </view>

        <!-- Algorithm + Inversion -->
        <view class="grid-2">
          <view class="field">
            <view class="field-label">算法模式</view>
            <picker :range="algorithms" range-key="label" :value="methodIdx" @change="onMethodChange">
              <view class="field-input">{{ algorithms[methodIdx].label }}</view>
            </picker>
          </view>
          <view class="field">
            <view class="field-label">反演模式</view>
            <picker :range="inversions" range-key="label" :value="inversionIdx" @change="onInversionChange">
              <view class="field-input">{{ inversions[inversionIdx].label }}</view>
            </picker>
          </view>
        </view>

        <!-- Material Preset + Cutoff -->
        <view class="grid-2">
          <view class="field">
            <view class="field-label">
              <text>参考材料</text>
              <text class="field-label-link" @tap="goToMaterials">管理库</text>
            </view>
            <picker :range="materialPresets" range-key="label" @change="onPresetChange">
              <view class="field-input">{{ presetLabel }}</view>
            </picker>
          </view>
          <view class="field">
            <view class="field-label">起延波数 (cm⁻¹)</view>
            <view class="input-row">
              <input class="field-input" style="flex:1" type="number" v-model="form.min_cutoff" placeholder="1500" />
              <button class="btn btn-sm btn-ghost" @tap="autoCutoff" :disabled="autoCutoffBusy">✨</button>
            </view>
          </view>
        </view>

        <!-- n_film + n_sub -->
        <view class="grid-2">
          <view class="field">
            <view class="field-label">薄膜折射率 n_film</view>
            <input class="field-input" type="number" step="0.01" v-model="form.n_film" placeholder="2.60" />
          </view>
          <view class="field">
            <view class="field-label">衬底折射率 n_sub</view>
            <input class="field-input" type="number" step="0.01" v-model="form.n_sub" placeholder="2.55" />
          </view>
        </view>

        <!-- n range + peak distance -->
        <view class="grid-2 joint-section">
          <view class="field">
            <view class="field-label">n 联合反演范围</view>
            <view class="input-row">
              <input class="field-input" style="flex:1" type="number" step="0.1" v-model="form.n_min" placeholder="1.80" />
              <text class="range-sep">—</text>
              <input class="field-input" style="flex:1" type="number" step="0.1" v-model="form.n_max" placeholder="4.20" />
            </view>
          </view>
          <view class="field">
            <view class="field-label">寻峰间距</view>
            <input class="field-input" type="number" v-model="form.peak_distance" placeholder="30" />
          </view>
        </view>

        <!-- Actions -->
        <view class="hero-actions" style="margin-top: 16px;">
          <button class="btn btn-primary" @tap="runAnalysis" :disabled="running">
            {{ running ? '运算中...' : '▶ 执行运算分析' }}
          </button>
          <button class="btn btn-outline" @tap="syncToSimulator" :disabled="!lastResult">
            导入到仿真器
          </button>
        </view>
      </view>
    </view>

    <!-- Section: KPI Cards -->
    <view class="section" v-if="lastResult">
      <view class="section-title">核心指标</view>
      <view class="kpi-row">
        <view class="kpi-card">
          <view class="kpi-label">外延层厚度</view>
          <view class="kpi-value kpi-green">{{ displayThickness }}</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">拟合置信度</view>
          <view class="kpi-value kpi-purple">{{ displayConfidence }}</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">干涉峰数量</view>
          <view class="kpi-value kpi-blue">{{ lastResult.peak_count }}</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">平均 Δν</view>
          <view class="kpi-value">{{ displayDeltaNu }}</view>
        </view>
      </view>
    </view>

    <!-- Section: Visualizations -->
    <view class="section" v-if="lastResult">
      <view class="section-title">可视化中心</view>

      <!-- Viz Tabs -->
      <scroll-view scroll-x class="viz-tabs-scroll" :show-scrollbar="false">
        <view class="viz-tab-row">
          <view
            v-for="(tab, idx) in vizTabs"
            :key="idx"
            class="viz-tab"
            :class="{ active: vizTabIdx === idx }"
            @tap="switchVizTab(idx)"
          >{{ tab }}</view>
        </view>
      </scroll-view>

      <!-- Spectrum Plot (Tab 0) -->
      <view class="card" v-if="vizTabIdx === 0 && spectrumB64">
        <view class="card-title">干涉光谱拟合</view>
        <view class="zoom-wrapper">
          <view
            class="zoom-container"
            @touchstart.stop.prevent="onImgTouchStart"
            @touchmove.stop.prevent="onImgTouchMove"
            @touchend.stop.prevent="onImgTouchEnd"
            @tap="onImgTap"
          >
            <image
              :src="spectrumSrc"
              mode="widthFix"
              class="plot-image"
              :style="imgTransformStyle"
            />
          </view>
        </view>
      </view>

      <!-- Wafer Heatmap (Tab 1) -->
      <view class="card" v-if="vizTabIdx === 1">
        <view class="card-title">晶圆均匀性分布</view>
        <image v-if="waferB64" :src="waferSrc" mode="widthFix" class="plot-image" />
        <view v-else class="card-desc loading-desc">渲染中...</view>
      </view>

      <!-- Crystal Lattice (Tab 2) -->
      <view class="card" v-if="vizTabIdx === 2">
        <view class="card-title">3D 原子晶格构型</view>
        <image v-if="crystalB64" :src="crystalSrc" mode="widthFix" class="plot-image" />
        <view v-else class="card-desc loading-desc">渲染中...</view>
      </view>

      <!-- Standing Wave (Tab 3) -->
      <view class="card" v-if="vizTabIdx === 3">
        <view class="card-title">驻波光场深度解析</view>
        <image v-if="swaveB64" :src="swaveSrc" mode="widthFix" class="plot-image" />
        <view v-else class="card-desc loading-desc">渲染中...</view>
      </view>

      <!-- Dispersion (Tab 4) -->
      <view class="card" v-if="vizTabIdx === 4">
        <view class="card-title">动态色散建模 (n-k)</view>
        <image v-if="dispB64" :src="dispSrc" mode="widthFix" class="plot-image" />
        <view v-else class="card-desc loading-desc">渲染中...</view>
      </view>

      <!-- Result Terminal (all tabs) -->
      <view class="card" style="margin-top: 12px;">
        <view class="card-title">系统回馈</view>
        <view class="result-box">{{ resultText }}</view>
      </view>
    </view>

    <!-- Section: Import Data -->
    <view class="section">
      <view class="section-title">导入实验室数据</view>
      <!-- #ifdef H5 -->
      <view class="card">
        <view class="field">
          <view class="field-label">材料名称</view>
          <input class="field-input" v-model="importForm.material" placeholder="e.g. SiC" />
        </view>
        <view class="field">
          <view class="field-label">入射角 (deg)</view>
          <input class="field-input" type="number" step="0.1" v-model="importForm.angle" placeholder="10.0" />
        </view>
        <view class="field">
          <checkbox-group @change="onImportReplaceChange">
            <label class="checkbox-label">
              <checkbox value="replace" :checked="importForm.replace" />
              导入前清空同材料同角度数据
            </label>
          </checkbox-group>
        </view>
        <view class="hero-actions">
          <button class="btn btn-outline" @tap="chooseFile">选择文件</button>
          <button class="btn btn-primary" @tap="doImport" :disabled="!importForm.filePath || importing">
            {{ importing ? '导入中...' : '执行导入' }}
          </button>
        </view>
        <view class="card-desc" v-if="importForm.fileName">已选择: {{ importForm.fileName }}</view>
        <view class="card-desc" v-if="importMsg">{{ importMsg }}</view>
      </view>
      <!-- #endif -->
      <!-- #ifdef APP-PLUS -->
      <view class="card">
        <view class="card-desc" style="text-align: center; padding: 20px;">
          App 端暂不支持直接上传文件。<br/>
          请通过 Web 客户端导入数据后，在此处刷新数据集即可使用。
        </view>
      </view>
      <!-- #endif -->
    </view>

    <!-- Safety spacer -->
    <view style="height: 40px;"></view>
  </view>
</template>

<script>
import { api } from '../../common/api';
import config from '../../common/config';

export default {
  data() {
    return {
      // Health
      healthOk: null,

      // Loading
      loading: false,
      loadingText: '运算中...',
      running: false,
      importing: false,
      importMsg: '',
      autoCutoffBusy: false,

      // Datasets from API
      datasets: [],
      datasetsRaw: [],
      datasetIdx: 0,

      // Materials (for presets)
      materials: [],
      materialPresets: [],
      presetIdx: 0,  // 0 = custom/manual

      // Algorithm modes
      algorithms: [
        { value: '峰值间距法（快速）', label: '峰值间距法（快速）' },
        { value: 'TMM拟合法（精细）', label: 'TMM拟合法（精细）' }
      ],
      inversions: [
        { value: '固定折射率（反演厚度）', label: '固定折射率（反演厚度）' },
        { value: '联合反演（厚度+n_film）', label: '联合反演（厚度+n_film）' }
      ],
      methodIdx: 1,
      inversionIdx: 0,

      // Form
      form: {
        material: '',
        angle_deg: '',
        min_cutoff: '1500',
        n_film: '2.60',
        n_sub: '2.55',
        n_min: '1.80',
        n_max: '4.20',
        peak_distance: '30'
      },

      // Result
      lastResult: null,
      resultText: '',
      displayThickness: '—',
      displayConfidence: '—',
      displayDeltaNu: '—',

      // Viz
      vizTabs: ['干涉光谱', '晶圆均匀性', '晶格构型', '驻波光场', 'n-k色散'],
      vizTabIdx: 0,
      spectrumB64: '',
      waferB64: '',
      crystalB64: '',
      swaveB64: '',
      dispB64: '',

      // Import
      importForm: {
        material: '',
        angle: '10.0',
        replace: true,
        filePath: '',
        fileName: ''
      },

      // Pinch zoom
      _imgScale: 1,
      _imgTx: 0,
      _imgTy: 0,
      _imgZoom: null
    };
  },
  computed: {
    selectedDatasetLabel() {
      if (!this.datasets.length) return '(无数据 — 请先通过 Web 端导入)';
      return this.datasets[this.datasetIdx]?.name || '选择数据集';
    },
    presetLabel() {
      if (this.presetIdx === 0) return '— 自定义参数 —';
      return this.materialPresets[this.presetIdx]?.label || '— 自定义参数 —';
    },
    spectrumSrc() {
      return this.spectrumB64 ? `data:image/png;base64,${this.spectrumB64}` : '';
    },
    waferSrc() {
      return this.waferB64 ? `data:image/png;base64,${this.waferB64}` : '';
    },
    crystalSrc() {
      return this.crystalB64 ? `data:image/png;base64,${this.crystalB64}` : '';
    },
    swaveSrc() {
      return this.swaveB64 ? `data:image/png;base64,${this.swaveB64}` : '';
    },
    dispSrc() {
      return this.dispB64 ? `data:image/png;base64,${this.dispB64}` : '';
    },
    imgTransformStyle() {
      const s = this._imgScale || 1;
      const x = this._imgTx || 0;
      const y = this._imgTy || 0;
      return `transform: translate(${x}px, ${y}px) scale(${s});`;
    }
  },
  onLoad() {
    this.initAll();
  },
  onShow() {
    // Reload materials when coming back from materials page
    this.loadMaterials();
    this.loadDatasets();
  },
  methods: {
    async initAll() {
      try {
        const res = await api.getHealth();
        this.healthOk = res && res.ok;
      } catch (e) {
        this.healthOk = false;
      }
      this.loadDatasets();
      this.loadMaterials();
      this.restoreState();
    },

    // ---- Data Loading ----
    async loadDatasets() {
      try {
        const res = await api.getDatasets();
        this.datasetsRaw = res.items || [];
        this.datasets = res.items || [];
        // If we have a form material & angle from saved state, keep it selected
        if (this.form.material && this.form.angle_deg) {
          const idx = this.datasets.findIndex(
            d => d.material === this.form.material && String(d.angle) === String(this.form.angle_deg)
          );
          if (idx >= 0) this.datasetIdx = idx;
        }
      } catch (e) {
        this.datasets = [];
        this.datasetsRaw = [];
      }
    },
    async loadMaterials() {
      try {
        const res = await api.getMaterials();
        this.materials = res.items || [];
        this.materialPresets = [
          { label: '— 自定义参数 —', n_film: null, n_sub: null },
          ...this.materials.map(m => ({
            label: `${m.name} (n_film=${m.n_film}, n_sub=${m.n_sub})`,
            n_film: m.n_film,
            n_sub: m.n_sub,
            name: m.name
          }))
        ];
      } catch (e) {
        this.materials = [];
        this.materialPresets = [{ label: '— 自定义参数 —', n_film: null, n_sub: null }];
      }
    },

    // ---- Pickers ----
    onDatasetChange(e) {
      this.datasetIdx = Number(e.detail.value || 0);
      const ds = this.datasets[this.datasetIdx];
      if (ds) {
        this.form.material = ds.material;
        this.form.angle_deg = String(ds.angle);
        this.saveState();
      }
    },
    onMethodChange(e) {
      this.methodIdx = Number(e.detail.value || 0);
      this.saveState();
    },
    onInversionChange(e) {
      this.inversionIdx = Number(e.detail.value || 0);
      this.saveState();
    },
    onPresetChange(e) {
      this.presetIdx = Number(e.detail.value || 0);
      const p = this.materialPresets[this.presetIdx];
      if (p && p.n_film != null && p.n_sub != null) {
        this.form.n_film = String(p.n_film);
        this.form.n_sub = String(p.n_sub);
      }
      this.saveState();
    },

    // ---- Auto Cutoff ----
    async autoCutoff() {
      if (!this.form.material || !this.form.angle_deg) {
        uni.showToast({ title: '请先选择数据集', icon: 'none' });
        return;
      }
      this.autoCutoffBusy = true;
      try {
        const res = await api.suggestCutoff({
          material: this.form.material,
          angle: parseFloat(this.form.angle_deg)
        });
        if (res.ok) {
          this.form.min_cutoff = String(Math.round(res.value));
          uni.showToast({ title: '已推算最佳起延波数', icon: 'none' });
          this.saveState();
        } else {
          uni.showToast({ title: res.error || '推算失败', icon: 'none' });
        }
      } catch (e) {
        uni.showToast({ title: e.message || '推算失败', icon: 'none' });
      } finally {
        this.autoCutoffBusy = false;
      }
    },

    // ---- Run Analysis ----
    async runAnalysis() {
      if (!this.form.material || !this.form.angle_deg) {
        uni.showToast({ title: '请先选择数据集', icon: 'none' });
        return;
      }

      const payload = {
        material: this.form.material,
        angle_deg: parseFloat(this.form.angle_deg),
        min_cutoff: parseFloat(this.form.min_cutoff) || 1500,
        n_film: parseFloat(this.form.n_film) || 2.6,
        n_sub: parseFloat(this.form.n_sub) || 2.55,
        n_min: parseFloat(this.form.n_min) || 1.8,
        n_max: parseFloat(this.form.n_max) || 4.2,
        peak_distance: parseInt(this.form.peak_distance) || 30,
        method: this.algorithms[this.methodIdx].value,
        inversion: this.inversions[this.inversionIdx].value
      };

      this.running = true;
      this.loading = true;
      this.loadingText = '多维矩阵逆算中...';
      this.resultText = '运算正在进行中，解析干涉条纹...\n求解逆斯涅尔相消方程...';

      try {
        const res = await api.analyze(payload);
        if (res.ok) {
          this.lastResult = res;
          this.spectrumB64 = res.spectrum_plot_b64 || '';

          // Animate KPIs
          this.animateKPI('displayThickness', res.thickness_um, ' μm', 3);
          this.animateKPI('displayConfidence', res.fit_confidence, '%', 1);
          this.displayDeltaNu = (res.avg_delta_nu || 0).toFixed(2) + ' cm⁻¹';

          // Result text
          this.resultText =
            `> 运算完成 [OK]\n` +
            `> 参数: n_film=${res.n_film.toFixed(3)}, n_sub=${res.n_sub.toFixed(3)}\n` +
            `> 获取有效波峰: ${res.peak_count}个. 平均间距: ${(res.avg_delta_nu || 0).toFixed(2)} cm⁻¹\n` +
            `> MSE Final 指标: ${(res.mse_final || 0).toFixed(5)}\n` +
            `> ----\n` +
            `> 核心结论: 拟定厚度 ${res.thickness_um.toFixed(3)} μm (εr≈${(res.epsilon_r || 0).toFixed(2)})`;

          // Load secondary viz images
          this.loadVizImages(res);

          uni.showToast({ title: '分析完成并已归档', icon: 'success' });
        } else {
          this.resultText = '运算错误: ' + (res.error || '未知错误');
          uni.showToast({ title: res.error || '分析失败', icon: 'none' });
        }
      } catch (e) {
        this.resultText = '运算错误: ' + (e.message || '网络请求失败');
        uni.showToast({ title: e.message || '分析失败', icon: 'none' });
      } finally {
        this.running = false;
        this.loading = false;
      }
    },

    async loadVizImages(res) {
      const material = this.form.material || '';
      const title = `${material} - ${this.form.angle_deg}度`;

      // Wafer
      try {
        const w = await api.getPlotWafer({ thickness_um: res.thickness_um, material });
        if (w.ok) this.waferB64 = w.image_b64;
      } catch (e) { /* ignore */ }

      // Crystal
      try {
        const c = await api.getPlotCrystal({ material });
        if (c.ok) this.crystalB64 = c.image_b64;
      } catch (e) { /* ignore */ }

      // Standing wave
      if (res.swave_x && res.swave_y && res.swave_z) {
        try {
          const s = await api.getPlotStandingWave({
            swave_x: res.swave_x,
            swave_y: res.swave_y,
            swave_z: res.swave_z,
            title: `${title} | Standing Wave`
          });
          if (s.ok) this.swaveB64 = s.image_b64;
        } catch (e) { /* ignore */ }
      }

      // Dispersion
      if (res.disp_x && res.disp_n && res.disp_k) {
        try {
          const d = await api.getPlotDispersion({
            disp_x: res.disp_x,
            disp_n: res.disp_n,
            disp_k: res.disp_k,
            disp_ref_n: res.disp_ref_n || [],
            disp_upper: res.disp_upper || [],
            disp_lower: res.disp_lower || [],
            title: `${title} | n-k Dispersion`
          });
          if (d.ok) this.dispB64 = d.image_b64;
        } catch (e) { /* ignore */ }
      }
    },

    animateKPI(field, value, suffix, decimals) {
      const target = Number(value) || 0;
      let current = 0;
      const steps = 30;
      const duration = 1200;
      const interval = duration / steps;
      const increment = target / steps;

      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        this[field] = current.toFixed(decimals) + suffix;
      }, interval);
    },

    switchVizTab(idx) {
      this.vizTabIdx = idx;
    },

    // ---- Sync to Simulator ----
    syncToSimulator() {
      if (!this.lastResult) return;
      const slim = {
        thickness: this.lastResult.thickness_um,
        n_film: this.lastResult.n_film,
        n_sub: this.lastResult.n_sub,
        angle: parseFloat(this.form.angle_deg) || 0,
        material: this.form.material,
        fit_confidence: this.lastResult.fit_confidence,
        mse_final: this.lastResult.mse_final,
        x: this.lastResult.x || [],
        y: this.lastResult.y || [],
        fit_y: this.lastResult.fit_y || [],
        peaks_x: this.lastResult.peaks_x || [],
        peaks_y: this.lastResult.peaks_y || [],
        spectrum_plot_b64: this.spectrumB64
      };
      uni.setStorageSync('epi_lab_import', JSON.stringify({
        imported_at: Date.now(),
        analysis: slim
      }));
      uni.showToast({ title: '已导入到仿真器', icon: 'success' });
      // Navigate to simulator tab
      uni.switchTab({ url: '/pages/simulator/simulator' });
    },

    goToMaterials() {
      uni.switchTab({ url: '/pages/materials/materials' });
    },

    // ---- Import (H5 only) ----
    onImportReplaceChange(e) {
      this.importForm.replace = (e.detail.value || []).includes('replace');
    },
    chooseFile() {
      // #ifdef H5
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.csv,.xlsx,.xls';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          this.importForm.filePath = file;
          this.importForm.fileName = file.name;
        }
      };
      input.click();
      // #endif
    },
    async doImport() {
      if (!this.importForm.material || !this.importForm.angle) {
        uni.showToast({ title: '请填写材料名称和角度', icon: 'none' });
        return;
      }
      this.importing = true;
      this.importMsg = '';
      try {
        // #ifdef H5
        const formData = new FormData();
        formData.append('material', this.importForm.material);
        formData.append('angle', this.importForm.angle);
        formData.append('replace', this.importForm.replace ? '1' : '0');
        formData.append('file', this.importForm.filePath);

        const res = await fetch(
          `${config.baseUrl}/api/import`,
          { method: 'POST', body: formData }
        );
        const data = await res.json();
        if (res.ok && data.ok) {
          this.importMsg = `导入成功: 写入 ${data.count} 行`;
          uni.showToast({ title: '导入成功', icon: 'success' });
          this.loadDatasets();
          // Auto-select
          const label = data.label;
          this.$nextTick(() => {
            const idx = this.datasets.findIndex(d => d.name === label);
            if (idx >= 0) this.datasetIdx = idx;
          });
        } else {
          this.importMsg = data.error || '导入失败';
          uni.showToast({ title: data.error || '导入失败', icon: 'none' });
        }
        // #endif
      } catch (e) {
        this.importMsg = '导入失败: ' + (e.message || '网络错误');
        uni.showToast({ title: '导入失败', icon: 'none' });
      } finally {
        this.importing = false;
      }
    },

    // ---- Pinch Zoom ----
    onImgTouchStart(e) {
      const touches = e.touches || e.changedTouches || [];
      if (!this._imgZoom) {
        this._imgZoom = { startDist: null, startScale: this._imgScale || 1, lastX: 0, lastY: 0, dragging: false };
      }
      if (touches.length === 2) {
        this._imgZoom.startDist = this._imgDist(touches[0], touches[1]);
        this._imgZoom.startScale = this._imgScale || 1;
      } else if (touches.length === 1) {
        this._imgZoom.dragging = true;
        this._imgZoom.lastX = touches[0].clientX;
        this._imgZoom.lastY = touches[0].clientY;
      }
    },
    onImgTouchMove(e) {
      const touches = e.touches || e.changedTouches || [];
      if (!this._imgZoom) return;
      if (touches.length === 2 && this._imgZoom.startDist) {
        const d = this._imgDist(touches[0], touches[1]);
        const scale = (d / this._imgZoom.startDist) * this._imgZoom.startScale;
        this._imgScale = Math.max(1, Math.min(scale, 6));
      } else if (touches.length === 1 && this._imgZoom.dragging && this._imgScale > 1) {
        this._imgTx = (this._imgTx || 0) + touches[0].clientX - this._imgZoom.lastX;
        this._imgTy = (this._imgTy || 0) + touches[0].clientY - this._imgZoom.lastY;
        this._imgZoom.lastX = touches[0].clientX;
        this._imgZoom.lastY = touches[0].clientY;
      }
    },
    onImgTouchEnd() {
      if (this._imgZoom) {
        this._imgZoom.startDist = null;
        this._imgZoom.dragging = false;
      }
    },
    onImgTap() {
      if (this._imgScale > 1) {
        this._imgScale = 1;
        this._imgTx = 0;
        this._imgTy = 0;
      }
    },
    _imgDist(a, b) {
      const dx = (a.clientX || a.pageX) - (b.clientX || b.pageX);
      const dy = (a.clientY || a.pageY) - (b.clientY || b.pageY);
      return Math.sqrt(dx * dx + dy * dy);
    },

    // ---- State Persistence ----
    saveState() {
      const state = {
        datasetIdx: this.datasetIdx,
        methodIdx: this.methodIdx,
        inversionIdx: this.inversionIdx,
        presetIdx: this.presetIdx,
        form: { ...this.form }
      };
      uni.setStorageSync('epi_dash_state', JSON.stringify(state));
    },
    restoreState() {
      try {
        const raw = uni.getStorageSync('epi_dash_state');
        if (!raw) return;
        const s = JSON.parse(raw);
        if (s.methodIdx != null) this.methodIdx = s.methodIdx;
        if (s.inversionIdx != null) this.inversionIdx = s.inversionIdx;
        if (s.presetIdx != null) this.presetIdx = s.presetIdx;
        if (s.form) {
          if (s.form.min_cutoff) this.form.min_cutoff = s.form.min_cutoff;
          if (s.form.n_film) this.form.n_film = s.form.n_film;
          if (s.form.n_sub) this.form.n_sub = s.form.n_sub;
          if (s.form.n_min) this.form.n_min = s.form.n_min;
          if (s.form.n_max) this.form.n_max = s.form.n_max;
          if (s.form.peak_distance) this.form.peak_distance = s.form.peak_distance;
        }
        // dataset idx restored after datasets load
        if (s.datasetIdx != null) this.datasetIdx = s.datasetIdx;
      } catch (e) { /* ignore */ }
    }
  },
  watch: {
    form: {
      deep: true,
      handler() { this.saveState(); }
    },
    methodIdx() { this.saveState(); },
    inversionIdx() { this.saveState(); },
    presetIdx() { this.saveState(); },
    datasetIdx() { this.saveState(); }
  }
};
</script>

<style lang="scss">
@import '../../uni.scss';

// Loader
.loader-overlay {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(2, 6, 23, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  gap: 16px;
}
.loader-spinner {
  width: 48px; height: 48px;
  border: 3px solid rgba(14, 165, 233, 0.2);
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loader-text {
  color: #94a3b8;
  font-size: 14px;
}

// Hero
.hero-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 13px;
  color: #94a3b8;
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
}
.dot-green { background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.6); }
.dot-red { background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.6); }

// Field label link
.field-label-link {
  font-size: 11px;
  color: #0ea5e9;
  margin-left: auto;
  text-decoration: none;
}

// Input row
.input-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.range-sep {
  color: #64748b;
  flex-shrink: 0;
}

// Joint section
.joint-section {
  border-top: 1px solid rgba(51, 65, 85, 0.4);
  padding-top: 12px;
  margin-top: 4px;
}

// KPI row
.kpi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.kpi-card {
  flex: 1 1 45%;
  min-width: 140px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: 12px;
  padding: 12px;
}
.kpi-label {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 4px;
}
.kpi-value {
  font-size: 22px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  color: #f8fafc;
}
.kpi-green { color: #10b981; }
.kpi-purple { color: #a78bfa; }
.kpi-blue { color: #38bdf8; }

// Viz tabs
.viz-tabs-scroll {
  white-space: nowrap;
  margin-bottom: 8px;
}
.viz-tab-row {
  display: inline-flex;
  gap: 8px;
  padding: 4px 0;
}
.viz-tab {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  background: rgba(15, 23, 42, 0.5);
  color: #94a3b8;
  border: 1px solid rgba(51, 65, 85, 0.4);
  flex-shrink: 0;
}
.viz-tab.active {
  background: rgba(14, 165, 233, 0.15);
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.5);
}

// Zoom
.zoom-wrapper { overflow: hidden; }
.zoom-container {
  width: 100%;
  height: auto;
  touch-action: none;
}
.plot-image {
  width: 100%;
  border-radius: 12px;
  transform-origin: center center;
  will-change: transform;
}

// Result box
.result-box {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #a7f3d0;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 12px;
  white-space: pre-wrap;
  min-height: 80px;
  line-height: 1.6;
}

// Checkbox label
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #cbd5e1;
}

// Card desc loading
.loading-desc {
  text-align: center;
  padding: 30px;
  color: #64748b;
}

// Small ghost button
.btn-sm {
  padding: 4px 10px;
  font-size: 16px;
  flex-shrink: 0;
}
.btn-outline {
  background: transparent;
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
}
</style>

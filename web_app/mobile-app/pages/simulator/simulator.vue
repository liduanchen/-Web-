<template>
  <view class="screen">
    <!-- Hero -->
    <view class="hero">
      <view class="hero-title">全景物理仿真器</view>
      <view class="hero-sub">Optical Path Simulation · Real-time Ray Tracing</view>
    </view>

    <!-- Import Status -->
    <view class="section" v-if="importedResult">
      <view class="card">
        <view class="card-title">导入的拟合结果</view>
        <view class="card-desc">
          <text v-if="isUsingImported">
            ✓ 当前显示从分析面板导入的拟合结果: {{ importedResult.material || '未知' }} |
            厚度 {{ (importedResult.thickness || 0).toFixed(3) }} μm |
            置信度 {{ (importedResult.fit_confidence || 0).toFixed(1) }}%
          </text>
          <text v-else>
            已导入拟合结果作为参考。当前参数已手动修改，显示参数驱动仿真。
          </text>
        </view>
      </view>
    </view>

    <!-- Ray Canvas -->
    <view class="section">
      <view class="section-title">介质层光路实时演算 (Snell's Law · 多次反射)</view>
      <canvas
        canvas-id="rayCanvas"
        id="rayCanvas"
        class="ray-canvas"
        @touchstart="onCanvasTouch"
      ></canvas>
    </view>

    <!-- Spectrum -->
    <view class="section">
      <view class="section-title">理论反射光谱图</view>
      <view class="card">
        <canvas
          canvas-id="specCanvas"
          id="specCanvas"
          class="spec-canvas"
        ></canvas>
      </view>
    </view>

    <!-- Sliders -->
    <view class="section">
      <view class="section-title">干涉核心变量调控板</view>
      <view class="card">
        <!-- Thickness -->
        <view class="field">
          <view class="field-label">
            外延层厚度 (d)
            <text class="val-chip">{{ thickness.toFixed(3) }} μm</text>
          </view>
          <slider :min="0.05" :max="100" :value="thickness" step="0.05" show-value
            @change="(e) => onSliderChange('thickness', e.detail.value)" />
          <input class="field-input" type="number" step="0.01" :value="thickness"
            @input="(e) => onNumChange('thickness', e.detail.value)" />
        </view>

        <!-- n_film -->
        <view class="field">
          <view class="field-label">
            薄膜折射率 (n₁)
            <text class="val-chip">{{ nFilm.toFixed(2) }}</text>
          </view>
          <slider :min="1.2" :max="4.5" :value="nFilm" step="0.02" show-value
            @change="(e) => onSliderChange('nFilm', e.detail.value)" />
          <input class="field-input" type="number" step="0.01" :value="nFilm"
            @input="(e) => onNumChange('nFilm', e.detail.value)" />
        </view>

        <!-- n_sub -->
        <view class="field">
          <view class="field-label">
            衬底折射率 (n₂)
            <text class="val-chip">{{ nSub.toFixed(2) }}</text>
          </view>
          <slider :min="1.2" :max="4.5" :value="nSub" step="0.02" show-value
            @change="(e) => onSliderChange('nSub', e.detail.value)" />
          <input class="field-input" type="number" step="0.01" :value="nSub"
            @input="(e) => onNumChange('nSub', e.detail.value)" />
        </view>

        <!-- Angle -->
        <view class="field">
          <view class="field-label">
            入射角 (θ)
            <text class="val-chip">{{ angleDeg }}°</text>
          </view>
          <slider :min="0" :max="75" :value="angleDeg" step="1" show-value
            @change="(e) => onSliderChange('angle', e.detail.value)" />
          <input class="field-input" type="number" min="0" max="89" step="0.5" :value="angleDeg"
            @input="(e) => onNumChange('angle', e.detail.value)" />
        </view>

        <!-- Preset + Reset -->
        <view class="hero-actions" style="margin-top: 12px;">
          <picker :range="presets" range-key="label" @change="onPresetSel">
            <button class="btn btn-outline">加载材料预设</button>
          </picker>
          <button class="btn btn-ghost" @tap="resetParams">重置</button>
        </view>
      </view>
    </view>

    <view style="height: 40px;"></view>
  </view>
</template>

<script>
import { api } from '../../common/api';

export default {
  data() {
    return {
      // Parameters
      thickness: 1.0,
      nFilm: 2.60,
      nSub: 2.55,
      angleDeg: 30,

      // Imported from dashboard
      importedResult: null,
      userTouched: false,

      // Materials for presets
      presets: [],
      materials: [],

      // Canvas
      rayW: 0,
      rayH: 0,
      specW: 0,
      specH: 0,

      // Experimental data
      expData: null
    };
  },
  computed: {
    isUsingImported() {
      if (!this.importedResult || this.userTouched) return false;
      return Math.abs((this.importedResult.thickness || 0) - this.thickness) < 1e-6 &&
        Math.abs((this.importedResult.n_film || 0) - this.nFilm) < 1e-6 &&
        Math.abs((this.importedResult.n_sub || 0) - this.nSub) < 1e-6 &&
        Math.abs((this.importedResult.angle || 0) - this.angleDeg) < 1e-6;
    }
  },
  onLoad(options) {
    // Check for import from dashboard
    this.loadImportedResult();

    // URL params (from web "sync to lab")
    if (options) {
      if (options.thickness) this.thickness = parseFloat(options.thickness);
      if (options.n) this.nFilm = parseFloat(options.n);
      if (options.nsub) this.nSub = parseFloat(options.nsub);
      if (options.angle) this.angleDeg = parseFloat(options.angle);
    }
  },
  onReady() {
    this.initCanvases();
    this.loadMaterials();
  },
  onShow() {
    // Re-check imported result when tab switches
    this.loadImportedResult();
    this.$nextTick(() => {
      this.initCanvases();
      this.loadMaterials();
    });
  },
  methods: {
    loadImportedResult() {
      try {
        const raw = uni.getStorageSync('epi_lab_import');
        if (raw) {
          const payload = JSON.parse(raw);
          if (payload && payload.analysis) {
            this.importedResult = payload.analysis;
            // If user hasn't touched controls, sync params
            if (!this.userTouched) {
              if (payload.analysis.thickness != null) this.thickness = Number(payload.analysis.thickness);
              if (payload.analysis.n_film != null) this.nFilm = Number(payload.analysis.n_film);
              if (payload.analysis.n_sub != null) this.nSub = Number(payload.analysis.n_sub);
              if (payload.analysis.angle != null) this.angleDeg = Number(payload.analysis.angle);
              if (payload.analysis.x && payload.analysis.y) {
                this.expData = { x: payload.analysis.x, y: payload.analysis.y };
              }
            }
          }
        }
      } catch (e) { /* ignore */ }
    },

    async loadMaterials() {
      try {
        const res = await api.getMaterials();
        this.materials = res.items || [];
        this.presets = this.materials.map(m => ({
          label: `${m.name} (n_film=${m.n_film}, n_sub=${m.n_sub})`,
          n_film: m.n_film,
          n_sub: m.n_sub
        }));
      } catch (e) {
        this.presets = [];
      }
    },

    onPresetSel(e) {
      const p = this.presets[Number(e.detail.value || 0)];
      if (p) {
        this.nFilm = p.n_film;
        this.nSub = p.n_sub;
        this.userTouched = true;
        this.updateAll();
      }
    },

    resetParams() {
      this.thickness = 1.0;
      this.nFilm = 2.60;
      this.nSub = 2.55;
      this.angleDeg = 30;
      this.userTouched = false;
      this.expData = null;
      // Reapply imported if available
      this.loadImportedResult();
      this.updateAll();
    },

    onSliderChange(field, value) {
      this[field] = Number(value);
      this.userTouched = true;
      this.updateAll();
    },
    onNumChange(field, value) {
      const v = Number(value);
      if (!isNaN(v)) {
        this[field] = v;
        this.userTouched = true;
        this.updateAll();
      }
    },

    updateAll() {
      this.$nextTick(() => {
        this.drawRayCanvas();
        this.drawSpecCanvas();
      });
    },

    // ---- Canvases ----
    initCanvases() {
      // Ray canvas
      const self = this;
      try {
        const query = uni.createSelectorQuery().in(this);
        query.select('#rayCanvas').boundingClientRect(rect => {
          if (!rect) return;
          self.rayW = rect.width || 340;
          self.rayH = Math.max(280, rect.width * 0.7);
          self.drawRayCanvas();
        }).exec();
        query.select('#specCanvas').boundingClientRect(rect => {
          if (!rect) return;
          self.specW = rect.width || 340;
          self.specH = Math.max(220, rect.width * 0.55);
          self.drawSpecCanvas();
        }).exec();
      } catch (e) { /* ignore */ }
    },

    drawRayCanvas() {
      const ctx = uni.createCanvasContext('rayCanvas', this);
      const w = this.rayW || 340;
      const h = this.rayH || 280;
      const margin = w * 0.06;
      const airH = h * 0.28;
      const ySub = h * 0.78;

      // Log-scale film height for visual dynamic range
      const t = Math.max(0.05, this.thickness);
      const filmH = 15 + (Math.log1p(t) / Math.log1p(100)) * 120;
      const yFilmTop = ySub - filmH;

      // Clear
      ctx.clearRect(0, 0, w, h);

      // Background
      ctx.setFillStyle('#020617');
      ctx.fillRect(0, 0, w, h);

      // Substrate
      ctx.setFillStyle('rgba(30, 41, 59, 0.4)');
      ctx.fillRect(margin, ySub, w - margin * 2, h - ySub - margin);
      ctx.setFillStyle('rgba(139, 92, 246, 0.5)');
      ctx.fillRect(margin, ySub, w - margin * 2, 2);

      // Film
      ctx.setFillStyle('rgba(14, 165, 233, 0.15)');
      ctx.fillRect(margin, yFilmTop, w - margin * 2, filmH);
      ctx.setFillStyle('rgba(56, 189, 248, 0.6)');
      ctx.fillRect(margin, yFilmTop, w - margin * 2, 1.5);

      // Labels
      ctx.setFillStyle('#cbd5e1');
      ctx.setFontSize(11);
      ctx.fillText(`Air n₀=1.0`, margin + 8, airH * 0.5);
      ctx.fillText(`Film n=${this.nFilm.toFixed(2)}  d=${t.toFixed(3)}μm`, margin + 8, yFilmTop + 14);
      ctx.fillText(`Substrate n=${this.nSub.toFixed(2)}`, margin + 8, ySub + 16);

      // Ray tracing
      const n0 = 1.0;
      const theta0 = this.angleDeg * Math.PI / 180;
      const sinTh1 = n0 * Math.sin(theta0) / Math.max(this.nFilm, 1.01);
      const theta1 = Math.asin(Math.max(-1, Math.min(1, sinTh1)));

      const entryX = margin + (w - margin * 2) * 0.30;
      const rayLenAir = (yFilmTop - airH * 0.5) * 1.2;
      const xAir0 = entryX - rayLenAir * Math.sin(theta0);
      const yAir0 = yFilmTop - rayLenAir * Math.cos(theta0);

      // Normal line
      ctx.setStrokeStyle('rgba(148, 163, 184, 0.3)');
      ctx.setLineWidth(1);
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(entryX, yFilmTop - 50);
      ctx.lineTo(entryX, ySub + 20);
      ctx.stroke();
      ctx.setLineDash([]);

      // Incident ray
      ctx.setStrokeStyle('rgba(14, 165, 233, 0.9)');
      ctx.setLineWidth(2.5);
      ctx.beginPath();
      ctx.moveTo(xAir0, yAir0);
      ctx.lineTo(entryX, yFilmTop);
      ctx.stroke();

      // Multiple internal reflections
      let x = entryX;
      let y = yFilmTop + 1;
      let ux = Math.sin(theta1);
      let uy = Math.cos(theta1);
      let outCount = 0;

      for (let bounce = 0; bounce < 14; bounce++) {
        if (Math.abs(uy) < 1e-9) break;
        const tHit = uy > 0 ? (ySub - y) / uy : (yFilmTop - y) / uy;
        if (tHit <= 0) break;
        const x2 = x + ux * tHit;
        const y2 = y + uy * tHit;
        if (x2 < margin - 10 || x2 > w - margin + 10) break;

        const alpha = Math.max(0.15, 0.85 - bounce * 0.08);
        ctx.setStrokeStyle(`rgba(56, 189, 248, ${alpha})`);
        ctx.setLineWidth(bounce === 0 ? 2 : 1.2);
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Emergent rays
        if (Math.abs(y2 - yFilmTop) < 4 && outCount < 5) {
          outCount++;
          const outLen = (yFilmTop - airH * 0.5) * 0.9;
          const dx = (outCount - 1) * 10;
          ctx.setStrokeStyle(`rgba(139, 92, 246, ${Math.max(0.15, 0.8 - outCount * 0.15)})`);
          ctx.setLineWidth(1.5);
          ctx.setLineDash([6, 4]);
          ctx.beginPath();
          ctx.moveTo(x2 + dx * 0.5, yFilmTop);
          ctx.lineTo(x2 - outLen * Math.sin(theta0) + dx, yFilmTop - outLen * Math.cos(theta0));
          ctx.stroke();
          ctx.setLineDash([]);
        }
        x = x2;
        y = y2;
        uy = -uy;
      }

      ctx.draw();
    },

    drawSpecCanvas() {
      const ctx = uni.createCanvasContext('specCanvas', this);
      const w = this.specW || 340;
      const h = this.specH || 220;
      const pad = { left: 48, right: 20, top: 20, bottom: 40 };
      const pw = w - pad.left - pad.right;
      const ph = h - pad.top - pad.bottom;

      ctx.clearRect(0, 0, w, h);
      ctx.setFillStyle('#0f172a');
      ctx.fillRect(0, 0, w, h);

      // Axes
      ctx.setStrokeStyle('#475569');
      ctx.setLineWidth(1);
      ctx.beginPath();
      ctx.moveTo(pad.left, pad.top);
      ctx.lineTo(pad.left, h - pad.bottom);
      ctx.lineTo(w - pad.right, h - pad.bottom);
      ctx.stroke();

      // Labels
      ctx.setFillStyle('#94a3b8');
      ctx.setFontSize(10);
      ctx.fillText('波数 (cm⁻¹)', w / 2 - 20, h - 6);
      ctx.save();
      ctx.translate(10, h / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText('反射率 (%)', -30, 0);
      ctx.restore();

      // Spectrum curves
      const xMin = 1000, xMax = 3000;
      const yMin = 0, yMax = 100;

      const toX = (v) => pad.left + ((v - xMin) / (xMax - xMin)) * pw;
      const toY = (v) => pad.top + (1 - (v - yMin) / (yMax - yMin)) * ph;

      // Experimental data
      if (this.expData && this.expData.x && this.expData.y) {
        ctx.setStrokeStyle('#22d3ee');
        ctx.setLineWidth(2);
        ctx.beginPath();
        let first = true;
        for (let i = 0; i < this.expData.x.length; i++) {
          const sx = toX(this.expData.x[i]);
          const sy = toY(this.expData.y[i]);
          if (first) { ctx.moveTo(sx, sy); first = false; }
          else ctx.lineTo(sx, sy);
        }
        ctx.stroke();
      }

      // Theoretical cosine curve
      const nFilm = Math.max(1.01, this.nFilm);
      const angleRad = this.angleDeg * Math.PI / 180;
      const cosThPrime = Math.cos(Math.asin(Math.min(1, Math.sin(angleRad) / nFilm)));
      const d = Math.max(0.01, this.thickness);

      ctx.setStrokeStyle('#f59e0b');
      ctx.setLineWidth(2);
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      let first = true;
      for (let nu = xMin; nu <= xMax; nu += 10) {
        const phase = 4 * Math.PI * nu * nFilm * d * cosThPrime / 10000;
        const refl = 50 + 20 * Math.cos(phase);
        const sx = toX(nu);
        const sy = toY(Math.max(5, Math.min(95, refl)));
        if (first) { ctx.moveTo(sx, sy); first = false; }
        else ctx.lineTo(sx, sy);
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Legend
      ctx.setFillStyle('#22d3ee');
      ctx.fillRect(w - pad.right - 130, pad.top + 4, 12, 12);
      ctx.setFillStyle('#f59e0b');
      ctx.fillRect(w - pad.right - 130, pad.top + 20, 12, 12);
      ctx.setFillStyle('#cbd5e1');
      ctx.setFontSize(10);
      ctx.fillText('实验光谱', w - pad.right - 114, pad.top + 14);
      ctx.fillText('理论仿真', w - pad.right - 114, pad.top + 30);

      ctx.draw();
    },

    onCanvasTouch() {
      // Toggle user touched
      this.userTouched = true;
    }
  }
};
</script>

<style lang="scss">
@import '../../uni.scss';

.ray-canvas {
  width: 100%;
  height: 320px;
  background: #020617;
  border-radius: 12px;
  margin-top: 8px;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.spec-canvas {
  width: 100%;
  height: 280px;
  border-radius: 8px;
}

.val-chip {
  font-size: 12px;
  color: #38bdf8;
  margin-left: 6px;
  font-weight: 600;
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

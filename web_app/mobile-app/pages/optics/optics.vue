<template>
  <view class="screen">
    <view class="hero">
      <view class="hero-title">光路示意 · Snell's Law</view>
      <view class="hero-sub">可视化多次反射 · 入射/反射/折射 · 全内反射检测</view>
    </view>

    <!-- Controls -->
    <view class="section">
      <view class="card">
        <!-- Incident medium -->
        <view class="field">
          <view class="field-label">上层介质折射率 n₀</view>
          <input class="field-input" type="number" step="0.01" v-model.number="n0" @input="redraw" />
          <view class="slider-row">
            <slider min="10" max="300" :value="Math.round(n0 * 100)" @change="onN0Slider" />
          </view>
        </view>
        <view class="field">
          <view class="field-label">入射角 (度)</view>
          <input class="field-input" type="number" v-model.number="angleDeg" min="0" max="89" @input="onAngleInput" />
          <view class="slider-row">
            <slider min="0" max="89" :value="angleDeg" show-value @change="onAngleSlider" />
          </view>
        </view>
        <view class="grid-2">
          <view class="field">
            <view class="field-label">薄膜折射率 n₁</view>
            <input class="field-input" type="number" step="0.01" v-model.number="n1" @input="onN1Input" />
            <view class="slider-row">
              <slider min="10" max="450" :value="Math.round(n1 * 100)" @change="onN1Slider" />
            </view>
          </view>
          <view class="field">
            <view class="field-label">衬底折射率 n₂</view>
            <input class="field-input" type="number" step="0.01" v-model.number="n2" @input="onN2Input" />
            <view class="slider-row">
              <slider min="10" max="500" :value="Math.round(n2 * 100)" @change="onN2Slider" />
            </view>
          </view>
        </view>
        <view class="field">
          <view class="field-label">
            薄膜厚度 (μm)
            <text class="val-chip">{{ thickness.toFixed(2) }} μm</text>
          </view>
          <view class="slider-row">
            <slider min="5" max="10000" :value="Math.round(thickness * 100)" @change="onThicknessSlider" />
          </view>
        </view>
        <view class="hero-actions">
          <button class="btn btn-primary" @tap="redraw">更新视图</button>
          <button class="btn btn-ghost" @tap="reset">重置</button>
        </view>
      </view>
    </view>

    <!-- Canvas -->
    <view class="section">
      <canvas
        canvas-id="opticsCanvas"
        id="opticsCanvas"
        class="optics-canvas"
      ></canvas>
      <view class="hint" v-if="tirActive" style="color: #ef4444;">
        ⚠ 全内反射发生（薄膜→衬底界面无折射）
      </view>
      <view class="hint" v-else>
        提示：拖动滑块或直接输入数值调整参数。红→入射，橙→反射，绿→折射。
      </view>
    </view>

    <view style="height: 40px;"></view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      n0: 1.0,
      angleDeg: 30,
      n1: 2.60,
      n2: 2.55,
      thickness: 2.0,
      tirActive: false,
      canvasW: 0,
      canvasH: 0,
    };
  },
  onReady() {
    this.initCanvas();
  },
  onShow() {
    this.$nextTick(() => {
      this.initCanvas();
    });
  },
  methods: {
    initCanvas() {
      const self = this;
      try {
        const query = uni.createSelectorQuery().in(this);
        query.select('#opticsCanvas').boundingClientRect(rect => {
          if (!rect) return;
          self.canvasW = rect.width || 340;
          self.canvasH = Math.max(360, rect.width * 1.1);
          self.redraw();
        }).exec();
      } catch (e) { /* ignore */ }
    },

    onAngleInput() {
      if (this.angleDeg < 0) this.angleDeg = 0;
      if (this.angleDeg > 89) this.angleDeg = 89;
      this.redraw();
    },
    onAngleSlider(e) {
      this.angleDeg = Number(e.detail.value || 0);
      this.redraw();
    },
    onN0Slider(e) {
      this.n0 = (Number(e.detail.value) || 10) / 100;
      this.redraw();
    },
    onN1Input() { if (this.n1 < 0.01) this.n1 = 0.01; this.redraw(); },
    onN2Input() { if (this.n2 < 0.01) this.n2 = 0.01; this.redraw(); },
    onN1Slider(e) {
      this.n1 = (Number(e.detail.value) || 260) / 100;
      this.redraw();
    },
    onN2Slider(e) {
      this.n2 = (Number(e.detail.value) || 255) / 100;
      this.redraw();
    },
    onThicknessSlider(e) {
      this.thickness = (Number(e.detail.value) || 100) / 100;
      this.redraw();
    },
    reset() {
      this.n0 = 1.0;
      this.angleDeg = 30;
      this.n1 = 2.60;
      this.n2 = 2.55;
      this.thickness = 2.0;
      this.redraw();
    },

    redraw() {
      const w = this.canvasW || 340;
      const h = this.canvasH || 360;
      const ctx = uni.createCanvasContext('opticsCanvas', this);

      ctx.clearRect(0, 0, w, h);

      // Background
      ctx.setFillStyle('#0f172a');
      ctx.fillRect(0, 0, w, h);

      const margin = w * 0.06;
      const airH = h * 0.18;
      // Log-scale film height
      const t = Math.max(0.05, this.thickness);
      const filmH = 15 + (Math.log1p(t) / Math.log1p(100)) * 130;
      const y1 = airH;
      const y2 = y1 + filmH;
      const ySub = y2;

      // Air region
      ctx.setFillStyle('rgba(2, 6, 23, 0.6)');
      ctx.fillRect(0, 0, w, y1);

      // Film region
      ctx.setFillStyle('rgba(14, 165, 233, 0.1)');
      ctx.fillRect(0, y1, w, filmH);

      // Substrate region
      ctx.setFillStyle('rgba(30, 41, 59, 0.4)');
      ctx.fillRect(0, y2, w, h - y2);

      // Interface lines
      ctx.setStrokeStyle('rgba(56, 189, 248, 0.5)');
      ctx.setLineWidth(2);
      ctx.beginPath();
      ctx.moveTo(margin, y1);
      ctx.lineTo(w - margin, y1);
      ctx.stroke();
      ctx.setStrokeStyle('rgba(139, 92, 246, 0.4)');
      ctx.beginPath();
      ctx.moveTo(margin, y2);
      ctx.lineTo(w - margin, y2);
      ctx.stroke();

      // Labels
      ctx.setFillStyle('#cbd5e1');
      ctx.setFontSize(11);
      ctx.fillText(`Air n₀=${this.n0.toFixed(2)}`, margin + 6, y1 - 6);
      ctx.fillText(`Film n₁=${this.n1.toFixed(2)}  d=${t.toFixed(2)}μm`, margin + 6, y1 + 14);
      ctx.fillText(`Substrate n₂=${this.n2.toFixed(2)}`, margin + 6, y2 + 16);

      // === Ray tracing ===
      const theta0 = this.angleDeg * Math.PI / 180;
      const n0 = Math.max(0.01, this.n0);
      const n1 = Math.max(0.01, this.n1);
      const n2 = Math.max(0.01, this.n2);

      // Snell: n0*sin(θ0) = n1*sin(θ1) = n2*sin(θ2)
      const sinTh1 = n0 * Math.sin(theta0) / n1;
      let tir1 = false;
      let theta1 = 0;
      if (Math.abs(sinTh1) >= 1) { tir1 = true; } else { theta1 = Math.asin(sinTh1); }

      const sinTh2 = n0 * Math.sin(theta0) / n2;
      let tir2 = false;
      let theta2 = 0;
      if (Math.abs(sinTh2) >= 1) { tir2 = true; } else { theta2 = Math.asin(sinTh2); }

      this.tirActive = tir1 || tir2;

      const L = Math.min(280, w * 0.85);
      const entryX = margin + (w - margin * 2) * 0.30;

      // Normal at entry
      ctx.setStrokeStyle('rgba(148, 163, 184, 0.25)');
      ctx.setLineWidth(1);
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(entryX, y1 - 60);
      ctx.lineTo(entryX, y2 + 30);
      ctx.stroke();
      ctx.setLineDash([]);

      // Incident ray (red)
      const ix = entryX - L * 0.4 * Math.sin(theta0);
      const iy = y1 - L * 0.4 * Math.cos(theta0);
      ctx.setStrokeStyle('#ef4444');
      ctx.setLineWidth(3);
      ctx.beginPath();
      ctx.moveTo(ix, iy);
      ctx.lineTo(entryX, y1);
      ctx.stroke();

      // Reflected ray from surface (orange)
      ctx.setStrokeStyle('#f97316');
      ctx.setLineWidth(3);
      const rx = entryX + L * 0.3 * Math.sin(theta0);
      const ry = y1 - L * 0.3 * Math.cos(theta0);
      ctx.beginPath();
      ctx.moveTo(entryX, y1);
      ctx.lineTo(rx, ry);
      ctx.stroke();

      // Refracted into film (green)
      if (!tir1) {
        const fx = entryX + filmH * Math.tan(theta1);
        const fy = y2;
        ctx.setStrokeStyle('#22c55e');
        ctx.setLineWidth(2.5);
        ctx.beginPath();
        ctx.moveTo(entryX, y1);
        ctx.lineTo(fx, fy);
        ctx.stroke();

        // Reflected at substrate interface (back up)
        const rx2 = fx + filmH * Math.tan(theta1);
        const ry2 = y1;
        ctx.setStrokeStyle('rgba(34, 197, 94, 0.5)');
        ctx.setLineWidth(1.5);
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(fx, fy);
        ctx.lineTo(rx2, ry2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Second reflected ray escapes (blue-purple)
        const ex = rx2 + L * 0.25 * Math.sin(theta0);
        const ey = ry2 - L * 0.25 * Math.cos(theta0);
        ctx.setStrokeStyle('#8b5cf6');
        ctx.setLineWidth(2);
        ctx.beginPath();
        ctx.moveTo(rx2, ry2);
        ctx.lineTo(ex, ey);
        ctx.stroke();

        // Substrate transmission
        if (!tir2) {
          const sx = fx + (h - y2 + 20) * Math.tan(theta2);
          const sy = h;
          ctx.setStrokeStyle('#22d3ee');
          ctx.setLineWidth(2);
          ctx.setLineDash([6, 4]);
          ctx.beginPath();
          ctx.moveTo(fx, fy);
          ctx.lineTo(sx, sy);
          ctx.stroke();
          ctx.setLineDash([]);

          // Normal at substrate interface
          ctx.setStrokeStyle('rgba(148, 163, 184, 0.2)');
          ctx.setLineWidth(1);
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(fx, y2);
          ctx.lineTo(fx, y2 + 40);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }

      // Angle arcs
      ctx.setStrokeStyle('#64748b');
      ctx.setLineWidth(1.2);
      ctx.beginPath();
      ctx.arc(entryX, y1, 35, -theta0, 0, false);
      ctx.stroke();
      ctx.setFillStyle('#ef4444');
      ctx.setFontSize(11);
      ctx.fillText(`θ₀=${this.angleDeg}°`, entryX + 38, y1 - 6);

      if (!tir1) {
        ctx.setStrokeStyle('#64748b');
        ctx.beginPath();
        ctx.arc(entryX, y1, 45, 0, theta1, false);
        ctx.stroke();
        ctx.setFillStyle('#22c55e');
        ctx.fillText(`θ₁=${(theta1 * 180 / Math.PI).toFixed(1)}°`, entryX + 48, y1 + 28);
      }

      ctx.draw();
    }
  }
};
</script>

<style lang="scss">
@import '../../uni.scss';

.optics-canvas {
  width: 100%;
  height: 420px;
  background: #0f172a;
  border-radius: 12px;
  margin-top: 8px;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.val-chip {
  font-size: 12px;
  color: #38bdf8;
  margin-left: 6px;
  font-weight: 600;
}

.hint {
  color: #64748b;
  font-size: 12px;
  margin-top: 8px;
  text-align: center;
}

.slider-row {
  margin-top: 4px;
}
</style>

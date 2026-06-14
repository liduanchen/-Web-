<template>
  <view class="screen">
    <view class="hero">
      <view class="hero-title">分析记录溯源</view>
      <view class="hero-sub">Analytical Traces & Experiment Snapshots</view>
      <view class="hero-actions">
        <button class="btn btn-primary" @tap="loadHistory">刷新记录</button>
      </view>
    </view>

    <!-- Record List -->
    <view class="section">
      <view class="section-title">历史快照索引</view>
      <view class="card">
        <view v-if="!historyList.length" class="card-desc" style="text-align: center; padding: 20px;">
          暂无分析记录，请先在仪表盘执行分析。
        </view>
        <view v-else>
          <view
            class="list-item"
            :class="{ 'list-item-active': activeId === item.id }"
            v-for="item in historyList"
            :key="item.id"
            @tap="openDetail(item.id)"
          >
            <view style="flex: 1;">
              <view style="font-weight: 600; color: #f8fafc;">{{ item.dataset_name }}</view>
              <view class="card-desc" style="display: flex; justify-content: space-between;">
                <text>厚度: {{ (item.thickness || 0).toFixed(3) }} μm</text>
                <text>{{ item.timestamp }}</text>
              </view>
            </view>
            <view class="pill">#{{ item.id }}</view>
          </view>
        </view>
      </view>
    </view>

    <!-- Detail Panel -->
    <view class="section" v-if="detail">
      <view class="section-title">
        记录档案 #{{ detail.id }} : {{ detail.dataset_name }}
      </view>

      <!-- KPI Row -->
      <view class="kpi-row">
        <view class="kpi-card">
          <view class="kpi-label">测算厚度</view>
          <view class="kpi-value kpi-green">{{ (detail.thickness || 0).toFixed(3) }} μm</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">置信度</view>
          <view class="kpi-value kpi-purple">{{ (detail.fit_confidence || 0).toFixed(1) }}%</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">算法</view>
          <view class="kpi-value kpi-blue" style="font-size: 14px;">{{ detail.method }}</view>
        </view>
        <view class="kpi-card">
          <view class="kpi-label">MSE</view>
          <view class="kpi-value" style="font-size: 14px;">{{ (detail.mse || 0).toFixed(5) }}</view>
        </view>
      </view>

      <!-- Spectrum Image -->
      <view class="card" style="margin-top: 12px;" v-if="detail.spectrum_plot_b64">
        <view class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
          <text>干涉光谱拟合图</text>
          <button class="btn btn-sm btn-outline" @tap="downloadImage">保存到相册</button>
        </view>
        <view class="zoom-wrapper">
          <view
            class="zoom-container"
            @touchstart.stop.prevent="onTouchStart"
            @touchmove.stop.prevent="onTouchMove"
            @touchend.stop.prevent="onTouchEnd"
            @tap="onTap"
          >
            <image
              :src="`data:image/png;base64,${detail.spectrum_plot_b64}`"
              mode="widthFix"
              class="plot-image"
              :style="imageStyle"
            />
          </view>
        </view>
      </view>

      <!-- Parameters JSON -->
      <view class="card" style="margin-top: 12px;" v-if="detail.parameters_json">
        <view class="card-title">原始调用参数</view>
        <view class="result-box">{{ formatJson(detail.parameters_json) }}</view>
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
      historyList: [],
      activeId: null,
      detail: null,
      // Zoom
      _scale: 1,
      _translateX: 0,
      _translateY: 0,
      _zoom: null
    };
  },
  computed: {
    imageStyle() {
      const s = this._scale || 1;
      const x = this._translateX || 0;
      const y = this._translateY || 0;
      return `transform: translate(${x}px, ${y}px) scale(${s});`;
    }
  },
  onLoad() {
    this.loadHistory();
  },
  onShow() {
    this.loadHistory();
  },
  onPullDownRefresh() {
    this.loadHistory().then(() => uni.stopPullDownRefresh());
  },
  methods: {
    async loadHistory() {
      try {
        const res = await api.getHistory();
        this.historyList = res.items || [];
      } catch (e) {
        this.historyList = [];
        uni.showToast({ title: '加载历史失败', icon: 'none' });
      }
    },
    async openDetail(id) {
      this.activeId = id;
      // Reset zoom
      this._scale = 1;
      this._translateX = 0;
      this._translateY = 0;
      try {
        const res = await api.getHistoryDetail(id);
        if (res.ok) {
          this.detail = res.data;
          // Scroll to detail
          uni.pageScrollTo({ selector: '.section:last-child', duration: 300 });
        }
      } catch (e) {
        uni.showToast({ title: '调阅历史明细失败', icon: 'none' });
      }
    },
    formatJson(obj) {
      try {
        return JSON.stringify(obj, null, 2);
      } catch (e) {
        return String(obj || '');
      }
    },
    downloadImage() {
      if (!this.detail || !this.detail.spectrum_plot_b64) {
        uni.showToast({ title: '无可下载的图片', icon: 'none' });
        return;
      }
      // #ifdef APP-PLUS
      // Save base64 to temp file then to album
      const bitmap = new plus.nativeObj.Bitmap('temp_bmp');
      bitmap.loadBase64Data(this.detail.spectrum_plot_b64, () => {
        const path = `_doc/epi_history_${this.detail.id}.png`;
        bitmap.save(path, {}, () => {
          bitmap.clear();
          plus.gallery.save(path, () => {
            uni.showToast({ title: '已保存到相册', icon: 'success' });
          }, (err) => {
            uni.showToast({ title: '保存失败: ' + (err.message || ''), icon: 'none' });
          });
        }, (err) => {
          uni.showToast({ title: '写入失败: ' + (err.message || ''), icon: 'none' });
        });
      }, (err) => {
        uni.showToast({ title: '解码失败: ' + (err.message || ''), icon: 'none' });
      });
      // #endif
      // #ifdef H5
      const a = document.createElement('a');
      a.href = `data:image/png;base64,${this.detail.spectrum_plot_b64}`;
      a.download = `history_${this.detail.id}_spectrum.png`;
      a.click();
      uni.showToast({ title: '下载已开始', icon: 'success' });
      // #endif
    },

    // Pinch zoom
    onTouchStart(e) {
      const touches = e.touches || e.changedTouches || [];
      if (!this._zoom) {
        this._zoom = { startDist: null, startScale: this._scale || 1, lastX: 0, lastY: 0, dragging: false };
      }
      if (touches.length === 2) {
        this._zoom.startDist = this._dist(touches[0], touches[1]);
        this._zoom.startScale = this._scale || 1;
      } else if (touches.length === 1) {
        this._zoom.dragging = true;
        this._zoom.lastX = touches[0].clientX;
        this._zoom.lastY = touches[0].clientY;
      }
    },
    onTouchMove(e) {
      const touches = e.touches || e.changedTouches || [];
      if (!this._zoom) return;
      if (touches.length === 2 && this._zoom.startDist) {
        const d = this._dist(touches[0], touches[1]);
        const scale = (d / this._zoom.startDist) * this._zoom.startScale;
        this._scale = Math.max(1, Math.min(scale, 6));
      } else if (touches.length === 1 && this._zoom.dragging && this._scale > 1) {
        this._translateX = (this._translateX || 0) + touches[0].clientX - this._zoom.lastX;
        this._translateY = (this._translateY || 0) + touches[0].clientY - this._zoom.lastY;
        this._zoom.lastX = touches[0].clientX;
        this._zoom.lastY = touches[0].clientY;
      }
    },
    onTouchEnd() {
      if (this._zoom) {
        this._zoom.startDist = null;
        this._zoom.dragging = false;
      }
    },
    onTap() {
      if (this._scale > 1) {
        this._scale = 1;
        this._translateX = 0;
        this._translateY = 0;
      }
    },
    _dist(a, b) {
      const dx = (a.clientX || a.pageX) - (b.clientX || b.pageX);
      const dy = (a.clientY || a.pageY) - (b.clientY || b.pageY);
      return Math.sqrt(dx * dx + dy * dy);
    }
  }
};
</script>

<style lang="scss">
@import '../../uni.scss';

.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.3);
  margin-bottom: 8px;
  transition: all 0.2s;
}
.list-item-active {
  background: rgba(14, 165, 233, 0.08);
  border-color: rgba(56, 189, 248, 0.5);
}

.pill {
  background: rgba(14, 165, 233, 0.15);
  color: #38bdf8;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  margin-left: 8px;
}

.kpi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
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
  font-size: 20px;
  font-weight: 700;
  color: #f8fafc;
}
.kpi-green { color: #10b981; }
.kpi-purple { color: #a78bfa; }
.kpi-blue { color: #38bdf8; }

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

.result-box {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #a7f3d0;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 12px;
  white-space: pre-wrap;
  line-height: 1.5;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 11px;
}
.btn-outline {
  background: transparent;
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
}
</style>

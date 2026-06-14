<template>
  <view class="screen">
    <view class="hero">
      <view class="hero-title">折射率定制数据库</view>
      <view class="hero-sub">Refractive Index Parameters Library</view>
      <view class="hero-actions">
        <button class="btn btn-primary" @tap="loadMaterials">刷新</button>
      </view>
    </view>

    <!-- Add / Update -->
    <view class="section">
      <view class="section-title">添加或更新材料</view>
      <view class="card">
        <view class="field">
          <view class="field-label">材料标识 (唯一名)</view>
          <input class="field-input" v-model="form.name" placeholder="e.g. SiC" />
        </view>
        <view class="grid-2">
          <view class="field">
            <view class="field-label">外延层参考 n_film</view>
            <input class="field-input" type="number" step="0.01" v-model="form.n_film" placeholder="2.60" />
          </view>
          <view class="field">
            <view class="field-label">衬底参考 n_sub</view>
            <input class="field-input" type="number" step="0.01" v-model="form.n_sub" placeholder="2.55" />
          </view>
        </view>
        <view class="hero-actions">
          <button class="btn btn-secondary" @tap="saveMaterial">保存数据</button>
          <text class="status-text" v-if="statusText">{{ statusText }}</text>
        </view>
      </view>
    </view>

    <!-- Inventory -->
    <view class="section">
      <view class="section-title">材料库存</view>
      <view class="card">
        <view v-if="!materials.length" class="card-desc" style="text-align: center; padding: 20px;">
          暂无自定义材料，系统已预置 SiC / Si / GaN / GaAs
        </view>
        <view v-else>
          <view class="list-item" v-for="item in materials" :key="item.id">
            <view style="flex: 1;">
              <view style="font-weight: 600; color: #f8fafc;">{{ item.name }}</view>
              <view class="card-desc">
                n_film: {{ (item.n_film || 0).toFixed(2) }} | n_sub: {{ (item.n_sub || 0).toFixed(2) }}
              </view>
            </view>
            <button class="btn btn-ghost btn-danger" @tap="removeMaterial(item.name)">删除</button>
          </view>
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
      materials: [],
      form: {
        name: '',
        n_film: '',
        n_sub: ''
      },
      statusText: ''
    };
  },
  onLoad() {
    this.loadMaterials();
  },
  onShow() {
    this.loadMaterials();
  },
  onPullDownRefresh() {
    this.loadMaterials().then(() => uni.stopPullDownRefresh());
  },
  methods: {
    async loadMaterials() {
      try {
        const res = await api.getMaterials();
        this.materials = res.items || [];
      } catch (e) {
        this.materials = [];
        uni.showToast({ title: '加载失败', icon: 'none' });
      }
    },
    async saveMaterial() {
      if (!this.form.name || !this.form.n_film || !this.form.n_sub) {
        this.statusText = '请填写所有字段';
        return;
      }
      try {
        const res = await api.addMaterial({
          name: this.form.name.trim(),
          n_film: parseFloat(this.form.n_film),
          n_sub: parseFloat(this.form.n_sub)
        });
        if (res.ok) {
          this.statusText = '✓ 已保存';
          this.form.name = '';
          this.form.n_film = '';
          this.form.n_sub = '';
          uni.showToast({ title: '材料保存成功', icon: 'success' });
          this.loadMaterials();
        } else {
          this.statusText = res.error || '保存失败';
          uni.showToast({ title: res.error || '保存失败', icon: 'none' });
        }
      } catch (e) {
        this.statusText = '保存失败';
        uni.showToast({ title: e.message || '保存失败', icon: 'none' });
      }
    },
    async removeMaterial(name) {
      uni.showModal({
        title: '确认删除',
        content: `确定要移除 "${name}" 的折射率预设吗？`,
        success: async (res) => {
          if (res.confirm) {
            try {
              const r = await api.deleteMaterial(name);
              if (r.ok) {
                uni.showToast({ title: '已安全移除', icon: 'success' });
                this.loadMaterials();
              } else {
                uni.showToast({ title: r.error || '删除失败', icon: 'none' });
              }
            } catch (e) {
              uni.showToast({ title: e.message || '删除失败', icon: 'none' });
            }
          }
        }
      });
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
}

.btn-secondary {
  background: rgba(14, 165, 233, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
}

.btn-danger {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
  font-size: 12px;
  padding: 4px 12px;
}

.status-text {
  font-size: 13px;
  color: #10b981;
  margin-left: 8px;
}
</style>

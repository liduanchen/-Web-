const messages = {
  'zh-CN': {
    'header.title': 'EPI 视界',
    tab: {
      dashboard: '仪表盘',
      history: '历史',
      materials: '材料',
      simulator: '模拟器'
    },
    page: {
      simulator: '模拟器',
      history: '历史',
      materials: '材料',
      visualization: '3D 可视化',
      dispersion: '复折射率模型'
    },
    btn: {
      run: '运行',
      suggest: '建议截止',
      refresh: '刷新',
      update: '更新'
    },
    misc: {
      dataset: '数据集',
      material: '材料',
      angle: '入射角',
      thickness: '厚度',
      confidence: '置信度'
    }
  },
  'en': {
    'header.title': 'EPI Vision',
    tab: {
      dashboard: 'Dashboard',
      history: 'History',
      materials: 'Materials',
      simulator: 'Simulator'
    },
    page: {
      simulator: 'Simulator',
      history: 'History',
      materials: 'Materials',
      visualization: '3D Visualization',
      dispersion: 'Dispersion Model'
    },
    btn: {
      run: 'Run',
      suggest: 'Suggest Cutoff',
      refresh: 'Refresh',
      update: 'Update'
    },
    misc: {}
  }
};

let locale = 'zh-CN';

export function setLocale(l) {
  if (messages[l]) locale = l;
}

export function t(key) {
  const parts = key.split('.');
  let node = messages[locale] || {};
  for (const p of parts) {
    if (node && Object.prototype.hasOwnProperty.call(node, p)) node = node[p];
    else return key;
  }
  return typeof node === 'string' ? node : key;
}

export default { t, setLocale };

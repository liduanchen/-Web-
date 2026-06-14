import config from './config';

const buildHeaders = (token) => {
  const headers = {
    'Content-Type': 'application/json'
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

const request = ({ url, method = 'GET', data = {}, token }) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${config.baseUrl}${url}`,
      method,
      data,
      header: buildHeaders(token),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        // Try to extract error message from response body
        const body = res.data;
        const msg = (body && (body.error || body.message)) || `HTTP ${res.statusCode}`;
        reject(new Error(msg));
      },
      fail: (err) => {
        reject(new Error(err.errMsg || 'Network request failed'));
      }
    });
  });
};

const upload = ({ url, filePath, name = 'file', formData = {} }) => {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${config.baseUrl}${url}`,
      filePath,
      name,
      formData,
      success: (res) => {
        try {
          const parsed = JSON.parse(res.data || '{}');
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(parsed);
            return;
          }
          reject(new Error(parsed.error || `HTTP ${res.statusCode}`));
        } catch (error) {
          reject(new Error('Invalid server response'));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || 'Upload failed'));
      }
    });
  });
};

export const api = {
  // Health
  getHealth() {
    return request({ url: '/api/health' });
  },

  // Datasets (API-driven, not hardcoded)
  getDatasets() {
    return request({ url: '/api/datasets' });
  },
  getDatasetData(params) {
    return request({ url: '/api/dataset_data', data: params });
  },

  // Import
  importDataset({ filePath, formData }) {
    return upload({ url: '/api/import', filePath, formData });
  },

  // Materials CRUD
  getMaterials() {
    return request({ url: '/api/materials' });
  },
  addMaterial(payload) {
    return request({ url: '/api/materials', method: 'POST', data: payload });
  },
  deleteMaterial(name) {
    return request({ url: `/api/materials/${encodeURIComponent(name)}`, method: 'DELETE' });
  },

  // Analysis helpers
  suggestCutoff(payload) {
    return request({ url: '/api/suggest_cutoff', method: 'POST', data: payload });
  },

  // Main analysis endpoint — sends method + inversion matching Flask API
  analyze(payload) {
    return request({ url: '/api/analyze', method: 'POST', data: payload });
  },

  // History
  getHistory() {
    return request({ url: '/api/history' });
  },
  getHistoryDetail(id) {
    return request({ url: `/api/history/${id}` });
  },

  // Visualization plots (server-rendered base64 PNGs)
  getPlotWafer(params) {
    return request({ url: '/api/plot/wafer', method: 'POST', data: params });
  },
  getPlotCrystal(params) {
    return request({ url: '/api/plot/crystal', method: 'POST', data: params });
  },
  getPlotStandingWave(params) {
    return request({ url: '/api/plot/standing-wave', method: 'POST', data: params });
  },
  getPlotDispersion(params) {
    return request({ url: '/api/plot/dispersion', method: 'POST', data: params });
  }
};

import { create } from 'zustand';
import api from '../services/api';

const useDiagnosticsStore = create((set) => ({
  queueCount: 0,
  async refreshQueueCount() {
    const response = await api.get('/diagnostics/queue');
    set({ queueCount: response.data.count || 0 });
  },
  async saveDiagnostics(payload) {
    const response = await api.post('/diagnostics/save', payload);
    set({ queueCount: response.data.count || 0 });
    return response.data;
  },
  async exportDiagnostics() {
    const response = await api.post('/diagnostics/export');
    set({ queueCount: 0 });
    return response.data;
  },
}));

export default useDiagnosticsStore;

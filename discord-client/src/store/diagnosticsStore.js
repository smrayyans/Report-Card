import { create } from 'zustand';
import api from '../services/api';

const useDiagnosticsStore = create((set) => ({
  queueCount: 0,
  queueItems: [],
  async refreshQueueCount() {
    const response = await api.get('/diagnostics/queue');
    set({ queueCount: response.data.count || 0 });
  },
  async refreshQueueItems() {
    const response = await api.get('/diagnostics/queue/items');
    set({ queueItems: response.data.items || [] });
  },
  async saveDiagnostics(payload) {
    const response = await api.post('/diagnostics/save', payload);
    set({ queueCount: response.data.count || 0 });
    return response.data;
  },
  async updateQueuedDiagnostics(queueId, payload) {
    const response = await api.put(`/diagnostics/queue/${queueId}`, payload);
    set({ queueCount: response.data.count || 0 });
    return response.data;
  },
  async clearQueue() {
    const response = await api.delete('/diagnostics/queue');
    set({ queueCount: response.data.count || 0, queueItems: [] });
    return response.data;
  },
  async exportDiagnostics() {
    const response = await api.post('/diagnostics/export');
    set({ queueCount: 0 });
    return response.data;
  },
}));

export default useDiagnosticsStore;

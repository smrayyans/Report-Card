import { create } from 'zustand';
import api from '../services/api';

const useReportStore = create((set, get) => ({
  config: null,
  filters: {},
  remarks: [],
  subjects: [],
  loading: false,
  queueCount: 0,
  async fetchInitial() {
    if (get().loading) return;
    set({ loading: true });
    try {
      const [configRes, filtersRes, remarksRes, subjectsRes] = await Promise.all([
        api.get('/config'),
        api.get('/filters'),
        api.get('/remarks'),
        api.get('/subjects'),
      ]);

      set({
        config: configRes.data,
        filters: filtersRes.data.filters || {},
        remarks: remarksRes.data.presets || [],
        subjects: subjectsRes.data,
        loading: false,
      });
    } catch (error) {
      console.error(error);
      set({ loading: false });
      throw error;
    }
  },
  async refreshQueueCount() {
    const response = await api.get('/reports/queue');
    set({ queueCount: response.data.count || 0 });
  },
  async saveFilters(nextFilters) {
    await api.put('/filters', { filters: nextFilters });
    set({ filters: nextFilters });
  },
  async saveRemarks(nextRemarks) {
    await api.put('/remarks', { presets: nextRemarks });
    set({ remarks: nextRemarks });
  },
  async saveConfig(nextConfig) {
    await api.put('/config', nextConfig);
    set({ config: nextConfig });
  },
  async createSubject(subjectName, type = 'Core') {
    const response = await api.post('/subjects', { subject_name: subjectName, type });
    const newSubject = { subject_name: response.data.subject_name, type: response.data.type };
    set((state) => ({ subjects: [...state.subjects, newSubject].sort((a, b) => a.subject_name.localeCompare(b.subject_name)) }));
    return newSubject;
  },
  async updateSubject(oldName, newName, type) {
    const response = await api.put(`/subjects/${encodeURIComponent(oldName)}`, { new_name: newName, type });
    set((state) => ({
      subjects: state.subjects
        .map((s) => (s.subject_name === oldName ? { subject_name: response.data.subject_name, type: response.data.type } : s))
        .sort((a, b) => a.subject_name.localeCompare(b.subject_name)),
    }));
    return response.data;
  },
  async deleteSubject(subjectName) {
    await api.delete(`/subjects/${encodeURIComponent(subjectName)}`);
    set((state) => ({ subjects: state.subjects.filter((s) => s.subject_name !== subjectName) }));
  },
  async saveReport(payload) {
    const response = await api.post('/reports/save', payload);
    set({ queueCount: response.data.count || 0 });
    return response.data;
  },
  async exportReports() {
    const response = await api.post('/reports/export');
    set({ queueCount: 0 });
    return response.data;
  },

}));

export default useReportStore;

import { create } from 'zustand';
import api from '../services/api';

const useStudentStore = create((set, get) => ({
  students: [],
  stats: { total: 0, active: 0, inactive: 0 },
  classes: [],
  loading: false,
  detail: null,
  detailLoading: false,
  importLoading: false,
  history: [],
  historyLoading: false,
  totalStudents: 0,
  currentOffset: 0,
  hasMore: false,
  loadingMore: false,
  fetchStudents: async (filters) => {
    set({ loading: true, currentOffset: 0 });
    try {
      const params = { limit: 15, offset: 0 };
      if (filters?.search) params.search = filters.search;
      if (filters?.class_sec && filters.class_sec !== 'All') params.class_sec = filters.class_sec;
      if (filters?.status && filters.status !== 'All') params.status = filters.status;
      const response = await api.get('/students', { params });
      const { students, total, offset } = response.data;
      set({
        students,
        totalStudents: total,
        currentOffset: offset + students.length,
        hasMore: offset + students.length < total,
        loading: false
      });
    } catch (error) {
      console.error(error);
      set({ loading: false });
      throw error;
    }
  },
  loadMoreStudents: async (filters) => {
    const { currentOffset, loadingMore } = get();
    if (loadingMore) return;

    set({ loadingMore: true });
    try {
      const params = { limit: 15, offset: currentOffset };
      if (filters?.search) params.search = filters.search;
      if (filters?.class_sec && filters.class_sec !== 'All') params.class_sec = filters.class_sec;
      if (filters?.status && filters.status !== 'All') params.status = filters.status;
      const response = await api.get('/students', { params });
      const { students: newStudents, total, offset } = response.data;
      set((state) => ({
        students: (() => {
          const seen = new Set(state.students.map((student) => student.gr_no));
          const merged = [...state.students];
          newStudents.forEach((student) => {
            if (!seen.has(student.gr_no)) {
              seen.add(student.gr_no);
              merged.push(student);
            }
          });
          return merged;
        })(),
        totalStudents: total,
        currentOffset: offset + newStudents.length,
        hasMore: offset + newStudents.length < total,
        loadingMore: false
      }));
    } catch (error) {
      console.error(error);
      set({ loadingMore: false });
      throw error;
    }
  },
  fetchStats: async () => {
    try {
      const response = await api.get('/students/stats');
      set({ stats: response.data });
    } catch (error) {
      console.error(error);
    }
  },
  fetchClasses: async () => {
    try {
      const response = await api.get('/students/classes');
      set({ classes: ['All Classes', ...response.data] });
    } catch (error) {
      console.error(error);
    }
  },
  fetchStudentDetail: async (grNo) => {
    if (!grNo) return null;
    set({ detailLoading: true });
    try {
      const response = await api.get(`/students/${grNo}`);
      set({ detail: response.data, detailLoading: false });
      return response.data;
    } catch (error) {
      set({ detailLoading: false });
      throw error;
    }
  },
  fetchReportHistory: async (grNo) => {
    if (!grNo) return [];
    set({ historyLoading: true });
    try {
      const response = await api.get(`/reports/history/${encodeURIComponent(grNo)}`);
      set({ history: response.data.items || [], historyLoading: false });
      return response.data.items || [];
    } catch (error) {
      set({ historyLoading: false });
      throw error;
    }
  },
  downloadReportHistoryPdf: async (resultId) => {
    if (!resultId) return null;
    const response = await api.get(`/reports/history/${resultId}/pdf`);
    return response.data;
  },
  clearDetail: () => set({ detail: null }),
  importStudents: async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    set({ importLoading: true });
    try {
      const response = await api.post('/students/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      set({ importLoading: false });
      return response.data;
    } catch (error) {
      set({ importLoading: false });
      throw error;
    }
  },
  updateStudent: async (grNo, updates) => {
    if (!grNo || !updates) return;
    try {
      const response = await api.put(`/students/${grNo}`, updates);
      // Update the detail if it's currently loaded
      set({ detail: response.data });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  deleteStudent: async (grNo) => {
    if (!grNo) return;
    try {
      await api.delete(`/students/${grNo}`);
      set({ detail: null });
    } catch (error) {
      throw error;
    }
  },
}));

export default useStudentStore;

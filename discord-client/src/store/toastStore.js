import { create } from 'zustand';

const useToastStore = create((set, get) => ({
  toasts: [],
  pushToast: ({ title, message, type = 'info', duration = 4000, openOutput = false }) => {
    const id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    const toast = { id, title, message, type, duration, openOutput };
    set((state) => ({ toasts: [...state.toasts, toast] }));

    setTimeout(() => {
      const exists = get().toasts.find((entry) => entry.id === id);
      if (exists) {
        get().dismissToast(id);
      }
    }, duration);
    return id;
  },
  dismissToast: (id) => {
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  },
}));

export default useToastStore;

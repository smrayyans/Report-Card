import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import ToastStack from './components/ToastStack';
import LoginPage from './pages/LoginPage';
import StudentsPage from './pages/StudentsPage';
import ReportsPage from './pages/ReportsPage';
import DiagnosticsPage from './pages/DiagnosticsPage';
import SettingsPage from './pages/SettingsPage';
import useAuthStore from './store/authStore';
import './styles/global.css';

function App() {
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    const handleBeforeUnload = () => {
      // Clear auth state on window close
      logout();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [logout]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/students" replace />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/diagnostics" element={<DiagnosticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <ToastStack />
    </BrowserRouter>
  );
}

export default App;

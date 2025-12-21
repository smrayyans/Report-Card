import { Navigate, Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import useAuthStore from '../store/authStore';

const routeMeta = [
  {
    path: '/students',
    title: 'Student Intelligence Hub',
    subtitle: 'Search, filter, and celebrate every student with Discord-tier polish.',
  },
  {
    path: '/reports',
    title: 'Report Studio',
    subtitle: 'Craft cinematic report cards with live totals and PDF export.',
  },
  {
    path: '/diagnostics',
    title: 'Diagnostics Lab',
    subtitle: 'Capture skill-by-skill diagnostics with quick ratings and comments.',
  },
  {
    path: '/settings',
    title: 'Control Center',
    subtitle: 'Configure sessions, subjects, and presets to match your academy.',
  },
];

function resolveMeta(pathname) {
  return routeMeta.find((meta) => pathname.startsWith(meta.path)) || routeMeta[0];
}

export default function MainLayout() {
  const user = useAuthStore((state) => state.user);
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const meta = resolveMeta(location.pathname);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar title={meta.title} subtitle={meta.subtitle} />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

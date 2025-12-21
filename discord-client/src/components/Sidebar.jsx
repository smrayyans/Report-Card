import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import useAuthStore from '../store/authStore';

const navItems = [
  {
    to: '/students',
    label: 'Students',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24">
        <path
          d="M12 12c2.761 0 5-2.239 5-5S14.761 2 12 2 7 4.239 7 7s2.239 5 5 5zm0 2c-3.309 0-10 1.654-10 5v1h20v-1c0-3.346-6.691-5-10-5z"
          fill="currentColor"
        />
      </svg>
    ),
  },
  {
    to: '/reports',
    label: 'Reports',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24">
        <path d="M6 2h9l5 5v15H6z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
        <path d="M14 2v6h6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: '/diagnostics',
    label: 'Diagnostics',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24">
        <path
          d="M4 5h16v14H4z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path d="M7 9h10M7 13h6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: '/settings',
    label: 'Settings',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24">
        <path
          d="M19.14 12.936c.036-.305.06-.616.06-.936s-.024-.631-.07-.936l2.11-1.65a.5.5 0 00.12-.63l-2-3.464a.5.5 0 00-.6-.22l-2.49 1a7.083 7.083 0 00-1.62-.936l-.38-2.65A.5.5 0 0013.77 2h-3.54a.5.5 0 00-.5.424l-.38 2.65a7.083 7.083 0 00-1.62.936l-2.49-1a.5.5 0 00-.6.22l-2 3.464a.5.5 0 00.12.63l2.11 1.65c-.046.305-.07.616-.07.936s.024.631.07.936l-2.11 1.65a.5.5 0 00-.12.63l2 3.464a.5.5 0 00.6.22l2.49-1c.5.39 1.04.71 1.62.936l.38 2.65a.5.5 0 00.5.424h3.54a.5.5 0 00.5-.424l.38-2.65a7.083 7.083 0 001.62-.936l2.49 1a.5.5 0 00.6-.22l2-3.464a.5.5 0 00-.12-.63l-2.11-1.65zM12 15.5A3.5 3.5 0 1115.5 12 3.5 3.5 0 0112 15.5z"
          fill="currentColor"
        />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const user = useAuthStore((state) => state.user);
  const initials = user?.username?.slice(0, 2)?.toUpperCase() || 'FA';
  return (
    <aside className="sidebar">
      <div className="sidebar__logo">
        <span>{initials}</span>
      </div>
      <nav className="sidebar__nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx('sidebar__button', isActive && 'sidebar__button--active')}
          >
            <span className="sidebar__icon">{item.icon}</span>
            <span className="sidebar__tooltip">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

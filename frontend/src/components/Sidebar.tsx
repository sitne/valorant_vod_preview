import React from 'react';
import { NavLink } from 'react-router-dom';
import { Tv, Grid, Settings, Activity } from 'lucide-react';

export const Sidebar: React.FC = () => {
    const navItems = [
        { icon: Tv, label: 'Videos', path: '/' },
        { icon: Grid, label: 'Rounds', path: '/rounds' },
        { icon: Activity, label: 'Analysis', path: '/analysis' },
        { icon: Settings, label: 'Config', path: '/config' },
    ];

    return (
        <div className="sidebar">
            <div className="header" style={{ justifyContent: 'center' }}>
                <h2 style={{ fontSize: '1.2rem', color: 'var(--accent)' }}>V-SCOUT</h2>
            </div>
            <nav style={{ flex: 1, padding: '1rem 0' }}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `nav-item ${isActive ? 'active' : ''}`
                        }
                        style={({ isActive }) => ({
                            display: 'flex',
                            alignItems: 'center',
                            padding: '1rem 1.5rem',
                            color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                            background: isActive ? 'linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%)' : 'transparent',
                            borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                            textDecoration: 'none',
                            transition: 'all 0.2s',
                            gap: '1rem'
                        })}
                    >
                        <item.icon size={20} />
                        <span style={{ fontWeight: 500 }}>{item.label}</span>
                    </NavLink>
                ))}
            </nav>
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    System Status: <span style={{ color: 'var(--success)' }}>Online</span>
                </div>
            </div>
        </div>
    );
};

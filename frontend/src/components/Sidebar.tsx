import React from 'react';
import { NavLink } from 'react-router-dom';
import { Tv, Grid, Settings, Activity } from 'lucide-react';

export const Sidebar: React.FC = () => {
    const navItems = [
        { icon: Tv, label: 'ビデオ', path: '/', description: '動画アップロード' },
        { icon: Activity, label: '分析', path: '/analysis', description: '処理状況' },
        { icon: Grid, label: 'ラウンド', path: '/rounds', description: '検出結果' },
        { icon: Settings, label: '設定', path: '/config', description: '詳細設定' },
    ];

    return (
        <div className="sidebar">
            {/* ロゴエリア - Spatial Consistency: 常に上部固定 */}
            <div className="header" style={{ justifyContent: 'center' }}>
                <h2 style={{ fontSize: '1.2rem', color: 'var(--accent)', margin: 0 }}>V-SCOUT</h2>
            </div>

            {/* ナビゲーション - Gestalt: 論理的なグループ化 */}
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
                            padding: '0.75rem 1.5rem',
                            color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                            background: isActive ? 'linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%)' : 'transparent',
                            borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                            textDecoration: 'none',
                            transition: 'all 0.15s', // 即座フィードバック
                            gap: '1rem',
                            position: 'relative',
                            cursor: 'pointer'
                        })}
                        onMouseEnter={e => {
                            const element = e.currentTarget;
                            if (!element.classList.contains('active')) {
                                element.style.color = 'var(--text-primary)';
                                element.style.paddingLeft = '1.75rem';
                            }
                        }}
                        onMouseLeave={e => {
                            const element = e.currentTarget;
                            if (!element.classList.contains('active')) {
                                element.style.color = 'var(--text-secondary)';
                                element.style.paddingLeft = '1.5rem';
                            }
                        }}
                    >
                        <item.icon size={20} style={{ flexShrink: 0 }} />
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <span style={{ fontWeight: 500 }}>{item.label}</span>
                            <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                                {item.description}
                            </span>
                        </div>
                    </NavLink>
                ))}
            </nav>

            {/* フッター - Spatial Consistency: 常に下部固定 */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: 'var(--success)',
                        animation: 'pulse 2s infinite'
                    }} />
                    <span>システム正常</span>
                </div>
            </div>

            <style>{`
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `}</style>
        </div>
    );
};

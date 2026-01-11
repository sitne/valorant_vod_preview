import React, { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: ReactNode;
    title?: string;
    actions?: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children, title, actions }) => {
    return (
        <div style={{ display: 'flex' }}>
            <Sidebar />
            <div className="main-content" style={{ flex: 1 }}>
                <header style={{
                    marginBottom: '2rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    {title && <h1>{title}</h1>}
                    {actions && <div>{actions}</div>}
                </header>
                <main>{children}</main>
            </div>
        </div>
    );
};

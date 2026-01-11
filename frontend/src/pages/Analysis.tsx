import React, { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { getStatus, stopAnalyze, type JobStatus } from '../api';
import { Square, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Analysis: React.FC = () => {
    const [status, setStatus] = useState<JobStatus | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const poll = async () => {
            try {
                const s = await getStatus();
                setStatus(s);
            } catch (e) {
                console.error(e);
            }
        };

        poll();
        const interval = setInterval(poll, 1000);
        return () => clearInterval(interval);
    }, []);

    const handleStop = async () => {
        if (confirm('Are you sure you want to stop the analysis?')) {
            await stopAnalyze();
        }
    };

    if (!status) return <Layout>Loading...</Layout>;

    return (
        <Layout title="Analysis Dashboard">
            <div className="card" style={{ maxWidth: '800px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                            {status.is_running ? 'Processing Video...' : 'Status: ' + status.status}
                        </h2>
                        <div style={{ color: 'var(--text-secondary)' }}>
                            Job ID: {status.id || 'N/A'}
                        </div>
                    </div>
                    {status.is_running && (
                        <button className="btn" onClick={handleStop} style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>
                            <Square size={16} fill="currentColor" /> Stop
                        </button>
                    )}
                </div>

                {/* Progress Bar */}
                <div style={{ background: 'var(--bg-tertiary)', height: '8px', borderRadius: '4px', overflow: 'hidden', marginBottom: '1rem' }}>
                    <div style={{
                        width: `${status.progress * 100}%`,
                        background: 'var(--accent)',
                        height: '100%',
                        transition: 'width 0.5s ease'
                    }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <span> Progress </span>
                    <span> {(status.progress * 100).toFixed(1)}% </span>
                </div>

                {/* Current Activity Log */}
                <div style={{
                    marginTop: '2rem',
                    background: 'var(--bg-primary)',
                    padding: '1rem',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                    color: status.is_running ? 'var(--text-primary)' : 'var(--text-secondary)'
                }}>
                    {"> " + status.status}
                </div>

                {!status.is_running && status.progress >= 1.0 && (
                    <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                        <div style={{ color: 'var(--success)', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                            <CheckCircle /> Analysis Complete
                        </div>
                        <button className="btn btn-primary" onClick={() => navigate('/rounds')}>
                            View Results
                        </button>
                    </div>
                )}
            </div>
        </Layout>
    );
};

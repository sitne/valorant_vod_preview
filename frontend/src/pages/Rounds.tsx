import React, { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { getRounds, type Round } from '../api';
import { Filter } from 'lucide-react';

export const Rounds: React.FC = () => {
    const [rounds, setRounds] = useState<Round[]>([]);

    useEffect(() => {
        getRounds().then(res => setRounds(res.rounds));
    }, []);

    return (
        <Layout title="Detected Rounds">
            <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
                <div className="btn">
                    <Filter size={16} /> Filter
                </div>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: '1.5rem'
            }}>
                {rounds.map(r => (
                    <div key={r.round} className="card" style={{ padding: 0, overflow: 'hidden', cursor: 'pointer', transition: 'transform 0.2s' }}>
                        <div style={{ aspectRatio: '1/1', background: 'var(--bg-primary)', position: 'relative' }}>
                            <img
                                src={r.image_url}
                                alt={`Round ${r.round}`}
                                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                            />
                            <div style={{
                                position: 'absolute',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                background: 'rgba(0,0,0,0.7)',
                                padding: '0.5rem',
                                fontSize: '0.9rem',
                                fontWeight: 600
                            }}>
                                Round {r.round}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Layout>
    );
};

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { startAnalyze } from '../api';
import { Play } from 'lucide-react';

export const Videos: React.FC = () => {
    const navigate = useNavigate();
    const [localPath, setLocalPath] = useState('');
    const [url, setUrl] = useState('');
    const [startTime, setStartTime] = useState<string>('');
    const [endTime, setEndTime] = useState<string>('');
    const [loading, setLoading] = useState(false);

    const handleStart = async () => {
        try {
            setLoading(true);
            await startAnalyze({
                local_video_path: localPath || undefined,
                video_url: url || undefined,
                start_time: startTime ? parseTime(startTime) : undefined,
                end_time: endTime ? parseTime(endTime) : undefined,
            });
            navigate('/analysis');
        } catch (e) {
            alert('Failed to start analysis: ' + e);
        } finally {
            setLoading(false);
        }
    };

    const parseTime = (t: string) => {
        // Basic parser, just returns seconds or assumes seconds if int
        // In real app, reuse the python logic or precise parser
        // For now assuming the user inputs seconds or mm:ss
        if (t.includes(':')) {
            const parts = t.split(':').map(Number);
            if (parts.length === 2) return parts[0] * 60 + parts[1];
            if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
        }
        return parseFloat(t);
    };

    return (
        <Layout title="Videos">
            <div className="card" style={{ maxWidth: '600px' }}>
                <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>New Analysis</h3>

                <div style={{ display: 'grid', gap: '1rem' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Local Video Path</label>
                        <input
                            type="text"
                            value={localPath}
                            onChange={e => setLocalPath(e.target.value)}
                            placeholder="C:\path\to\video.mp4"
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>OR</div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>YouTube URL</label>
                        <input
                            type="text"
                            value={url}
                            onChange={e => setUrl(e.target.value)}
                            placeholder="https://youtube.com/..."
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Start Time (opt)</label>
                            <input
                                type="text"
                                value={startTime}
                                onChange={e => setStartTime(e.target.value)}
                                placeholder="00:00"
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>End Time (opt)</label>
                            <input
                                type="text"
                                value={endTime}
                                onChange={e => setEndTime(e.target.value)}
                                placeholder="00:00"
                                style={{ width: '100%' }}
                            />
                        </div>
                    </div>

                    <button
                        className="btn btn-primary"
                        style={{ marginTop: '1.5rem', justifyContent: 'center' }}
                        onClick={handleStart}
                        disabled={loading}
                    >
                        <Play size={18} />
                        {loading ? 'Starting...' : 'Start Analysis'}
                    </button>
                </div>
            </div>
        </Layout>
    );
};

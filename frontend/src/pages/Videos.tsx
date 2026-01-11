import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { startAnalyze } from '../api';
import { Play, AlertCircle } from 'lucide-react';

export const Videos: React.FC = () => {
    const navigate = useNavigate();
    const [localPath, setLocalPath] = useState('');
    const [url, setUrl] = useState('');
    const [startTime, setStartTime] = useState<string>('');
    const [endTime, setEndTime] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // 入力形式柔軟性: mm:ss, hh:mm:ss, 秒数を自動判定
    const parseTime = (t: string): number => {
        if (!t) return 0;
        t = t.trim();
        
        if (t.includes(':')) {
            const parts = t.split(':').map(Number).filter(n => !isNaN(n));
            if (parts.length === 2) return parts[0] * 60 + parts[1];
            if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
        }
        return parseFloat(t) || 0;
    };

    // 入力バリデーション
    const validateInputs = (): boolean => {
        setError('');
        if (!localPath && !url) {
            setError('ローカルパスまたはURLを入力してください');
            return false;
        }
        if (startTime && parseTime(startTime) < 0) {
            setError('開始時刻は0以上である必要があります');
            return false;
        }
        if (endTime && parseTime(endTime) < 0) {
            setError('終了時刻は0以上である必要があります');
            return false;
        }
        if (startTime && endTime && parseTime(startTime) > parseTime(endTime)) {
            setError('開始時刻は終了時刻より前である必要があります');
            return false;
        }
        return true;
    };

    const handleStart = async () => {
        if (!validateInputs()) return;

        try {
            setLoading(true);
            setError('');
            await startAnalyze({
                local_video_path: localPath || undefined,
                video_url: url || undefined,
                start_time: startTime ? parseTime(startTime) : undefined,
                end_time: endTime ? parseTime(endTime) : undefined,
            });
            navigate('/analysis');
        } catch (e) {
            setError('分析の開始に失敗しました: ' + e);
        } finally {
            setLoading(false);
        }
    };

    // キーボードショートカット (Enter でも開始可能)
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            handleStart();
        }
    };

    return (
        <Layout title="ビデオ分析">
            <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
                <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    新規分析を開始
                </h3>

                {/* エラーメッセージ: Gestalt原則に基づくグループ化 */}
                {error && (
                    <div style={{
                        display: 'flex',
                        gap: '0.75rem',
                        padding: '0.75rem 1rem',
                        background: 'rgba(255, 70, 85, 0.1)',
                        border: '1px solid var(--accent)',
                        borderRadius: '4px',
                        marginBottom: '1.5rem',
                        alignItems: 'center'
                    }}>
                        <AlertCircle size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                        <span style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{error}</span>
                    </div>
                )}

                <div style={{ display: 'grid', gap: '1.5rem' }} onKeyDown={handleKeyDown}>
                    {/* ビデオソース選択 - Gestalt: ローカル/URL をグループ化 */}
                    <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
                        <legend style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                            ビデオソース (必須)
                        </legend>
                        <div style={{ display: 'grid', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>
                                    ローカルファイルパス
                                </label>
                                <input
                                    type="text"
                                    value={localPath}
                                    onChange={e => setLocalPath(e.target.value)}
                                    placeholder="C:\path\to\video.mp4 or /path/to/video.mp4"
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        background: 'var(--bg-primary)',
                                        color: 'var(--text-primary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '4px',
                                        fontSize: '0.9rem',
                                        transition: 'border-color 0.1s'
                                    }}
                                    onFocus={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                                    onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}
                                />
                            </div>

                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                または
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>
                                    YouTube URL
                                </label>
                                <input
                                    type="text"
                                    value={url}
                                    onChange={e => setUrl(e.target.value)}
                                    placeholder="https://youtube.com/..."
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        background: 'var(--bg-primary)',
                                        color: 'var(--text-primary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '4px',
                                        fontSize: '0.9rem',
                                        transition: 'border-color 0.1s'
                                    }}
                                    onFocus={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                                    onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}
                                />
                            </div>
                        </div>
                    </fieldset>

                    {/* 分析範囲 - Gestalt: 時間範囲をグループ化 */}
                    <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
                        <legend style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                            分析範囲 (オプション)
                        </legend>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>
                                    開始時刻
                                </label>
                                <input
                                    type="text"
                                    value={startTime}
                                    onChange={e => setStartTime(e.target.value)}
                                    placeholder="mm:ss または秒数"
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        background: 'var(--bg-primary)',
                                        color: 'var(--text-primary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '4px',
                                        fontSize: '0.9rem',
                                        transition: 'border-color 0.1s'
                                    }}
                                    onFocus={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                                    onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>
                                    終了時刻
                                </label>
                                <input
                                    type="text"
                                    value={endTime}
                                    onChange={e => setEndTime(e.target.value)}
                                    placeholder="mm:ss または秒数"
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        background: 'var(--bg-primary)',
                                        color: 'var(--text-primary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '4px',
                                        fontSize: '0.9rem',
                                        transition: 'border-color 0.1s'
                                    }}
                                    onFocus={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                                    onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}
                                />
                            </div>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            形式: 00:00 (分:秒) または 0 (秒数)
                        </div>
                    </fieldset>

                    {/* CTA ボタン - OOUI: 「分析を開始」が主語ではなく「ビデオを分析」 */}
                    <button
                        className="btn btn-primary"
                        style={{
                            marginTop: '1rem',
                            justifyContent: 'center',
                            padding: '0.75rem 1.5rem',
                            opacity: loading ? 0.6 : 1,
                            cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                        onClick={handleStart}
                        disabled={loading}
                    >
                        <Play size={18} />
                        {loading ? '分析中...' : 'ビデオを分析'}
                    </button>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                        Ctrl+Enter でも実行可能
                    </div>
                </div>
            </div>
        </Layout>
    );
};

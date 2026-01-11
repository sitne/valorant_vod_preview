import React, { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { getStatus, stopAnalyze, type JobStatus } from '../api';
import { Square, CheckCircle, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Analysis: React.FC = () => {
    const [status, setStatus] = useState<JobStatus | null>(null);
    const [showStop, setShowStop] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const poll = async () => {
            try {
                const s = await getStatus();
                setStatus(s);
                setShowStop(false); // リセット
            } catch (e) {
                console.error(e);
            }
        };

        poll();
        const interval = setInterval(poll, 1000);
        return () => clearInterval(interval);
    }, []);

    // Modeless: 確認なしで停止可能 (インラインで状態表示)
    const handleStop = async () => {
        try {
            await stopAnalyze();
            // 即座フィードバック: UIが即座に反応
            setShowStop(true);
        } catch (e) {
            console.error('Failed to stop:', e);
        }
    };

    if (!status) {
        return (
            <Layout title="分析ダッシュボード">
                <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                    <div style={{ textAlign: 'center', padding: '2rem' }}>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            読み込み中...
                        </div>
                    </div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title="分析ダッシュボード">
            <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                {/* ヘッダー - Spatial Consistency: 常に上部に固定 */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '2rem',
                    paddingBottom: '1.5rem',
                    borderBottom: '1px solid var(--border)'
                }}>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', fontWeight: 600 }}>
                            {status.is_running ? '分析処理中...' : `ステータス: ${status.status}`}
                        </h2>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            ジョブID: {status.id || 'N/A'}
                        </div>
                    </div>

                    {/* 停止ボタン - Modeless: インライン停止、ダイアログなし */}
                    {status.is_running && (
                        <button
                            className="btn"
                            onClick={handleStop}
                            style={{
                                borderColor: 'var(--accent)',
                                color: 'var(--accent)',
                                transition: 'all 0.1s'
                            }}
                            onMouseEnter={e => {
                                e.currentTarget.style.background = 'rgba(255, 70, 85, 0.1)';
                            }}
                            onMouseLeave={e => {
                                e.currentTarget.style.background = 'transparent';
                            }}
                        >
                            <Square size={16} fill="currentColor" /> 停止
                        </button>
                    )}
                </div>

                {/* 停止確認メッセージ - Modeless: インライン状態表示 */}
                {showStop && (
                    <div style={{
                        display: 'flex',
                        gap: '0.75rem',
                        padding: '0.75rem 1rem',
                        background: 'rgba(255, 206, 0, 0.1)',
                        border: '1px solid var(--warning)',
                        borderRadius: '4px',
                        marginBottom: '1.5rem',
                        alignItems: 'center'
                    }}>
                        <AlertCircle size={20} style={{ color: 'var(--warning)', flexShrink: 0 }} />
                        <span style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                            停止要求を送信しました。処理が終了するまでお待ちください。
                        </span>
                    </div>
                )}

                {/* プログレスバー - 即座フィードバック */}
                <div style={{ marginBottom: '2rem' }}>
                    <div style={{
                        background: 'var(--bg-tertiary)',
                        height: '8px',
                        borderRadius: '4px',
                        overflow: 'hidden',
                        marginBottom: '0.75rem'
                    }}>
                        <div style={{
                            width: `${status.progress * 100}%`,
                            background: 'var(--accent)',
                            height: '100%',
                            transition: 'width 0.2s ease', // 即座フィードバック
                            borderRadius: '4px'
                        }} />
                    </div>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: '0.9rem',
                        color: 'var(--text-secondary)'
                    }}>
                        <span>進捗</span>
                        <span>{(status.progress * 100).toFixed(1)}%</span>
                    </div>
                </div>

                {/* ステータスログ - Gestalt: グループ化 */}
                <div style={{
                    marginBottom: '2rem',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border)',
                    padding: '1rem',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                    minHeight: '60px'
                }}>
                    <div style={{
                        color: status.is_running ? 'var(--accent)' : 'var(--success)',
                        transition: 'color 0.1s'
                    }}>
                        <span style={{ opacity: 0.5 }}>{'> '}</span>{status.status}
                    </div>
                </div>

                {/* 完了時アクション */}
                {!status.is_running && status.progress >= 1.0 && (
                    <div style={{
                        padding: '1.5rem',
                        background: 'rgba(0, 255, 159, 0.05)',
                        border: '1px solid var(--success)',
                        borderRadius: '4px',
                        textAlign: 'center'
                    }}>
                        <div style={{
                            color: 'var(--success)',
                            marginBottom: '1rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            fontSize: '1rem',
                            fontWeight: 600
                        }}>
                            <CheckCircle size={20} /> 分析が完了しました
                        </div>
                        <button
                            className="btn btn-primary"
                            onClick={() => navigate('/rounds')}
                            style={{ marginTop: '1rem' }}
                        >
                            結果を表示
                        </button>
                    </div>
                )}

                {/* エラー状態 */}
                {!status.is_running && status.status.includes('error') && (
                    <div style={{
                        padding: '1.5rem',
                        background: 'rgba(255, 70, 85, 0.05)',
                        border: '1px solid var(--accent)',
                        borderRadius: '4px',
                        textAlign: 'center'
                    }}>
                        <div style={{
                            color: 'var(--accent)',
                            marginBottom: '1rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            fontSize: '1rem',
                            fontWeight: 600
                        }}>
                            <AlertCircle size={20} /> エラーが発生しました
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                            {status.status}
                        </div>
                        <button
                            className="btn"
                            onClick={() => navigate('/')}
                            style={{ marginTop: '1rem' }}
                        >
                            ホームに戻る
                        </button>
                    </div>
                )}
            </div>
        </Layout>
    );
};

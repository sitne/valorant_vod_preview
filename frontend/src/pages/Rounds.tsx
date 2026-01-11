import React, { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { getRounds, type SessionRounds } from '../api';
import { Download, Maximize2 } from 'lucide-react';

export const Rounds: React.FC = () => {
    const [sessions, setSessions] = useState<SessionRounds[]>([]);
    const [totalRounds, setTotalRounds] = useState(0);
    const [selectedRound, setSelectedRound] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getRounds().then(res => {
            setSessions(res.sessions);
            setTotalRounds(res.rounds);
            setLoading(false);
        }).catch(() => {
            setLoading(false);
        });
    }, []);

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    };

    // ダウンロードハンドラ - OOUI: オブジェクト(ラウンド)→アクション(ダウンロード)
    const downloadImage = (imageUrl: string, roundNum: number) => {
        const a = document.createElement('a');
        a.href = imageUrl;
        // padStartを使って2桁のゼロ埋めを実現します
        const roundStr = roundNum.toString().padStart(2, '0');
        a.download = `round_${roundStr}.png`;
        a.click();
    };

    if (loading) {
        return (
            <Layout title="ラウンド検出結果">
                <div className="card" style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center', padding: '2rem' }}>
                    <div style={{ color: 'var(--text-secondary)' }}>読み込み中...</div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title="ラウンド検出結果">
            {/* ヘッダー - Spatial Consistency: 常に上部 */}
            <div style={{
                marginBottom: '2rem',
                padding: '1rem',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        合計 <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{totalRounds}</span> ラウンド
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                        {sessions.length} セッション
                    </div>
                </div>
            </div>

            {/* セッションセクション - Gestalt: ラウンドをセッション単位でグループ化 */}
            {sessions.map((session) => (
                <div key={session.session_id} style={{ marginBottom: '3rem' }}>
                    {/* セッションメタデータ */}
                    <div style={{
                        padding: '1rem',
                        background: 'var(--bg-secondary)',
                        borderRadius: '4px',
                        marginBottom: '1.5rem',
                        borderLeft: '4px solid var(--accent)',
                        display: 'grid',
                        gridTemplateColumns: 'auto 1fr auto',
                        gap: '1.5rem',
                        alignItems: 'center'
                    }}>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, fontFamily: 'monospace' }}>
                                {session.session_id.substring(0, 20)}...
                            </h3>
                        </div>
                        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            <div>
                                ラウンド: <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{session.round_count}</span>
                            </div>
                            <div>
                                ステータス: <span style={{
                                    color: session.status === 'completed' ? 'var(--success)' : 'var(--warning)',
                                    fontWeight: 500
                                }}>
                                    {session.status === 'completed' ? '完了' : session.status}
                                </span>
                            </div>
                            <div style={{ color: 'var(--text-secondary)' }}>
                                {formatDate(session.created_at)}
                            </div>
                        </div>
                    </div>

                    {/* ラウンドグリッド - Gestalt: グリッドレイアウト */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                        gap: '1.5rem'
                    }}>
                        {session.rounds.map(r => {
                            const roundKey = `${session.session_id} -${r.round} `;
                            const isSelected = selectedRound === roundKey;
                            return (
                                <div
                                    key={roundKey}
                                    className="card"
                                    style={{
                                        padding: 0,
                                        overflow: 'hidden',
                                        cursor: 'pointer',
                                        transition: 'all 0.1s',
                                        border: isSelected
                                            ? '2px solid var(--accent)'
                                            : '1px solid var(--border)',
                                        transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                                        boxShadow: isSelected
                                            ? '0 0 20px rgba(255, 70, 85, 0.2)'
                                            : 'none'
                                    }}
                                    onClick={() => setSelectedRound(isSelected ? null : roundKey)}
                                >
                                    {/* 画像コンテナ */}
                                    <div style={{
                                        aspectRatio: '1/1',
                                        background: 'var(--bg-primary)',
                                        position: 'relative',
                                        overflow: 'hidden'
                                    }}>
                                        <img
                                            src={r.image_url}
                                            alt={`Round ${r.round} `}
                                            style={{
                                                width: '100%',
                                                height: '100%',
                                                objectFit: 'contain',
                                                transition: 'transform 0.2s'
                                            }}
                                            onMouseEnter={e => {
                                                (e.target as HTMLImageElement).style.transform = 'scale(1.05)';
                                            }}
                                            onMouseLeave={e => {
                                                (e.target as HTMLImageElement).style.transform = 'scale(1)';
                                            }}
                                        />

                                        {/* ラウンド番号バッジ */}
                                        <div style={{
                                            position: 'absolute',
                                            top: '0.5rem',
                                            right: '0.5rem',
                                            background: 'rgba(0, 0, 0, 0.7)',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '4px',
                                            fontSize: '0.8rem',
                                            fontWeight: 600,
                                            color: 'var(--accent)'
                                        }}>
                                            Round {r.round}
                                        </div>

                                        {/* ホバーオーバーレイ - Modeless: アクション表示 */}
                                        <div style={{
                                            position: 'absolute',
                                            bottom: 0,
                                            left: 0,
                                            right: 0,
                                            top: 0,
                                            background: 'linear-gradient(180deg, transparent 50%, rgba(0,0,0,0.8) 100%)',
                                            display: 'flex',
                                            alignItems: 'flex-end',
                                            justifyContent: 'center',
                                            gap: '0.5rem',
                                            padding: '1rem',
                                            opacity: isSelected ? 1 : 0,
                                            transition: 'opacity 0.2s'
                                        }}>
                                            <button
                                                className="btn"
                                                style={{
                                                    padding: '0.5rem',
                                                    fontSize: '0.8rem',
                                                    gap: '0.3rem'
                                                }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    downloadImage(r.image_url, r.round);
                                                }}
                                                title="ダウンロード"
                                            >
                                                <Download size={16} />
                                            </button>
                                            <button
                                                className="btn"
                                                style={{
                                                    padding: '0.5rem',
                                                    fontSize: '0.8rem',
                                                    gap: '0.3rem'
                                                }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    window.open(r.image_url, '_blank');
                                                }}
                                                title="拡大表示"
                                            >
                                                <Maximize2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}

            {/* 空状態 */}
            {sessions.length === 0 && (
                <div style={{
                    textAlign: 'center',
                    padding: '4rem 2rem',
                    color: 'var(--text-secondary)',
                    background: 'var(--bg-secondary)',
                    borderRadius: '4px',
                    border: '1px dashed var(--border)'
                }}>
                    <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                        まだラウンドが検出されていません
                    </div>
                    <div style={{ fontSize: '0.9rem' }}>
                        動画をアップロードして分析を開始してください
                    </div>
                </div>
            )}
        </Layout>
    );
};

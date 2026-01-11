import axios from 'axios';

const api = axios.create({
    baseURL: '/',
});

export interface JobStatus {
    id: string | null;
    is_running: boolean;
    progress: number;
    status: string;
    current_time: number;
}

export interface Round {
    round: number;
    image_url: string;
    timestamp?: number;
    full_image_url?: string;
}

export interface SessionRounds {
    session_id: string;
    created_at: string;
    status: string;
    round_count: number;
    rounds: Round[];
}

export interface RoundsResponse {
    sessions: SessionRounds[];
    total_sessions: number;
    rounds: number;
}

export const getStatus = async () => {
    const res = await api.get<JobStatus>('/api/status');
    return res.data;
};

export const getRounds = async () => {
    const res = await api.get<RoundsResponse>('/api/rounds');
    return res.data;
};

export const startAnalyze = async (params: {
    video_url?: string,
    local_video_path?: string,
    start_time?: number,
    end_time?: number,
    detection_threshold?: number,
    session_id?: string
}) => {
    const res = await api.post('/api/analyze', params);
    return res.data;
};

export const stopAnalyze = async () => {
    const res = await api.post('/api/stop');
    return res.data;
};

export const getSessions = async () => {
    const res = await api.get<RoundsResponse>('/api/rounds');
    return res.data;
};

export const getSession = async (sessionId: string) => {
    const res = await api.get<SessionRounds>(`/api/sessions/${sessionId}`);
    return res.data;
};

export const getSessionRounds = async (sessionId: string) => {
    const res = await api.get<SessionRounds>(`/api/sessions/${sessionId}/rounds`);
    return res.data;
};

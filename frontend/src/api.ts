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

export interface Session {
    session_id: string;
    video_url: string | null;
    created_at: string;
    status: string;
    round_count: number;
    tags: string[];
}

export interface SessionRoundsResponse {
    session_id: string;
    rounds: Round[];
}

export const getStatus = async () => {
    const res = await api.get<JobStatus>('/status');
    return res.data;
};

export const getRounds = async () => {
    const res = await api.get<{ rounds: Round[] }>('/rounds');
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
    const res = await api.post('/analyze', params);
    return res.data;
};

export const stopAnalyze = async () => {
    const res = await api.post('/stop');
    return res.data;
};

export const getSessions = async (): Promise<Session[]> => {
    const res = await api.get<Session[]>('/sessions');
    return res.data;
};

export const getSession = async (sessionId: string): Promise<Session> => {
    const res = await api.get<Session>(`/sessions/${sessionId}`);
    return res.data;
};

export const getSessionRounds = async (sessionId: string): Promise<SessionRoundsResponse> => {
    const res = await api.get<SessionRoundsResponse>(`/sessions/${sessionId}/rounds`);
    return res.data;
};

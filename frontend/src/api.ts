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
    timestamp: number;
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
    detection_threshold?: number
}) => {
    const res = await api.post('/analyze', params);
    return res.data;
};

export const stopAnalyze = async () => {
    const res = await api.post('/stop');
    return res.data;
};

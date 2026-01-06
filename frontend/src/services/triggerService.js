import apiClient from './apiClient';

export default {
    getTriggers: async () => {
        const response = await apiClient.get('/api/v1/triggers');
        return response.data;
    },
    addTrigger: async (trigger) => {
        const response = await apiClient.post('/api/v1/triggers', trigger);
        return response.data;
    }
};

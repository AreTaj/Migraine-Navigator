import apiClient from './apiClient';

export default {
    getMedications: async () => {
        const response = await apiClient.get('/api/v1/medications');
        return response.data;
    },
    addMedication: async (medication) => {
        const response = await apiClient.post('/api/v1/medications', medication);
        return response.data;
    }
};

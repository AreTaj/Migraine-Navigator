import apiClient from './apiClient';
import { getCurrentLocation, getCityName } from '../utils/geolocation';

export default {
    createEntry: async (entryData) => {
        const response = await apiClient.post('/api/v1/entries', entryData);
        return response.data;
    },
    updateEntry: async (id, entryData) => {
        const response = await apiClient.put(`/api/v1/entries/${id}`, entryData);
        return response.data;
    },
    getLocation: async () => {
        const { latitude, longitude } = await getCurrentLocation();
        let locationName = await getCityName(latitude, longitude);
        return {
            latitude,
            longitude,
            locationName: locationName || `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`
        };
    }
};

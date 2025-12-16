import axios from 'axios';

// Get Current Location (Lat/Lon + City) via IP
export const getCurrentLocation = async () => {
    try {
        const response = await axios.get('/api/v1/location');
        const { latitude, longitude } = response.data;
        return { latitude, longitude };
    } catch (error) {
        throw new Error("Could not detect location via IP.");
    }
};

// Get human readable city name (Reverse Geocoding)
// Note: The IP API already returns the city address, so we can modify this to fetch it from the same endpoint 
// or simpler: let the frontend reuse the logic.
// However, to keep compatibility with existing calls, we can make this fetch the full address again or just reuse the logic.
// Efficient way: getCurrentLocation() now returns data that we can cache, but standard 'getCityName(lat, lon)' implies a fresh lookup.
// For IP-based, Lat/Lon is tied to City. 

export const getCityName = async (lat, lon) => {
    // If we are using IP, the previous call likely already got the address.
    // simpler approach: Call the same API, as it returns full details.
    try {
        const response = await axios.get('/api/v1/location');
        return response.data.address;
    } catch (error) {
        console.error("City fetch error:", error);
        return null;
    }
};

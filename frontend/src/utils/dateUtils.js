/**
 * Formats a Date object as a YYYY-MM-DD string using the local timezone.
 * This prevents the "tomorrow" bug caused by using toISOString() in negative UTC offsets.
 *
 * @param {Date} date - Optional Date object. Defaults to now.
 * @returns {string} - "YYYY-MM-DD"
 */
export const formatDateLocal = (date = new Date()) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

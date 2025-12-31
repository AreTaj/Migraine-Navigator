import { Activity, Thermometer, Droplets, CloudRain, CloudSun, ShieldCheck } from 'lucide-react';

const AllCaughtUpCard = ({ weather, todayEntry, tempUnit }) => {
    // Determine Health Status
    const isRecovering = todayEntry && todayEntry['Pain Level'] > 0;

    // Determine Weather Condition
    const isRainy = weather && weather.prcp > 0.1;
    const isHumid = weather && weather.humidity > 70;

    // Select Icon
    const StatusIcon = isRecovering ? ShieldCheck : (isRainy ? CloudRain : CloudSun);
    const iconColor = isRecovering ? '#4ade80' : (isRainy ? '#60a5fa' : '#fcd34d');

    // Temperature Formatting
    const formatTemp = (celsius) => {
        if (celsius === undefined) return '--';
        if (tempUnit === 'F') {
            const fahrenheit = (celsius * 9) / 5 + 32;
            return `${fahrenheit.toFixed(1)}°F`;
        }
        return `${celsius.toFixed(1)}°C`;
    };

    return (
        <div style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            background: 'rgba(30, 41, 59, 0.4)',
            borderRadius: '12px',
            border: '1px solid #334155',
            padding: '16px',
            animation: 'fadeIn 0.5s ease-in-out',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Subtle Pulse Background for active monitoring */}
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '100px',
                height: '100px',
                background: `${iconColor}10`,
                filter: 'blur(40px)',
                borderRadius: '50%',
                zIndex: 0
            }} />

            <div style={{ zIndex: 1, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px', width: '100%' }}>
                {/* Weather Metrics */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#e2e8f0' }}>
                        <StatusIcon size={24} color={iconColor} />
                        <span style={{ fontSize: '1.4rem', fontWeight: '600' }}>
                            {formatTemp(weather?.temp)}
                        </span>
                    </div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {isRainy ? 'Precipitation' : 'Current Temp'}
                    </p>
                </div>

                {/* Secondary Metrics */}
                <div style={{ width: '1px', height: '30px', background: '#334155', alignSelf: 'center' }} />

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#e2e8f0' }}>
                        <Droplets size={20} color="#94a3b8" />
                        <span style={{ fontSize: '1.1rem', fontWeight: '500' }}>
                            {weather?.humidity !== undefined ? `${weather.humidity}%` : '--'}
                        </span>
                    </div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Humidity
                    </p>
                </div>
            </div>

            {isRecovering && (
                <div style={{
                    zIndex: 1,
                    marginTop: '8px',
                    padding: '6px 12px',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    <Activity size={14} color={iconColor} />
                    <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: '500' }}>
                        Status: Recovery Active
                    </span>
                </div>
            )}

            {isRecovering && (
                <p style={{ margin: 0, fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic' }}>
                    Acknowledge migraine logged this morning.
                </p>
            )}
        </div>
    );
};

export default AllCaughtUpCard;

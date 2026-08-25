import React, { useEffect, useState } from 'react';
import { subscribeWaking } from '../api.js';

export default function WakingBanner() {
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    const unsub = subscribeWaking(setWaking);
    return unsub;
  }, []);

  if (!waking) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '16px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98))',
        color: '#f8fafc',
        padding: '10px 20px',
        borderRadius: '9999px',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 0 15px rgba(56, 189, 248, 0.3)',
        border: '1px solid rgba(56, 189, 248, 0.4)',
        fontSize: '13.5px',
        fontWeight: '500',
        backdropFilter: 'blur(8px)',
        animation: 'fadeInSlide 0.3s ease-out',
      }}
      role="status"
      aria-live="polite"
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: '#38bdf8',
          boxShadow: '0 0 8px #38bdf8',
          display: 'inline-block',
          animation: 'pulseDot 1.5s infinite ease-in-out',
        }}
      />
      <span>
        <strong>Initializing AI services...</strong> Please wait a few moments.
      </span>
      <style>{`
        @keyframes pulseDot {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.4); opacity: 1; }
        }
        @keyframes fadeInSlide {
          from { opacity: 0; transform: translate(-50%, -10px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
      `}</style>
    </div>
  );
}

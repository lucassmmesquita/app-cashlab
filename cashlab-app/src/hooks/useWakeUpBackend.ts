/**
 * CashLab — Hook para "acordar" o backend no Render (plano Free)
 *
 * Faz um GET /health assim que o app abre, para que o servidor
 * já esteja pronto quando as telas fizerem as requisições reais.
 */
import { useEffect, useState } from 'react';
import { API_HOST } from '@/utils/constants';

type WakeStatus = 'sleeping' | 'waking' | 'awake' | 'error';

export function useWakeUpBackend() {
  const [status, setStatus] = useState<WakeStatus>('sleeping');

  useEffect(() => {
    let cancelled = false;

    const wake = async () => {
      setStatus('waking');
      try {
        const res = await fetch(`${API_HOST}/health`, { method: 'GET' });
        if (!cancelled) {
          setStatus(res.ok ? 'awake' : 'error');
        }
      } catch {
        if (!cancelled) setStatus('error');
        // Retry once after 3s
        setTimeout(async () => {
          try {
            await fetch(`${API_HOST}/health`);
            if (!cancelled) setStatus('awake');
          } catch {
            if (!cancelled) setStatus('error');
          }
        }, 3000);
      }
    };

    wake();
    return () => { cancelled = true; };
  }, []);

  return { status, isReady: status === 'awake' };
}

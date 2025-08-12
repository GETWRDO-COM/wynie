import React, { useEffect, useState } from 'react';

const BackendStatus = () => {
  const [ok, setOk] = useState(null);
  const [url, setUrl] = useState(process.env.REACT_APP_BACKEND_URL || '');

  useEffect(() => {
    const ping = async () => {
      try {
        const resp = await fetch(`${url}/api/market-score`);
        setOk(resp.ok);
      } catch {
        setOk(false);
      }
    };
    if (url) ping();
  }, [url]);

  return (
    <div className="text-xs text-gray-400">
      Backend: <span className="text-white/80">{url || 'not set'}</span> {ok===null? '' : ok ? <span className="text-green-400">• OK</span> : <span className="text-red-400">• Unreachable</span>}
    </div>
  );
};

export default BackendStatus;
import React from 'react';
import { Database, Cloud, Server, CheckCircle2 } from 'lucide-react';

export default function StatusBanner({ health }) {
  return (
    <div className="service-info-bar">
      <div className="service-chip">
        <Server size={14} color="#4f46e5" />
        <span>Compute: <strong>AWS EC2 Ready</strong></span>
        <span className="dot"></span>
      </div>

      <div className="service-chip">
        <Cloud size={14} color="#0284c7" />
        <span>Storage: <strong>{health?.storage || 'AWS S3 (or Local Fallback)'}</strong></span>
        <span className="dot"></span>
      </div>

      <div className="service-chip">
        <Database size={14} color="#059669" />
        <span>Database: <strong>{health?.database || 'PostgreSQL (Docker)'}</strong></span>
        <span className="dot"></span>
      </div>
    </div>
  );
}

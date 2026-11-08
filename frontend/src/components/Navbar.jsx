import React from 'react';
import { Cloud, Shield, ShieldCheck, LogOut, LogIn, HardDrive } from 'lucide-react';

export default function Navbar({ isAdmin, adminUser, onOpenLogin, onLogout }) {
  return (
    <nav className="navbar">
      <div className="container nav-container">
        <div className="logo">
          <Cloud className="w-7 h-7 text-indigo-600" />
          <span>CloudLens</span>
          <span className="logo-badge">AWS S3 & EC2</span>
        </div>

        <div className="nav-actions">
          {isAdmin ? (
            <>
              <div className="status-badge admin">
                <ShieldCheck size={16} />
                <span>Admin ({adminUser?.username || 'admin'})</span>
              </div>
              <button onClick={onLogout} className="btn-outline" title="Log out from admin mode">
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <div className="status-badge user">
                <Shield size={14} />
                <span>User Mode (Upload & View)</span>
              </div>
              <button onClick={onOpenLogin} className="btn-primary" title="Login as Admin to Delete images">
                <LogIn size={16} />
                <span>Admin Login</span>
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

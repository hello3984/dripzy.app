import React, { useState } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Logo from './logo.svg';

// Import components
import Navbar from './components/Navbar';
import HomePage from './components/HomePage';
import ProductsPage from './components/ProductsPage';
import TryOnPage from './components/TryOnPage';
import UserAuth from './components/UserAuth';
import VirtualTryOn from './components/VirtualTryOn';
import ThemeCollage from './components/ThemeCollage';

function App() {
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const handleLogin = (userData) => {
    setUser(userData);
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <Router>
      <div className="App">
        <Navbar 
          user={user} 
          onLogin={() => setShowAuthModal(true)} 
          onLogout={handleLogout} 
        />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/tryon" element={<TryOnPage />} />
            <Route path="/virtual-try-on" element={<VirtualTryOn onComplete={() => {}} />} />
            <Route path="/theme-collage" element={<ThemeCollage />} />
          </Routes>
        </main>
        
        <footer className="app-footer">
          <div className="container">
            <div className="footer-content">
              <div className="footer-section">
                <h3 className="footer-logo">
                  <img src={Logo} alt="Dripzy" />
                  dripzy
                </h3>
                <p>AI-powered fashion styling tailored just for you</p>
              </div>
              
              <div className="footer-section">
                <h3>Links</h3>
                <ul className="footer-links">
                  <li><a href="/">Features</a></li>
                  <li><a href="#how">How It Works</a></li>
                </ul>
              </div>
              
              <div className="footer-section">
                <h3>Legal</h3>
                <ul className="footer-links">
                  <li><a href="/privacy">Privacy Policy</a></li>
                  <li><a href="/terms">Terms of Service</a></li>
                </ul>
              </div>
              
              <div className="footer-section">
                <h3>Connect</h3>
                <div className="social-links">
                  <a href="https://instagram.com/dripzy.app" target="_blank" rel="noopener noreferrer" className="social-link">Instagram</a>
                  <a href="https://tiktok.com/@dripzyapp" target="_blank" rel="noopener noreferrer" className="social-link">TikTok</a>
                  <a href="mailto:hello@dripzy.app" className="social-link">Contact</a>
                </div>
              </div>
            </div>
            
            <div className="footer-bottom">
              <p>&copy; 2023 Dripzy. All rights reserved.</p>
              <div className="affiliate-disclosure">
                <p>Dripzy participates in affiliate programs and may earn commissions from qualifying purchases.</p>
              </div>
            </div>
          </div>
        </footer>
        
        {showAuthModal && (
          <div className="modal-overlay">
            <UserAuth onLogin={handleLogin} onClose={() => setShowAuthModal(false)} />
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;

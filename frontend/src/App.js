import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Import components
import Navbar from './components/Navbar';
import HomePage from './components/HomePage';
import ProductsPage from './components/ProductsPage';
import TryOnPage from './components/TryOnPage';
import UserAuth from './components/UserAuth';

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
          </Routes>
        </main>
        
        <footer className="app-footer">
          <div className="container">
            <div className="footer-content">
              <div className="footer-section">
                <h3>AI Fashion Assistant</h3>
                <p>Discover your perfect style with the help of AI</p>
              </div>
              
              <div className="footer-section">
                <h3>Quick Links</h3>
                <ul>
                  <li><a href="/">Home</a></li>
                  <li><a href="/products">Shop</a></li>
                  <li><a href="/tryon">Virtual Try-On</a></li>
                </ul>
              </div>
              
              <div className="footer-section">
                <h3>Connect With Us</h3>
                <div className="social-links">
                  <a href="/#" className="social-link">Facebook</a>
                  <a href="/#" className="social-link">Twitter</a>
                  <a href="/#" className="social-link">Instagram</a>
                </div>
              </div>
            </div>
            
            <div className="footer-bottom">
              <p>&copy; 2023 AI Fashion Assistant. All rights reserved.</p>
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

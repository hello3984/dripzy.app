import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './Header';
import Showcase from './Showcase';

// Placeholder components for other routes
const Features = () => <div className="main-container"><h1>Features</h1></div>;
const Pricing = () => <div className="main-container"><h1>Pricing</h1></div>;
const HowToUse = () => <div className="main-container"><h1>How To Use</h1></div>;
const About = () => <div className="main-container"><h1>About</h1></div>;
const SignIn = () => <div className="main-container"><h1>Sign In</h1></div>;
const SignUp = () => <div className="main-container"><h1>Sign Up</h1></div>;

const App = () => {
  return (
    <Router>
      <div className="app">
        <Header />
        <Routes>
          <Route path="/" element={<Showcase />} />
          <Route path="/features" element={<Features />} />
          <Route path="/showcase" element={<Showcase />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/how-to-use" element={<HowToUse />} />
          <Route path="/about" element={<About />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App; 
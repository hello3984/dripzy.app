import React, { useState } from 'react';
import { motion } from 'framer-motion';
import OutfitCollage from './OutfitCollage';
import LoadingIndicator from './LoadingIndicator';

const ThemeCollage = () => {
  const [prompt, setPrompt] = useState('');
  const [gender, setGender] = useState('female');
  const [budget, setBudget] = useState(400);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [outfit, setOutfit] = useState(null);
  const [generatedPrompt, setGeneratedPrompt] = useState('');

  // Preset theme suggestions
  const themeSuggestions = [
    'Coachella Dreams ✨',
    'Summer Picnic 🌿',
    'Beach Vacation 🏖️',
    'Date Night 💋',
    'Office Chic 💼',
    'Festival Vibes 🎵',
    'Vintage Inspired 🕰️',
    'Winter Wonderland ❄️',
    'Minimalist Urban 🏙️',
    'Boho Wedding 💍'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!prompt.trim()) {
      setError('Please enter a theme or prompt');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOutfit(null);
    setGeneratedPrompt(prompt);

    try {
      const response = await fetch('http://localhost:8004/outfits/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          gender,
          budget,
          include_alternatives: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      
      if (data && data.outfits && data.outfits.length > 0) {
        setOutfit(data.outfits[0]);
      } else {
        setError('No outfits found. Please try a different prompt.');
      }
    } catch (err) {
      setError(`Failed to generate outfit: ${err.message}`);
      console.error('Error generating outfit:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const selectThemeSuggestion = (suggestion) => {
    setPrompt(suggestion);
  };

  return (
    <div className="theme-collage-page">
      <main>
        <motion.div 
          className="header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Theme Outfit Generator</h1>
          <p>Enter a theme or style to generate a personalized outfit collage</p>
        </motion.div>

        <div className="suggestion-chips">
          {themeSuggestions.map((suggestion, index) => (
            <motion.button
              key={index}
              className="suggestion-chip"
              onClick={() => selectThemeSuggestion(suggestion)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + (index * 0.05), duration: 0.3 }}
            >
              {suggestion}
            </motion.button>
          ))}
        </div>

        <motion.form 
          onSubmit={handleSubmit}
          className="generate-form"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="input-group">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter a theme (e.g., 'Coachella Dreams ✨')"
              className="prompt-input"
            />
          </div>

          <div className="form-row">
            <div className="input-group">
              <label htmlFor="gender">Gender</label>
              <select 
                id="gender" 
                value={gender}
                onChange={(e) => setGender(e.target.value)}
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="unisex">Unisex</option>
              </select>
            </div>

            <div className="input-group">
              <label htmlFor="budget">Budget ($)</label>
              <select 
                id="budget" 
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
              >
                <option value="200">$200</option>
                <option value="400">$400</option>
                <option value="800">$800</option>
                <option value="1500">$1500+</option>
              </select>
            </div>
          </div>

          <button 
            type="submit"
            className="generate-button"
            disabled={isLoading}
          >
            {isLoading ? 'Generating...' : 'Generate Outfit Collage'}
          </button>
        </motion.form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="loading-container">
            <LoadingIndicator />
            <p>Creating your themed outfit collage...</p>
          </div>
        )}

        {outfit && (
          <motion.div
            className="result-container"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <OutfitCollage outfit={outfit} prompt={generatedPrompt} />
          </motion.div>
        )}
      </main>

      <style jsx>{`
        .theme-collage-page {
          min-height: 100vh;
          padding: 2rem;
          background-color: #f9f9f9;
          font-family: 'Poppins', sans-serif;
        }

        .header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .header h1 {
          font-family: 'Playfair Display', serif;
          font-size: 2.5rem;
          margin-bottom: 0.5rem;
          color: #333;
        }

        .header p {
          color: #666;
          font-size: 1.1rem;
        }

        .suggestion-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          justify-content: center;
          margin-bottom: 2rem;
        }

        .suggestion-chip {
          background-color: white;
          border: 1px solid #e3e3e3;
          border-radius: 30px;
          padding: 0.5rem 1rem;
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .suggestion-chip:hover {
          background-color: #f5f5f5;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07);
        }

        .generate-form {
          max-width: 600px;
          margin: 0 auto 2rem;
          padding: 2rem;
          background-color: white;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }

        .input-group {
          margin-bottom: 1.5rem;
        }

        .form-row {
          display: flex;
          gap: 1rem;
        }

        .form-row .input-group {
          flex: 1;
        }

        label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
          color: #555;
        }

        .prompt-input {
          width: 100%;
          padding: 0.8rem 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.2s;
        }

        .prompt-input:focus {
          border-color: #a884ff;
          outline: none;
          box-shadow: 0 0 0 3px rgba(168, 132, 255, 0.15);
        }

        select {
          width: 100%;
          padding: 0.8rem 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          background-color: white;
          cursor: pointer;
        }

        .generate-button {
          width: 100%;
          background-color: #6c4ed9;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 1rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s, transform 0.1s;
        }

        .generate-button:hover {
          background-color: #5b3ec7;
        }

        .generate-button:active {
          transform: translateY(1px);
        }

        .generate-button:disabled {
          background-color: #b0a8d1;
          cursor: not-allowed;
        }

        .error-message {
          background-color: #fff2f2;
          border-left: 4px solid #ff5252;
          color: #d32f2f;
          padding: 1rem;
          margin-bottom: 2rem;
          border-radius: 4px;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          margin: 3rem 0;
        }

        .loading-container p {
          margin-top: 1rem;
          color: #666;
        }

        .result-container {
          margin: 2rem 0;
        }

        @media (max-width: 768px) {
          .form-row {
            flex-direction: column;
            gap: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default ThemeCollage; 
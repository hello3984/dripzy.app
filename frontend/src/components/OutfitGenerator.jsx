import React, { useState } from 'react';
import './OutfitGenerator.css';

const OutfitGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [generatedOutfit, setGeneratedOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [gender, setGender] = useState('female'); // Default to female
  const [budget, setBudget] = useState(200); // Default budget as a number

  // Define API base URL based on environment
  const API_BASE_URL = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:5000' // Local development backend
    : 'https://dripzy-app.onrender.com'; // Production backend

  const handlePromptChange = (e) => {
    setPrompt(e.target.value);
  };

  const handleGenderChange = (e) => {
    setGender(e.target.value);
  };

  const handleBudgetChange = (e) => {
    // Ensure budget is a number
    const budgetValue = parseInt(e.target.value, 10);
    setBudget(budgetValue);
  };

  const generateOutfit = async () => {
    if (!prompt.trim()) {
      setError('Please enter a style description');
      return;
    }

    setLoading(true);
    setError(null);
    
    console.log("Sending request to backend with prompt:", prompt);
    console.log("Using API endpoint:", `${API_BASE_URL}/outfits/generate`);
    console.log("Request params:", { prompt, gender, budget });

    try {
      const response = await fetch(`${API_BASE_URL}/outfits/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          prompt, 
          gender, 
          budget 
        }),
        mode: 'cors',
      });

      console.log("Response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("API error:", errorText);
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      // Added detailed logging for debugging
      console.log("API response data:", JSON.stringify(data, null, 2));
      console.log("First outfit:", data.outfits && data.outfits[0] ? JSON.stringify(data.outfits[0], null, 2) : "No outfits returned");
      
      if (!data.outfits || !data.outfits.length) {
        throw new Error("No outfits returned from API");
      }
      
      setGeneratedOutfit(data.outfits[0]); // Use the first outfit from the array
    } catch (err) {
      console.error('Failed to generate outfit:', err);
      setError(`Failed to generate outfit: ${err.message}`);
      // Remove the mock data generation to ensure we only show real data
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalPrice = (items) => {
    return items.reduce((total, item) => total + (item.price || 0), 0).toFixed(2);
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      generateOutfit();
    }
  };

  return (
    <div className="outfit-generator">
      <div className="update-banner">
        🔥 NEW DESIGN DEPLOYED - APRIL 2024 🔥
        {process.env.NODE_ENV === 'development' && <span> (DEVELOPMENT MODE)</span>}
      </div>
      <div className="generator-container">
        <h2>AI Fashion Stylist</h2>
        <p className="description">
          Describe your style goal or occasion and our AI will create a personalized outfit for you.
        </p>
        
        <div className="prompt-input">
          <input
            type="text"
            value={prompt}
            onChange={handlePromptChange}
            onKeyPress={handleKeyPress}
            placeholder="e.g., Coachella outfit, business casual, date night"
            className="prompt-field"
          />
          
          <div className="filters">
            <select 
              value={gender} 
              onChange={handleGenderChange}
              className="filter-select"
            >
              <option value="female">Women's</option>
              <option value="male">Men's</option>
              <option value="unisex">Unisex</option>
            </select>
            
            <select 
              value={budget} 
              onChange={handleBudgetChange}
              className="filter-select"
            >
              <option value="100">Budget ($100)</option>
              <option value="200">Medium ($200)</option>
              <option value="500">Premium ($500)</option>
              <option value="1000">Luxury ($1000+)</option>
            </select>
          </div>
          
          <button 
            onClick={generateOutfit} 
            disabled={loading}
            className="generate-button"
          >
            {loading ? 'Generating...' : 'Generate Outfit'}
          </button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        {generatedOutfit && (
          <div className="outfit-results">
            <h3>Your {prompt} Outfit</h3>
            
            <div className="total-price">
              Total Price: ${generatedOutfit.total_price ? generatedOutfit.total_price.toFixed(2) : calculateTotalPrice(generatedOutfit.items)}
            </div>
            
            <div className="outfit-items">
              {generatedOutfit.items.map((item, index) => (
                <div key={index} className="outfit-item">
                  <div className="item-image">
                    {item.image_url ? (
                      <img src={item.image_url} alt={item.product_name || item.type} />
                    ) : (
                      <div className="placeholder-image">
                        {item.category} Image
                      </div>
                    )}
                  </div>
                  <div className="item-details">
                    <h4>{item.product_name || item.type}</h4>
                    <p className="brand">{item.brand}</p>
                    <p className="category">{item.category}</p>
                    {item.price && <p className="price">${item.price.toFixed(2)}</p>}
                    {(item.url || item.product_url) && (
                      <a 
                        href={item.url || item.product_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="shop-link"
                      >
                        Shop Now
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutfitGenerator; 
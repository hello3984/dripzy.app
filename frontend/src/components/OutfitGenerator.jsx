import React, { useState, useEffect } from 'react';
import './OutfitGenerator.css';
import MoodChart from './ui/MoodChart';
import LoadingIndicator from './ui/LoadingIndicator';
import analytics, { trackOutfitGeneration, trackThemeSelection, trackProductClick, trackPageView, trackError, trackPerformance } from '../services/analytics';

const OutfitGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [generatedOutfit, setGeneratedOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [gender, setGender] = useState('female'); // Default to female
  const [budget, setBudget] = useState(200); // Default budget as a number
  const [selectedMood, setSelectedMood] = useState(null);

  // Analytics tracking on component mount
  useEffect(() => {
    trackPageView('Outfit Generator');
    analytics.setSessionProperties({
      page: 'outfit_generator',
      timestamp: new Date().toISOString()
    });
  }, []);

  // Define API base URL based on environment
  const API_BASE_URL = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8000' // Local development backend (updated to correct running port)
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

  const handleMoodSelect = (moodId) => {
    setSelectedMood(moodId);
    
    // Analytics: Track mood/theme selection
    trackThemeSelection(moodId);
    analytics.trackStylePreference({
      type: 'mood',
      value: moodId,
      gender: gender,
      budgetRange: budget
    });
    
    // Update prompt based on selected mood
    const moodMap = {
      'boho': 'bohemian free-spirited outfit with natural elements',
      'minimalist': 'clean minimal outfit with simple lines and monochromatic palette',
      'glam': 'glamorous bold statement outfit with luxurious elements',
      'preppy': 'preppy classic outfit with structured silhouettes',
      'streetwear': 'urban streetwear outfit with contemporary elements',
      'vintage': 'vintage-inspired outfit with timeless pieces',
      'romantic': 'soft romantic outfit with feminine details and flowing fabrics',
      'edgy': 'edgy bold outfit with unconventional details',
      'athleisure': 'athletic-inspired comfortable yet stylish outfit',
      'festival': 'vibrant festival outfit with eclectic elements'
    };
    
    setPrompt(moodMap[moodId] || '');
  };

  const generateOutfit = async () => {
    if (!prompt.trim()) {
      setError('Please enter a style description or select a mood');
      return;
    }

    setLoading(true);
    setError(null);
    
    const startTime = Date.now();
    
    // Analytics: Track outfit generation start
    analytics.trackOutfitGenerationStart(prompt);
    
    // Using Enhanced API endpoint with smart retailer selection

    try {
      // ENHANCED: Use ultra-fast endpoint with smart Farfetch/Nordstrom routing
      const response = await fetch(`${API_BASE_URL}/outfits/ultra-fast-generate`, {
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

      if (!response.ok) {
        // POST request failed, trying fallback to GET test endpoint
        // If POST request fails, try the test endpoint as fallback
        const testResponse = await fetch(`${API_BASE_URL}/outfits/generate-test`);
        
        if (!testResponse.ok) {
          const errorText = await response.text();
          // API error occurred
          throw new Error(`Error ${response.status}: ${errorText}`);
        }
        
        const data = await testResponse.json();
        // API test response received
        
        if (!data.outfits || !data.outfits.length) {
          throw new Error("No outfits returned from API");
        }
        
        setGeneratedOutfit(data.outfits[0]); // Use the first outfit from the array
        return;
      }

      const data = await response.json();
      const responseTime = Date.now() - startTime;
      
      // Analytics: Track API response performance
      analytics.trackApiResponse('/outfits/ultra-fast-generate', responseTime, true);
      trackPerformance('outfit_generation_time', responseTime, prompt);
      
      if (!data.outfits || !data.outfits.length) {
        throw new Error("No outfits returned from API");
      }
      
      const outfit = data.outfits[0];
      setGeneratedOutfit(outfit);
      
      // Analytics: Track successful outfit generation
      trackOutfitGeneration({
        prompt: prompt,
        gender: gender,
        budget: budget,
        style: outfit.style,
        occasion: outfit.occasion,
        responseTime: responseTime,
        itemsCount: outfit.items.length,
        totalPrice: outfit.total_price,
        success: true
      });
      
      analytics.trackOutfitGenerationComplete({
        prompt: prompt,
        success: true,
        responseTime: responseTime,
        itemsCount: outfit.items.length,
        totalPrice: outfit.total_price
      });
    } catch (err) {
      // Failed to generate outfit
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
    <div className={`outfit-generator ${selectedMood ? `mood-selected-${selectedMood}` : ''}`}>
      <div className="update-banner">
        🔥 NEW DESIGN DEPLOYED - APRIL 2024 🔥
        {process.env.NODE_ENV === 'development' && <span> (DEVELOPMENT MODE)</span>}
      </div>
      <div className="generator-container">
        <h2>AI Fashion Stylist</h2>
        <p className="description">
          Describe your style goal or occasion and our AI will create a personalized outfit for you.
        </p>
        
        <MoodChart onSelectMood={handleMoodSelect} selectedMood={selectedMood} />
        
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
        
        {loading && <LoadingIndicator message="Curating your fashion recommendations..." />}
        
        {!loading && generatedOutfit && (
          <div className="outfit-results">
            <h3>Your {prompt} Outfit</h3>
            
            <div className="total-price">
              Total Price: ${generatedOutfit.total_price ? generatedOutfit.total_price.toFixed(2) : calculateTotalPrice(generatedOutfit.items)}
            </div>
            
            <div className="outfit-items">
              {generatedOutfit.items.map((item, index) => (
                <div key={index} className="outfit-item">
                  <div className="item-image">
                    {/* ENHANCED: Show all legitimate images including SerpAPI */}
                    {item.image_url && item.image_url.trim() && 
                     item.image_url.startsWith('http') && 
                     !item.image_url.includes('via.placeholder') ? (
                      <img 
                        src={item.image_url} 
                        alt={item.product_name || item.type} 
                        onError={(e) => {
                          // IMPROVED: Better error handling with fallback
                          console.log(`Failed to load image: ${item.image_url}`);
                          e.target.src = `https://via.placeholder.com/300x400/f8f9fa/333333?text=${encodeURIComponent(item.product_name?.substring(0, 20) || 'Fashion Item')}`;
                          e.target.style.opacity = '0.7';
                          e.target.style.border = '2px dashed #ddd';
                        }}
                        onLoad={(e) => {
                          // Image loaded successfully
                          e.target.style.opacity = '1';
                          e.target.style.border = 'none';
                        }}
                        style={{ 
                          opacity: '0.8', 
                          transition: 'opacity 0.3s ease',
                          maxWidth: '100%',
                          height: 'auto',
                          objectFit: 'cover'
                        }}
                      />
                    ) : (
                      <div className="missing-image-note">
                        <div className="placeholder-icon" style={{fontSize: '2rem', marginBottom: '8px'}}>👗</div>
                        <span>{item.product_name ? `${item.product_name.substring(0, 30)}...` : item.category || 'Fashion Item'}</span>
                        <div style={{fontSize: '0.8rem', color: '#888', marginTop: '4px'}}>
                          {item.brand && `by ${item.brand}`}
                        </div>
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
import React from 'react';
import stylistService from '../services/stylist';

const TrendingStylesDisplay = ({ onStyleSelect }) => {
  const { trendingStyles } = stylistService;

  // Get top 3 colors based on popularity
  const topColors = trendingStyles.colors
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, 3);

  // Get top 3 patterns based on popularity
  const topPatterns = trendingStyles.patterns
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, 3);

  // Get top fabrics based on popularity
  const topFabrics = trendingStyles.fabrics
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, 2);

  // Handle style click
  const handleStyleClick = (styleName) => {
    if (onStyleSelect && typeof onStyleSelect === 'function') {
      onStyleSelect(styleName);
    }
  };

  return (
    <div className="trending-styles-display">
      <div className="trend-section">
        <h3>Top Trending Colors</h3>
        <div className="color-chips">
          {topColors.map((color) => (
            <div 
              key={color.name} 
              className="color-chip"
              onClick={() => handleStyleClick(color.name)}
            >
              <div 
                className="color-sample" 
                style={{ backgroundColor: color.hex }}
              ></div>
              <div className="color-details">
                <span className="color-name">{color.name}</span>
                <span className="trend-score">{Math.round(color.popularity * 100)}% trending</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="trend-section">
        <h3>Hot Patterns & Prints</h3>
        <div className="trend-tags">
          {topPatterns.map((pattern) => (
            <button
              key={pattern.name}
              className="trend-tag"
              onClick={() => handleStyleClick(pattern.name)}
            >
              {pattern.name}
              <span className="trend-percentage">{Math.round(pattern.popularity * 100)}%</span>
            </button>
          ))}
        </div>
      </div>

      <div className="trend-section">
        <h3>Sustainable Materials</h3>
        <div className="trend-cards">
          {topFabrics.map((fabric) => (
            <div 
              key={fabric.name} 
              className="trend-card"
              onClick={() => handleStyleClick(fabric.name)}
            >
              <h4>{fabric.name}</h4>
              <div className="trend-meter">
                <div 
                  className="trend-meter-fill" 
                  style={{ width: `${fabric.popularity * 100}%` }}
                ></div>
              </div>
              <p className="trend-description">
                Trending in sustainable fashion
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="trend-inspiration">
        <h3>Stylist Tips</h3>
        <div className="stylist-tip">
          <p>"Mix trending colors with classic neutrals for a balanced look."</p>
          <span className="stylist-name">— AI Fashion Stylist</span>
        </div>
      </div>
    </div>
  );
};

export default TrendingStylesDisplay; 
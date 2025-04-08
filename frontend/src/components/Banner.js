import React from 'react';

const Banner = () => {
  return (
    <div className="home-banner">
      <div className="banner-content">
        <h1>Discover Your Perfect Style</h1>
        <p>
          AI-powered outfit recommendations tailored to your preferences, 
          budget, and occasions. Try on your looks virtually before you buy!
        </p>
      </div>
      <div className="banner-image">
        {/* In a real app, we would use an actual image here */}
        <div className="image-placeholder">
          <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <path fill="#FF5858" d="M32.9,-54.1C43.7,-49.2,54.4,-41.9,63,-30.9C71.5,-19.8,77.9,-5.1,76.3,8.8C74.7,22.6,65.2,35.6,54.2,44.5C43.3,53.4,30.9,58.3,17.3,64.8C3.6,71.3,-11.3,79.4,-24.8,77.3C-38.3,75.2,-50.3,62.8,-59.3,48.5C-68.3,34.1,-74.3,17.6,-73.1,1.9C-71.9,-13.8,-63.5,-27.5,-53.5,-37.9C-43.5,-48.3,-31.8,-55.4,-20.3,-60C-8.8,-64.6,2.6,-66.8,12.6,-63.5C22.6,-60.3,32.3,-51.5,41.5,-57C50.7,-62.4,60.5,-82.1,63.7,-78.8C67,-75.6,63.8,-49.5,55.7,-33.6C47.6,-17.8,34.7,-12.1,41.2,0.3C47.8,12.8,73.8,31.9,75.2,42.3C76.6,52.7,53.4,54.3,37.3,53.4C21.2,52.5,12.1,49,3.3,44.2C-5.6,39.3,-14.1,33.1,-29.1,31.4C-44.1,29.8,-65.7,32.7,-72.2,25.4C-78.7,18.1,-70.2,0.6,-65.9,-16.1C-61.7,-32.8,-61.8,-48.7,-53.1,-56.3C-44.5,-63.9,-27.2,-63.2,-13.5,-58.9C0.3,-54.5,10.5,-46.6,22.1,-59C33.7,-71.5,46.8,-104.2,48.9,-102.5C51,-100.7,42.2,-64.6,32.9,-54.1Z" transform="translate(100 100)" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default Banner; 
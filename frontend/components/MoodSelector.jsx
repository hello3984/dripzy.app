import React, { useState } from 'react';
import { motion } from 'framer-motion';

const moods = [
  {
    id: 'festival',
    name: 'Festival',
    description: 'Bohemian vibes with statement pieces',
    color: '#F5A623',
    icon: '🎭',
    backgroundImage: 'url(https://images.unsplash.com/photo-1535805754665-0369aa54c5a7?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'boho',
    name: 'Bohemian',
    description: 'Free-spirited and earthy aesthetics',
    color: '#D0A85C',
    icon: '🌿',
    backgroundImage: 'url(https://images.unsplash.com/photo-1503146234394-631200675614?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'edgy',
    name: 'Edgy',
    description: 'Bold statements with attitude',
    color: '#2D3436',
    icon: '⚡',
    backgroundImage: 'url(https://images.unsplash.com/photo-1536243298747-ea8874136d64?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'elegant',
    name: 'Elegant',
    description: 'Timeless sophistication and grace',
    color: '#9B8BBE',
    icon: '✨',
    backgroundImage: 'url(https://images.unsplash.com/photo-1480881209288-2e4ee91cac42?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'vintage',
    name: 'Vintage',
    description: 'Nostalgic styles from decades past',
    color: '#B15B5B',
    icon: '🕰️',
    backgroundImage: 'url(https://images.unsplash.com/photo-1506025883753-c77a55138d8a?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'minimalist',
    name: 'Minimalist',
    description: 'Clean lines and understated elegance',
    color: '#DFDFDF',
    icon: '◽',
    backgroundImage: 'url(https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'streetwear',
    name: 'Streetwear',
    description: 'Urban comfort with a statement',
    color: '#4A90E2',
    icon: '🏙️',
    backgroundImage: 'url(https://images.unsplash.com/photo-1523398002811-999ca8dec234?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  },
  {
    id: 'preppy',
    name: 'Preppy',
    description: 'Polished collegiate style',
    color: '#33B679',
    icon: '🏫',
    backgroundImage: 'url(https://images.unsplash.com/photo-1556905055-8f358a7a47b2?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)',
  }
];

const MoodSelector = ({ onMoodSelect, selectedMood }) => {
  const [hoveredMood, setHoveredMood] = useState(null);

  return (
    <div className="mood-selector">
      <h2>Select Your Style Mood</h2>
      <p className="subtitle">Choose a mood that inspires your outfit today</p>
      
      <div className="mood-grid">
        {moods.map((mood) => (
          <motion.div
            key={mood.id}
            className={`mood-card ${selectedMood === mood.id ? 'selected' : ''}`}
            onClick={() => onMoodSelect(mood.id)}
            onMouseEnter={() => setHoveredMood(mood.id)}
            onMouseLeave={() => setHoveredMood(null)}
            whileHover={{ y: -8, scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div 
              className="mood-background" 
              style={{ backgroundImage: mood.backgroundImage }}
            />
            <div className="mood-content">
              <div className="mood-icon" style={{ backgroundColor: mood.color }}>
                {mood.icon}
              </div>
              <h3>{mood.name}</h3>
              
              <motion.div 
                className="mood-description"
                initial={{ opacity: 0, height: 0 }}
                animate={{ 
                  opacity: hoveredMood === mood.id || selectedMood === mood.id ? 1 : 0,
                  height: hoveredMood === mood.id || selectedMood === mood.id ? 'auto' : 0
                }}
                transition={{ duration: 0.2 }}
              >
                <p>{mood.description}</p>
              </motion.div>
            </div>
            
            {selectedMood === mood.id && (
              <motion.div 
                className="selected-indicator"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </motion.div>
        ))}
      </div>

      <style jsx>{`
        .mood-selector {
          margin: 2rem 0;
          padding: 1rem;
        }
        
        h2 {
          text-align: center;
          font-size: 2rem;
          margin-bottom: 0.5rem;
          font-weight: 600;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
          text-align: center;
          color: #718096;
          margin-bottom: 2rem;
          font-weight: 400;
        }
        
        .mood-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
          gap: 1.5rem;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .mood-card {
          position: relative;
          border-radius: 12px;
          overflow: hidden;
          height: 180px;
          cursor: pointer;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          transition: all 0.3s ease;
        }
        
        .mood-card.selected {
          box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
          border: 2px solid #764ba2;
        }
        
        .mood-background {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-size: cover;
          background-position: center;
          opacity: 0.7;
          z-index: 1;
          transition: opacity 0.3s ease;
        }
        
        .mood-card:hover .mood-background,
        .mood-card.selected .mood-background {
          opacity: 0.9;
          transform: scale(1.05);
        }
        
        .mood-content {
          position: relative;
          z-index: 2;
          padding: 1.25rem;
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
          background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.5) 40%, rgba(0,0,0,0) 100%);
        }
        
        .mood-icon {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.2rem;
          margin-bottom: 0.5rem;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        h3 {
          color: white;
          font-size: 1.3rem;
          font-weight: 600;
          margin: 0.5rem 0;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        }
        
        .mood-description {
          overflow: hidden;
        }
        
        .mood-description p {
          color: rgba(255, 255, 255, 0.9);
          font-size: 0.9rem;
          margin: 0;
          line-height: 1.4;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .selected-indicator {
          position: absolute;
          top: 10px;
          right: 10px;
          width: 20px;
          height: 20px;
          background-color: #764ba2;
          border-radius: 50%;
          z-index: 3;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .selected-indicator::after {
          content: '✓';
          color: white;
          font-size: 12px;
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }
        
        @media (max-width: 768px) {
          .mood-grid {
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 1rem;
          }
          
          .mood-card {
            height: 150px;
          }
          
          h3 {
            font-size: 1.1rem;
          }
        }
      `}</style>
    </div>
  );
};

export default MoodSelector; 
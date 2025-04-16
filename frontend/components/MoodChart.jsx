import { useState } from 'react';
import { motion } from 'framer-motion';

const moods = [
  { id: 'boho', name: 'Bohemian', color: '#d4a373', description: 'Free-spirited, natural elements with a mix of patterns' },
  { id: 'minimalist', name: 'Minimalist', color: '#f8f9fa', description: 'Clean lines, monochromatic palette, and simplicity' },
  { id: 'glam', name: 'Glamorous', color: '#c9184a', description: 'Bold, luxurious with statement pieces and shine' },
  { id: 'preppy', name: 'Preppy', color: '#4361ee', description: 'Classic, polished with structured silhouettes' },
  { id: 'streetwear', name: 'Streetwear', color: '#2d3142', description: 'Urban, casual, and contemporary with bold graphics' },
  { id: 'vintage', name: 'Vintage', color: '#774936', description: 'Timeless pieces inspired by past decades' },
  { id: 'romantic', name: 'Romantic', color: '#ffb5a7', description: 'Soft, feminine with delicate details and flowing fabrics' },
  { id: 'edgy', name: 'Edgy', color: '#343a40', description: 'Bold, rebellious with unconventional details' },
  { id: 'athleisure', name: 'Athleisure', color: '#52b788', description: 'Athletic-inspired, comfortable yet stylish' },
  { id: 'festival', name: 'Festival', color: '#9d4edd', description: 'Vibrant, expressive, and eclectic for music events' },
];

const MoodChart = ({ onSelectMood, selectedMood }) => {
  const [expandedMood, setExpandedMood] = useState(null);

  const handleMoodClick = (mood) => {
    onSelectMood(mood);
  };

  const handleMoodHover = (mood) => {
    setExpandedMood(mood);
  };

  return (
    <div className="mood-chart">
      <h2 className="title">What's your style vibe today?</h2>
      <div className="moods-container">
        {moods.map((mood) => (
          <motion.div
            key={mood.id}
            className={`mood-item ${selectedMood === mood.id ? 'selected' : ''}`}
            onClick={() => handleMoodClick(mood.id)}
            onMouseEnter={() => handleMoodHover(mood.id)}
            onMouseLeave={() => setExpandedMood(null)}
            whileHover={{ scale: 1.05, y: -5 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div 
              className="mood-color" 
              style={{ backgroundColor: mood.color }}
            />
            <div className="mood-content">
              <span className="mood-name">{mood.name}</span>
              {expandedMood === mood.id && (
                <motion.p 
                  className="mood-description"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  {mood.description}
                </motion.p>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <style jsx>{`
        .mood-chart {
          width: 100%;
          max-width: 800px;
          margin: 2rem auto;
          padding: 1rem;
        }

        .title {
          text-align: center;
          font-size: 1.5rem;
          font-weight: 500;
          margin-bottom: 1.5rem;
          color: #333;
          font-family: 'Playfair Display', serif;
        }

        .moods-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 1rem;
        }

        .mood-item {
          background-color: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          flex-direction: column;
          height: 100%;
          position: relative;
        }

        .mood-item.selected {
          box-shadow: 0 0 0 2px ${expandedMood ? moods.find(m => m.id === expandedMood)?.color : '#805ad5'};
        }

        .mood-color {
          height: 8px;
          width: 100%;
        }

        .mood-content {
          padding: 1rem;
          flex-grow: 1;
          display: flex;
          flex-direction: column;
        }

        .mood-name {
          font-weight: 500;
          margin-bottom: 0.5rem;
          font-size: 1rem;
        }

        .mood-description {
          font-size: 0.875rem;
          color: #666;
          margin: 0;
          line-height: 1.4;
        }

        @media (max-width: 768px) {
          .moods-container {
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
          }
          
          .title {
            font-size: 1.25rem;
          }
        }
      `}</style>
    </div>
  );
};

export default MoodChart; 
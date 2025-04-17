import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MoodSelector from '../components/MoodSelector';

const StyleExplorer = () => {
  const [selectedMood, setSelectedMood] = useState('festival');
  const [loading, setLoading] = useState(true);
  const [outfits, setOutfits] = useState([]);
  
  useEffect(() => {
    fetchOutfitsForMood(selectedMood);
  }, [selectedMood]);
  
  const fetchOutfitsForMood = (mood) => {
    setLoading(true);
    
    // Simulate API call with setTimeout
    setTimeout(() => {
      // Mock data - in a real app, this would come from your API
      const mockOutfits = [
        {
          id: 'outfit1',
          name: 'Desert Dreamer',
          description: 'A free-spirited ensemble perfect for dancing in the desert sunset.',
          style: mood,
          items: [
            { name: 'Flowy Maxi Dress', category: 'Dress', price: 89.99, image: 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' },
            { name: 'Gladiator Sandals', category: 'Footwear', price: 59.99, image: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' },
            { name: 'Wide Brim Hat', category: 'Accessories', price: 45.00, image: 'https://images.unsplash.com/photo-1575428652377-a2d80e2277fc?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' }
          ],
          totalPrice: 194.98
        },
        {
          id: 'outfit2',
          name: 'Bohemian Rhapsody',
          description: 'Channel your inner flower child with this bohemian-inspired look.',
          style: mood,
          items: [
            { name: 'Embroidered Blouse', category: 'Top', price: 65.00, image: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' },
            { name: 'Denim Cutoffs', category: 'Bottom', price: 49.99, image: 'https://images.unsplash.com/photo-1565084888279-aca607ecce0c?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' },
            { name: 'Fringe Bag', category: 'Accessories', price: 79.00, image: 'https://images.unsplash.com/photo-1594223274512-ad4803739b7c?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=400&q=80' }
          ],
          totalPrice: 193.99
        }
      ];
      
      setOutfits(mockOutfits);
      setLoading(false);
    }, 1500);
  };
  
  const handleMoodSelect = (mood) => {
    setSelectedMood(mood);
  };
  
  return (
    <div className="style-explorer">
      <div className="page-header">
        <h1>Style Explorer</h1>
        <p>Discover your perfect festival look based on your style mood</p>
      </div>
      
      <MoodSelector selectedMood={selectedMood} onMoodSelect={handleMoodSelect} />
      
      <div className="outfits-section">
        <h2>Recommended Outfits</h2>
        
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Curating your personalized outfits...</p>
          </div>
        ) : (
          <AnimatePresence>
            <div className="outfits-grid">
              {outfits.map((outfit) => (
                <motion.div 
                  key={outfit.id}
                  className="outfit-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4 }}
                  whileHover={{ y: -10, boxShadow: '0 15px 30px rgba(0,0,0,0.1)' }}
                >
                  <div className="outfit-header">
                    <h3>{outfit.name}</h3>
                    <span className="price">${outfit.totalPrice.toFixed(2)}</span>
                  </div>
                  
                  <p className="outfit-description">{outfit.description}</p>
                  
                  <div className="outfit-items">
                    {outfit.items.map((item, index) => (
                      <div key={index} className="item-preview">
                        <div 
                          className="item-image" 
                          style={{backgroundImage: `url(${item.image})`}}
                        ></div>
                        <div className="item-details">
                          <span className="item-name">{item.name}</span>
                          <span className="item-price">${item.price.toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="outfit-actions">
                    <button className="btn-save">Save Outfit</button>
                    <button className="btn-details">View Details</button>
                  </div>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
      
      <style jsx>{`
        .style-explorer {
          max-width: 1200px;
          margin: 0 auto;
          padding: 40px 20px;
        }
        
        .page-header {
          text-align: center;
          margin-bottom: 30px;
        }
        
        .page-header h1 {
          font-family: 'Playfair Display', serif;
          font-size: 3rem;
          font-weight: 500;
          margin: 0 0 10px;
          color: #333;
        }
        
        .page-header p {
          font-size: 1.1rem;
          color: #666;
          margin: 0;
        }
        
        .outfits-section {
          margin-top: 50px;
          padding-top: 30px;
          border-top: 1px solid #eee;
        }
        
        .outfits-section h2 {
          font-family: 'Playfair Display', serif;
          font-size: 2rem;
          font-weight: 500;
          margin: 0 0 30px;
          color: #333;
          text-align: center;
        }
        
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 0;
        }
        
        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(0, 0, 0, 0.1);
          border-left-color: #D4AF37;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        .loading-container p {
          color: #666;
          font-size: 1.1rem;
        }
        
        .outfits-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
          gap: 30px;
        }
        
        .outfit-card {
          background-color: white;
          border-radius: 15px;
          overflow: hidden;
          box-shadow: 0 5px 15px rgba(0,0,0,0.05);
          transition: all 0.3s ease;
          padding: 25px;
        }
        
        .outfit-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        
        .outfit-header h3 {
          font-family: 'Playfair Display', serif;
          font-size: 1.6rem;
          font-weight: 500;
          margin: 0;
          color: #333;
        }
        
        .price {
          font-size: 1.4rem;
          font-weight: 500;
          color: #D4AF37;
        }
        
        .outfit-description {
          color: #666;
          margin: 0 0 20px;
          line-height: 1.5;
        }
        
        .outfit-items {
          display: flex;
          gap: 15px;
          margin-bottom: 25px;
        }
        
        .item-preview {
          flex: 1;
          border-radius: 10px;
          overflow: hidden;
          box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }
        
        .item-image {
          height: 180px;
          background-size: cover;
          background-position: center;
        }
        
        .item-details {
          padding: 12px;
          background-color: #f9f9f9;
        }
        
        .item-name {
          display: block;
          font-weight: 500;
          font-size: 0.9rem;
          margin-bottom: 3px;
          color: #333;
        }
        
        .item-price {
          font-size: 0.85rem;
          color: #666;
        }
        
        .outfit-actions {
          display: flex;
          gap: 15px;
        }
        
        .outfit-actions button {
          padding: 12px 20px;
          border-radius: 8px;
          font-weight: 500;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s ease;
          flex: 1;
        }
        
        .btn-save {
          background-color: #D4AF37;
          color: white;
          border: none;
        }
        
        .btn-details {
          background-color: white;
          color: #333;
          border: 1px solid #ddd;
        }
        
        .btn-save:hover {
          background-color: #C09F2F;
        }
        
        .btn-details:hover {
          background-color: #f5f5f5;
        }
        
        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 2.5rem;
          }
          
          .outfits-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default StyleExplorer; 
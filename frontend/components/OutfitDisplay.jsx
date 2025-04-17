import { motion } from 'framer-motion';
import Image from 'next/image';

const OutfitDisplay = ({ outfit }) => {
  if (!outfit) return null;
  
  return (
    <motion.div 
      className="outfit-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="outfit-header">
        <h2>{outfit.name || 'Custom Outfit'}</h2>
        {outfit.occasion && <span className="occasion">{outfit.occasion}</span>}
      </div>
      
      <p className="description">{outfit.description || 'A curated selection of items that perfectly complement each other.'}</p>
      
      <div className="items-grid">
        {Array.isArray(outfit.items) && outfit.items.map((item, index) => (
          <motion.div 
            key={item.id || index}
            className="item-card"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <div className="item-image">
              {item.image_url ? (
                <Image 
                  src={item.image_url} 
                  alt={item.name || `Item ${index + 1}`}
                  width={200}
                  height={200}
                  objectFit="cover"
                />
              ) : (
                <div className="placeholder-image">
                  <span>{item.category?.charAt(0) || '?'}</span>
                </div>
              )}
            </div>
            <div className="item-details">
              <h3>{item.name || `Item ${index + 1}`}</h3>
              {item.category && <span className="category">{item.category}</span>}
              {item.price && <span className="price">${parseFloat(item.price).toFixed(2)}</span>}
              {item.description && <p className="item-description">{item.description}</p>}
            </div>
          </motion.div>
        ))}
      </div>
      
      {outfit.total_price && (
        <div className="price-summary">
          <span>Total Price:</span>
          <strong>${parseFloat(outfit.total_price).toFixed(2)}</strong>
        </div>
      )}
      
      <style jsx>{`
        .outfit-container {
          background: white;
          border-radius: 16px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
          padding: 2rem;
          margin-bottom: 2rem;
          overflow: hidden;
        }
        
        .outfit-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        
        h2 {
          font-family: 'Playfair Display', serif;
          font-size: 1.8rem;
          font-weight: 600;
          margin: 0;
          color: #2d3748;
        }
        
        .occasion {
          background-color: #e9d8fd;
          color: #6b46c1;
          padding: 0.25rem 1rem;
          border-radius: 20px;
          font-size: 0.8rem;
          font-weight: 500;
        }
        
        .description {
          color: #718096;
          margin-bottom: 2rem;
          font-size: 0.95rem;
          line-height: 1.5;
        }
        
        .items-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
          gap: 1.5rem;
          margin-bottom: 1.5rem;
        }
        
        .item-card {
          background: #f8fafc;
          border-radius: 12px;
          overflow: hidden;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .item-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        .item-image {
          height: 200px;
          background: #edf2f7;
          position: relative;
          overflow: hidden;
        }
        
        .placeholder-image {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(45deg, #e6e6e6, #f5f5f5);
        }
        
        .placeholder-image span {
          font-size: 2rem;
          color: #a0aec0;
          font-weight: 600;
        }
        
        .item-details {
          padding: 1rem;
        }
        
        .item-details h3 {
          margin: 0 0 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          color: #2d3748;
        }
        
        .category {
          display: inline-block;
          background-color: #e6fffa;
          color: #319795;
          padding: 0.15rem 0.5rem;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 500;
          margin-right: 0.5rem;
        }
        
        .price {
          display: inline-block;
          font-weight: 600;
          color: #4a5568;
          font-size: 0.9rem;
        }
        
        .item-description {
          margin: 0.5rem 0 0;
          font-size: 0.8rem;
          color: #718096;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        .price-summary {
          display: flex;
          justify-content: flex-end;
          align-items: center;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px dashed #e2e8f0;
        }
        
        .price-summary span {
          color: #718096;
          margin-right: 0.5rem;
        }
        
        .price-summary strong {
          font-size: 1.2rem;
          color: #2d3748;
        }
        
        @media (max-width: 768px) {
          .outfit-container {
            padding: 1.5rem;
          }
          
          .items-grid {
            grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
          }
          
          h2 {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </motion.div>
  );
};

export default OutfitDisplay; 
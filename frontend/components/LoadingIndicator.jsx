import { motion } from 'framer-motion';

const LoadingIndicator = ({ message = 'Curating your fashion recommendations...' }) => {
  return (
    <div className="loading-container">
      <div className="spinner-container">
        <motion.div
          className="spinner"
          animate={{
            rotate: 360
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "linear"
          }}
        />
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="loading-message"
      >
        {message}
      </motion.p>
      
      <style jsx>{`
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 3rem 1rem;
        }
        
        .spinner-container {
          position: relative;
          width: 60px;
          height: 60px;
          margin-bottom: 1.5rem;
        }
        
        .spinner {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border: 3px solid rgba(0, 0, 0, 0.05);
          border-top: 3px solid #805ad5;
          border-radius: 50%;
        }
        
        .loading-message {
          font-size: 1rem;
          color: #4a5568;
          text-align: center;
          max-width: 300px;
          margin: 0;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};

export default LoadingIndicator; 
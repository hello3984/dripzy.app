import React from 'react';

/**
 * ProductCard component for displaying product information
 */
const ProductCard = ({ product }) => {
  if (!product) return null;

  // Handle default values gracefully
  const {
    name = 'Product Name',
    price = 0,
    image_url = '/placeholder.jpg',
    brand = '',
    category = ''
  } = product;

  // Format price with two decimal places
  const formattedPrice = typeof price === 'number' ? price.toFixed(2) : '0.00';

  // Handle image error
  const handleImageError = (e) => {
    e.target.src = '/placeholder.jpg';
  };

  return (
    <div className="product-card">
      <img 
        src={image_url} 
        alt={name} 
        onError={handleImageError}
        className="product-image"
      />
      <div className="product-info">
        <h4 className="product-name">{name}</h4>
        {brand && <p className="product-brand">{brand}</p>}
        {category && <p className="product-category">{category}</p>}
        <p className="product-price">${formattedPrice}</p>
      </div>
    </div>
  );
};

export default ProductCard; 
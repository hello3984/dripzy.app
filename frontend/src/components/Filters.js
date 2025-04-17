import React from 'react';

/**
 * Filters component for ProductsPage
 */
const Filters = ({ onFilterChange }) => {
  return (
    <div className="filters-container">
      <h4>Filters</h4>
      <div className="filter-options">
        {/* Filter options will go here */}
        <div className="filter-group">
          <label>Price Range</label>
          <div className="range-inputs">
            <input type="range" min="0" max="1000" onChange={(e) => onFilterChange?.({ price: e.target.value })} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Filters; 
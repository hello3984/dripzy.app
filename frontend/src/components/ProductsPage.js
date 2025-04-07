import React, { useState, useEffect } from 'react';
import { searchProducts } from '../services/api';
import { getAffiliateUrl } from '../services/amazon';

const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const [pageSize] = useState(12);
  
  // Filter states
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [brand, setBrand] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [source, setSource] = useState('');

  // Categories
  const categories = [
    { id: '', name: 'All Categories' },
    { id: 'top', name: 'Tops' },
    { id: 'bottom', name: 'Bottoms' },
    { id: 'dress', name: 'Dresses' },
    { id: 'shoes', name: 'Shoes' },
    { id: 'accessory', name: 'Accessories' },
    { id: 'outerwear', name: 'Outerwear' }
  ];
  
  // Product sources
  const sources = [
    { id: '', name: 'All Sources' },
    { id: 'amazon', name: 'Amazon' },
    { id: 'asos', name: 'ASOS' },
    { id: 'shopify', name: 'Shopify' }
  ];

  // Load products
  useEffect(() => {
    fetchProducts();
  }, [currentPage]);

  const fetchProducts = async (filters = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      // Merge current filters with any new filters
      const searchFilters = {
        query: filters.query !== undefined ? filters.query : query,
        category: filters.category !== undefined ? filters.category : category,
        brand: filters.brand !== undefined ? filters.brand : brand,
        min_price: filters.minPrice !== undefined ? filters.minPrice : minPrice,
        max_price: filters.maxPrice !== undefined ? filters.maxPrice : maxPrice,
        source: filters.source !== undefined ? filters.source : source,
        page: filters.page !== undefined ? filters.page : currentPage,
        page_size: pageSize
      };
      
      // Remove empty filters
      Object.keys(searchFilters).forEach(key => 
        !searchFilters[key] && delete searchFilters[key]
      );
      
      const data = await searchProducts(searchFilters);
      
      setProducts(data.products);
      setTotalProducts(data.total);
      
      // Update filter states if they were passed in
      if (filters.query !== undefined) setQuery(filters.query);
      if (filters.category !== undefined) setCategory(filters.category);
      if (filters.brand !== undefined) setBrand(filters.brand);
      if (filters.minPrice !== undefined) setMinPrice(filters.minPrice);
      if (filters.maxPrice !== undefined) setMaxPrice(filters.maxPrice);
      if (filters.source !== undefined) setSource(filters.source);
      if (filters.page !== undefined) setCurrentPage(filters.page);
      
    } catch (err) {
      console.error('Error fetching products:', err);
      setError('Failed to fetch products. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProducts({ page: 1 }); // Reset to page 1 when filtering
  };

  const clearFilters = () => {
    setQuery('');
    setCategory('');
    setBrand('');
    setMinPrice('');
    setMaxPrice('');
    setSource('');
    fetchProducts({
      query: '',
      category: '',
      brand: '',
      minPrice: '',
      maxPrice: '',
      source: '',
      page: 1
    });
  };

  const handlePageChange = (page) => {
    if (page >= 1 && page <= Math.ceil(totalProducts / pageSize)) {
      fetchProducts({ page });
    }
  };

  return (
    <div className="products-page">
      <div className="container">
        <h1>Shop Products</h1>
        
        <div className="products-layout">
          <aside className="filters-sidebar">
            <h2>Filters</h2>
            <form onSubmit={handleSearch} className="filters-form">
              <div className="form-group">
                <label htmlFor="search">Search</label>
                <input
                  type="text"
                  id="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search products..."
                  className="search-input"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="category">Category</label>
                <select
                  id="category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="category-select"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="brand">Brand</label>
                <input
                  type="text"
                  id="brand"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  placeholder="Brand name"
                  className="brand-input"
                />
              </div>
              
              <div className="form-group price-group">
                <label>Price Range</label>
                <div className="price-inputs">
                  <input
                    type="number"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    placeholder="Min"
                    className="price-input"
                    min="0"
                  />
                  <span className="price-separator">to</span>
                  <input
                    type="number"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    placeholder="Max"
                    className="price-input"
                    min="0"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="source">Source</label>
                <select
                  id="source"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="source-select"
                >
                  {sources.map(src => (
                    <option key={src.id} value={src.id}>{src.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-buttons">
                <button type="submit" className="apply-filters-btn">Apply Filters</button>
                <button type="button" onClick={clearFilters} className="clear-filters-btn">Clear Filters</button>
              </div>
            </form>
          </aside>
          
          <main className="products-main">
            {loading ? (
              <div className="loading">Loading products...</div>
            ) : error ? (
              <div className="error-message">{error}</div>
            ) : (
              <>
                <div className="products-header">
                  <div className="products-count">
                    {totalProducts} Products Found
                  </div>
                  <div className="products-sort">
                    <label htmlFor="sort">Sort by:</label>
                    <select id="sort" className="sort-select">
                      <option value="relevance">Relevance</option>
                      <option value="price-low">Price: Low to High</option>
                      <option value="price-high">Price: High to Low</option>
                      <option value="name">Name</option>
                    </select>
                  </div>
                </div>
                
                {products.length === 0 ? (
                  <div className="no-products">
                    <p>No products found. Try adjusting your filters.</p>
                  </div>
                ) : (
                  <div className="products-grid">
                    {products.map(product => (
                      <div className="product-card" key={product.id}>
                        <div className="product-image">
                          <img src={product.image_url || 'https://via.placeholder.com/300x400'} alt={product.name} />
                          {product.source && (
                            <div className="product-source">{product.source}</div>
                          )}
                        </div>
                        <div className="product-info">
                          <h3 className="product-name">{product.name}</h3>
                          <p className="product-brand">{product.brand}</p>
                          <p className="product-price">${product.price.toFixed(2)}</p>
                          <div className="product-actions">
                            <a 
                              href={getAffiliateUrl(product.url, product.source)} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="view-product-btn"
                            >
                              View Product
                            </a>
                            <button className="try-on-btn">Try On</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Pagination */}
                {products.length > 0 && (
                  <div className="pagination">
                    <button 
                      className="pagination-btn" 
                      disabled={currentPage === 1}
                      onClick={() => handlePageChange(currentPage - 1)}
                    >
                      Previous
                    </button>
                    
                    <div className="pagination-info">
                      Page {currentPage} of {Math.ceil(totalProducts / pageSize)}
                    </div>
                    
                    <button 
                      className="pagination-btn"
                      disabled={currentPage === Math.ceil(totalProducts / pageSize)}
                      onClick={() => handlePageChange(currentPage + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default ProductsPage; 
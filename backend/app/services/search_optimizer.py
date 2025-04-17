#!/usr/bin/env python
"""
Optimized search logic for product matching based on SerpAPI analysis
This module provides improved search strategies for product matching
"""
import os
import sys
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class SearchOptimizer:
    """
    Optimizes search queries for product matching based on analysis
    """
    
    # Search modifiers in order of effectiveness (will be updated by analysis)
    SEARCH_MODIFIERS = [
        " clothing",
        " fashion",
        " apparel",
        " wear",
        ""  # No modifier as fallback
    ]
    
    # Common filler words to remove
    FILLER_WORDS = [
        "a", "an", "the", "with", "for", "and", "or", 
        "that", "this", "these", "those", "some", "any"
    ]
    
    # Words that improve search quality
    QUALITY_TERMS = [
        "premium", "quality", "authentic", "genuine", "original",
        "brand", "new", "official", "designer", "trending"
    ]
    
    # Category terms that might improve search results
    CATEGORY_ENHANCERS = {
        "jeans": ["denim", "pants"],
        "t-shirt": ["tee", "top"],
        "shoes": ["footwear", "sneakers"],
        "dress": ["gown", "formal"],
        "sweater": ["pullover", "knit"],
        "jacket": ["coat", "outerwear"],
        "pants": ["trousers", "slacks"],
        "skirt": ["bottom"],
        "boots": ["footwear"],
        "accessories": ["items", "fashion"],
    }
    
    # Load analysis results if available
    def __init__(self):
        self.analysis_loaded = False
        self.best_modifier = " clothing"  # Default
        self.category_success_rates = {}
        self.color_improves_search = True
        self.brand_improves_search = True
        
        # Try to load analysis results
        try:
            analysis_path = os.path.join(
                os.path.dirname(__file__), 
                "serpapi_analysis.json"
            )
            
            if os.path.exists(analysis_path):
                with open(analysis_path, 'r') as f:
                    analysis = json.load(f)
                self._process_analysis(analysis)
                self.analysis_loaded = True
                logger.info("Loaded search optimization data from analysis results")
            else:
                logger.info("No analysis data found, using default optimization settings")
        except Exception as e:
            logger.warning(f"Error loading analysis data: {e}")
    
    def _process_analysis(self, analysis: Dict[str, Any]):
        """Process the analysis results to set optimal search parameters"""
        if "modifier_stats" in analysis:
            # Find best modifier
            best_success_rate = 0
            best_modifier = None
            
            for modifier, stats in analysis["modifier_stats"].items():
                success = stats.get("success", 0)
                count = stats.get("count", 0)
                if count > 0:
                    success_rate = (success / count) * 100
                    if success_rate > best_success_rate:
                        best_success_rate = success_rate
                        best_modifier = modifier
            
            if best_modifier:
                self.best_modifier = best_modifier
                
                # Reorder modifiers based on success rates
                ordered_modifiers = []
                for modifier, stats in sorted(
                    analysis["modifier_stats"].items(),
                    key=lambda x: x[1].get("success", 0) / max(x[1].get("count", 1), 1),
                    reverse=True
                ):
                    ordered_modifiers.append(modifier)
                
                # Add any missing default modifiers at the end
                for mod in self.SEARCH_MODIFIERS:
                    if mod not in ordered_modifiers:
                        ordered_modifiers.append(mod)
                
                self.SEARCH_MODIFIERS = ordered_modifiers
        
        # Extract success rates by category
        if "results" in analysis:
            category_counts = {}
            category_successes = {}
            
            for result in analysis["results"]:
                category = result.get("category")
                if category:
                    category_counts[category] = category_counts.get(category, 0) + 1
                    if result.get("success", False):
                        category_successes[category] = category_successes.get(category, 0) + 1
            
            # Calculate success rates
            for category, count in category_counts.items():
                if count > 0:
                    success = category_successes.get(category, 0)
                    self.category_success_rates[category] = success / count
            
            # Determine if color improves search
            color_success = 0
            color_total = 0
            no_color_success = 0
            no_color_total = 0
            
            for result in analysis["results"]:
                if result.get("color"):
                    color_total += 1
                    if result.get("success", False):
                        color_success += 1
                else:
                    no_color_total += 1
                    if result.get("success", False):
                        no_color_success += 1
            
            if color_total > 0 and no_color_total > 0:
                color_rate = color_success / color_total
                no_color_rate = no_color_success / no_color_total
                self.color_improves_search = color_rate > no_color_rate
    
    def optimize_search_query(self, item: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Build an optimized search query from item details
        
        Args:
            item: Dictionary containing item attributes like category, color, etc.
            
        Returns:
            Tuple containing:
              - Primary optimized query string
              - List of fallback query strings to try if primary fails
        """
        # Extract item attributes
        search_terms = item.get('search_keywords', [])
        color = item.get('color', '')
        category = item.get('category', '')
        brand = item.get('brand', '')
        description = item.get('description', '')
        
        # Primary query terms
        primary_terms = []
        
        # Start with brand if available (usually most specific)
        if brand and len(brand) < 25:  # Skip very long brand strings
            primary_terms.append(brand)
        
        # Add color if it improves search
        if color and self.color_improves_search:
            primary_terms.append(color)
        
        # Add category
        if category:
            primary_terms.append(category)
            
            # Add category enhancers if appropriate
            category_lower = category.lower()
            for cat, enhancers in self.CATEGORY_ENHANCERS.items():
                if cat in category_lower:
                    # Just add one enhancer to avoid query getting too long
                    primary_terms.append(enhancers[0])
                    break
        
        # Use search keywords if available
        if search_terms and len(search_terms) > 0:
            filtered_terms = [term for term in search_terms if term and len(term.strip()) > 0]
            primary_terms.extend(filtered_terms)
        # Otherwise use description
        elif description:
            # Clean description - remove filler words
            clean_description = description.lower()
            for word in self.FILLER_WORDS:
                clean_description = re.sub(r'\b' + word + r'\b', ' ', clean_description, flags=re.IGNORECASE)
            
            # Remove extra spaces
            clean_description = re.sub(r'\s+', ' ', clean_description).strip()
            
            # Use first 6-8 words for more focused search
            desc_words = clean_description.split()[:7]
            if desc_words:
                primary_terms.append(' '.join(desc_words))
                
        # Create primary query
        primary_query = ' '.join([term for term in primary_terms if term and len(term.strip()) > 0])
        
        # Truncate long queries
        primary_query = primary_query[:100] if len(primary_query) > 100 else primary_query
        
        # Generate fallback queries in case primary fails
        fallback_queries = []
        
        # Fallback 1: Just brand + category + color (more focused)
        if brand and category:
            fallback1 = f"{brand} {category}"
            if color:
                fallback1 = f"{color} {fallback1}"
            fallback_queries.append(fallback1)
        
        # Fallback 2: Just category and description start
        if category and description:
            desc_start = ' '.join(description.split()[:3])  # First 3 words
            fallback_queries.append(f"{category} {desc_start}")
        
        # Fallback 3: Just search keywords without other attributes
        if search_terms and len(search_terms) > 0:
            fallback_queries.append(' '.join(filtered_terms)[:100])
        
        # Add best modifier to primary query
        primary_query_with_modifier = primary_query + self.best_modifier
        
        # Make sure we don't duplicate search terms
        fallback_queries = [q for q in fallback_queries if q != primary_query]
        
        # Add fallback modifiers to try
        final_fallbacks = []
        for query in [primary_query] + fallback_queries:
            # Skip empty queries
            if not query.strip():
                continue
                
            # Add different modifiers for variety
            for modifier in self.SEARCH_MODIFIERS:
                if modifier != self.best_modifier:  # Skip best modifier as it's already in primary
                    final_fallbacks.append(query + modifier)
                
        return primary_query_with_modifier, final_fallbacks
    
    def enhance_item_for_search(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance an item with additional terms to improve search quality
        
        Args:
            item: Dictionary containing item attributes
            
        Returns:
            Enhanced item with improved search terms
        """
        # Create a copy to avoid modifying original
        enhanced = item.copy()
        
        # Extract and enhance search terms
        search_terms = enhanced.get('search_keywords', [])
        if not search_terms:
            search_terms = []
            enhanced['search_keywords'] = search_terms
            
        # Add category enhancers if they don't exist
        category = enhanced.get('category', '').lower()
        if category:
            for cat, enhancers in self.CATEGORY_ENHANCERS.items():
                if cat in category:
                    for enhancer in enhancers:
                        # Check if enhancer or similar term already exists
                        if not any(enhancer in term.lower() for term in search_terms):
                            search_terms.append(enhancer)
        
        # Add one quality term if appropriate and not already present
        if search_terms and category:
            # Determine which quality term might be appropriate
            if category.lower() in ['jeans', 'dress', 'jacket', 'sweater']:
                quality_idx = 0  # "premium" 
            elif category.lower() in ['t-shirt', 'shoes', 'boots']:
                quality_idx = 1  # "quality"
            else:
                quality_idx = 2  # "authentic"
            
            quality_term = self.QUALITY_TERMS[quality_idx]
            
            # Add if not already present
            if not any(quality_term in term.lower() for term in search_terms):
                search_terms.append(quality_term)
        
        return enhanced
    
    def get_search_recommendations(self) -> Dict[str, Any]:
        """
        Get search recommendations based on analysis
        
        Returns:
            Dictionary with search recommendations
        """
        recommendations = {
            "best_modifier": self.best_modifier,
            "color_improves_search": self.color_improves_search,
            "category_success_rates": self.category_success_rates,
            "search_modifiers_ranked": self.SEARCH_MODIFIERS
        }
        
        return recommendations

# Singleton instance for app-wide use
search_optimizer = SearchOptimizer()

def get_search_optimizer() -> SearchOptimizer:
    """Get the search optimizer singleton instance"""
    return search_optimizer 
// Google Tag Manager Analytics Service for Fashion AI Platform
// Tracks all user interactions and fashion-specific events

class AnalyticsService {
    constructor() {
        this.dataLayer = window.dataLayer || [];
        this.initializeDataLayer();
    }

    initializeDataLayer() {
        // Initialize dataLayer if not already present
        window.dataLayer = window.dataLayer || [];
        
        // Set initial user properties
        this.dataLayer.push({
            'platform': 'dripzy',
            'app_version': '1.0.0',
            'user_agent': navigator.userAgent,
            'timestamp': new Date().toISOString()
        });
    }

    // OUTFIT GENERATION TRACKING
    trackOutfitGeneration(data) {
        this.dataLayer.push({
            'event': 'outfit_generation',
            'event_category': 'Fashion AI',
            'event_action': 'Generate Outfit',
            'event_label': data.prompt || 'Custom Prompt',
            'custom_parameters': {
                'prompt': data.prompt,
                'gender': data.gender,
                'budget': data.budget,
                'style': data.style,
                'occasion': data.occasion,
                'response_time': data.responseTime,
                'items_count': data.itemsCount,
                'success': data.success
            }
        });
    }

    trackOutfitGenerationStart(prompt) {
        this.dataLayer.push({
            'event': 'outfit_generation_start',
            'event_category': 'Fashion AI',
            'event_action': 'Start Generation',
            'event_label': prompt,
            'custom_parameters': {
                'prompt': prompt,
                'timestamp': new Date().toISOString()
            }
        });
    }

    trackOutfitGenerationComplete(data) {
        this.dataLayer.push({
            'event': 'outfit_generation_complete',
            'event_category': 'Fashion AI', 
            'event_action': 'Complete Generation',
            'event_label': data.prompt,
            'custom_parameters': {
                'prompt': data.prompt,
                'success': data.success,
                'error': data.error || null,
                'response_time_ms': data.responseTime,
                'items_generated': data.itemsCount,
                'total_price': data.totalPrice
            }
        });
    }

    // PRODUCT INTERACTION TRACKING
    trackProductClick(product) {
        this.dataLayer.push({
            'event': 'product_click',
            'event_category': 'Product Interaction',
            'event_action': 'Click Product',
            'event_label': product.product_name,
            'ecommerce': {
                'currency': 'USD',
                'value': product.price,
                'items': [{
                    'item_id': product.product_id,
                    'item_name': product.product_name,
                    'item_category': product.category,
                    'item_brand': product.brand,
                    'price': product.price,
                    'quantity': 1
                }]
            }
        });
    }

    trackProductView(product) {
        this.dataLayer.push({
            'event': 'view_item',
            'event_category': 'Product Interaction',
            'event_action': 'View Product',
            'event_label': product.product_name,
            'ecommerce': {
                'currency': 'USD',
                'value': product.price,
                'items': [{
                    'item_id': product.product_id,
                    'item_name': product.product_name,
                    'item_category': product.category,
                    'item_brand': product.brand,
                    'price': product.price
                }]
            }
        });
    }

    trackRetailerRedirect(product, retailer) {
        this.dataLayer.push({
            'event': 'retailer_redirect',
            'event_category': 'Product Interaction',
            'event_action': 'Visit Retailer',
            'event_label': `${retailer} - ${product.product_name}`,
            'custom_parameters': {
                'retailer': retailer,
                'product_id': product.product_id,
                'product_name': product.product_name,
                'brand': product.brand,
                'price': product.price,
                'redirect_url': product.url
            }
        });
    }

    // THEME AND STYLE TRACKING
    trackThemeSelection(theme) {
        this.dataLayer.push({
            'event': 'theme_selection',
            'event_category': 'Style Preferences',
            'event_action': 'Select Theme',
            'event_label': theme,
            'custom_parameters': {
                'theme': theme,
                'timestamp': new Date().toISOString()
            }
        });
    }

    trackStylePreference(data) {
        this.dataLayer.push({
            'event': 'style_preference',
            'event_category': 'Style Preferences',
            'event_action': 'Set Preference',
            'event_label': `${data.type}: ${data.value}`,
            'custom_parameters': {
                'preference_type': data.type,
                'preference_value': data.value,
                'gender': data.gender,
                'budget_range': data.budgetRange
            }
        });
    }

    // USER JOURNEY TRACKING
    trackPageView(page) {
        this.dataLayer.push({
            'event': 'page_view',
            'event_category': 'Navigation',
            'event_action': 'Page View',
            'event_label': page,
            'page_title': document.title,
            'page_location': window.location.href,
            'page_path': window.location.pathname
        });
    }

    trackUserInteraction(action, element) {
        this.dataLayer.push({
            'event': 'user_interaction',
            'event_category': 'User Interface',
            'event_action': action,
            'event_label': element,
            'custom_parameters': {
                'interaction_type': action,
                'element': element,
                'timestamp': new Date().toISOString()
            }
        });
    }

    // PERFORMANCE TRACKING
    trackPerformance(metric, value, label) {
        this.dataLayer.push({
            'event': 'performance_metric',
            'event_category': 'Performance',
            'event_action': metric,
            'event_label': label,
            'custom_parameters': {
                'metric_name': metric,
                'metric_value': value,
                'metric_unit': 'ms',
                'timestamp': new Date().toISOString()
            }
        });
    }

    trackApiResponse(endpoint, responseTime, success) {
        this.dataLayer.push({
            'event': 'api_response',
            'event_category': 'API Performance',
            'event_action': success ? 'Success' : 'Error',
            'event_label': endpoint,
            'custom_parameters': {
                'endpoint': endpoint,
                'response_time_ms': responseTime,
                'success': success,
                'timestamp': new Date().toISOString()
            }
        });
    }

    // ERROR TRACKING
    trackError(error, context) {
        this.dataLayer.push({
            'event': 'error',
            'event_category': 'Error',
            'event_action': error.name || 'Unknown Error',
            'event_label': error.message || 'No message',
            'custom_parameters': {
                'error_message': error.message,
                'error_stack': error.stack,
                'error_context': context,
                'timestamp': new Date().toISOString(),
                'user_agent': navigator.userAgent
            }
        });
    }

    // CONVERSION TRACKING
    trackConversion(type, value, currency = 'USD') {
        this.dataLayer.push({
            'event': 'conversion',
            'event_category': 'Conversion',
            'event_action': type,
            'event_label': `${currency} ${value}`,
            'custom_parameters': {
                'conversion_type': type,
                'conversion_value': value,
                'currency': currency,
                'timestamp': new Date().toISOString()
            }
        });
    }

    // CUSTOM EVENT TRACKING
    trackCustomEvent(eventName, category, action, label, parameters = {}) {
        this.dataLayer.push({
            'event': eventName,
            'event_category': category,
            'event_action': action,
            'event_label': label,
            'custom_parameters': {
                ...parameters,
                'timestamp': new Date().toISOString()
            }
        });
    }

    // UTILITY METHODS
    setUserProperties(properties) {
        this.dataLayer.push({
            'event': 'user_properties',
            'user_properties': {
                ...properties,
                'timestamp': new Date().toISOString()
            }
        });
    }

    setSessionProperties(properties) {
        this.dataLayer.push({
            'event': 'session_properties',
            'session_properties': {
                ...properties,
                'session_start': new Date().toISOString()
            }
        });
    }
}

// Create singleton instance
const analytics = new AnalyticsService();

export default analytics;

// Convenience methods for common tracking
export const trackOutfitGeneration = (data) => analytics.trackOutfitGeneration(data);
export const trackProductClick = (product) => analytics.trackProductClick(product);
export const trackThemeSelection = (theme) => analytics.trackThemeSelection(theme);
export const trackPageView = (page) => analytics.trackPageView(page);
export const trackError = (error, context) => analytics.trackError(error, context);
export const trackPerformance = (metric, value, label) => analytics.trackPerformance(metric, value, label); 
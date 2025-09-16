/**
 * Elevate.AI - Main JavaScript
 * Handles common functionality across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation active state
    initNavigation();
    
    // Initialize file upload previews
    initFileUploads();
    
    // Initialize modals
    initModals();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize mobile menu toggle
    initMobileMenu();
    
    // Initialize animations
    initAnimations();
});

/**
 * Sets the active state on navigation based on current URL
 */
function initNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // Check if the current path starts with the link href
        // This handles both exact matches and sub-paths
        if (currentPath === href || 
            (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

/**
 * Initializes file upload previews and feedback
 */
function initFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const container = input.closest('.file-upload');
        if (!container) return;
        
        const preview = container.querySelector('.file-preview') || document.createElement('div');
        if (!preview.classList.contains('file-preview')) {
            preview.classList.add('file-preview');
            container.appendChild(preview);
        }
        
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Update preview text
            preview.innerHTML = `
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            `;
            
            // Show preview
            preview.style.display = 'block';
            
            // Update container style
            container.classList.add('has-file');
        });
    });
}

/**
 * Formats file size in bytes to human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initializes modal functionality
 */
function initModals() {
    // Modal open buttons
    const modalOpenButtons = document.querySelectorAll('[data-modal]');
    
    modalOpenButtons.forEach(button => {
        const modalId = button.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        
        if (!modal) return;
        
        button.addEventListener('click', function() {
            openModal(modalId);
        });
    });
    
    // Modal close buttons
    const modalCloseButtons = document.querySelectorAll('.modal-close, [data-close-modal]');
    
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = button.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal when clicking outside content
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
}

/**
 * Opens a modal by ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = 'block';
    document.body.classList.add('modal-open');
    
    // Trigger custom event
    modal.dispatchEvent(new CustomEvent('modal:open'));
}

/**
 * Closes a modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    
    // Trigger custom event
    modal.dispatchEvent(new CustomEvent('modal:close'));
}

/**
 * Initializes tooltips
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.classList.add('tooltip');
        tooltip.textContent = tooltipText;
        
        // Add tooltip to element
        element.appendChild(tooltip);
        
        // Show/hide tooltip on hover
        element.addEventListener('mouseenter', function() {
            tooltip.classList.add('show');
        });
        
        element.addEventListener('mouseleave', function() {
            tooltip.classList.remove('show');
        });
    });
}

/**
 * Initializes mobile menu functionality
 */
function initMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            document.body.classList.toggle('menu-open');
            
            // Toggle aria-expanded attribute
            const isExpanded = mainNav.classList.contains('active');
            menuToggle.setAttribute('aria-expanded', isExpanded);
            
            // Toggle menu icon
            const spans = menuToggle.querySelectorAll('span');
            spans.forEach(span => span.classList.toggle('active'));
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mainNav.contains(event.target) && !menuToggle.contains(event.target) && mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
                document.body.classList.remove('menu-open');
                menuToggle.setAttribute('aria-expanded', false);
                
                const spans = menuToggle.querySelectorAll('span');
                spans.forEach(span => span.classList.remove('active'));
            }
        });
    }
}

/**
 * Initializes animations for elements
 */
function initAnimations() {
    // Animate elements when they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(element => {
            observer.observe(element);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedElements.forEach(element => {
            element.classList.add('animated');
        });
    }
    
    // Add animation classes to elements on page load
    document.querySelectorAll('.card, .btn, .section-title').forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
        element.classList.add('fade-in');
    });
}

/**
 * Shows an alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, warning, danger, info)
 * @param {string} containerId - The ID of the container to append the alert to
 * @param {number} duration - Duration in milliseconds before auto-hiding (0 for no auto-hide)
 */
function showAlert(message, type = 'info', containerId = 'alert-container', duration = 5000) {
    // Get or create alert container
    let container = document.getElementById(containerId);
    
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'alert-container';
        document.body.appendChild(container);
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div class="alert-content">${message}</div>
        <button class="alert-close">&times;</button>
    `;
    
    // Add alert to container
    container.appendChild(alert);
    
    // Add close button functionality
    const closeButton = alert.querySelector('.alert-close');
    closeButton.addEventListener('click', function() {
        container.removeChild(alert);
    });
    
    // Auto-hide alert after duration (if specified)
    if (duration > 0) {
        setTimeout(function() {
            if (container.contains(alert)) {
                container.removeChild(alert);
            }
        }, duration);
    }
    
    return alert;
}

/**
 * Handles form submission with file uploads
 * @param {HTMLFormElement} form - The form element
 * @param {string} url - The URL to submit to
 * @param {Function} successCallback - Function to call on success
 * @param {Function} errorCallback - Function to call on error
 */
function submitFormWithFiles(form, url, successCallback, errorCallback) {
    // Prevent default form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create FormData object
        const formData = new FormData(form);
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-small"></span> Processing...';
        
        // Send request
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Reset button
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            
            // Call success callback
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => {
            // Reset button
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            
            // Call error callback
            if (typeof errorCallback === 'function') {
                errorCallback(error);
            } else {
                console.error('Error:', error);
                showAlert('An error occurred. Please try again.', 'danger');
            }
        });
    });
}

/**
 * Formats a date string to a readable format
 * @param {string} dateStr - The date string to format
 * @param {Object} options - Formatting options for toLocaleDateString
 * @returns {string} Formatted date string
 */
function formatDate(dateStr, options = { weekday: 'short', month: 'short', day: 'numeric' }) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', options);
}

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The debounce wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Creates a simple chart in a container
 * @param {string} containerId - The ID of the container element
 * @param {Array} data - Array of data points with x and y values
 * @param {Object} options - Chart options
 */
function createSimpleChart(containerId, data, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Default options
    const defaultOptions = {
        height: 250,
        barWidth: 30,
        barColor: '#4a6bff',
        showTooltips: true,
        xLabel: '',
        yLabel: ''
    };
    
    // Merge options
    const chartOptions = { ...defaultOptions, ...options };
    
    // Create chart container
    const chartContainer = document.createElement('div');
    chartContainer.className = 'simple-chart';
    chartContainer.style.height = `${chartOptions.height}px`;
    
    // Find max value for scaling
    const maxValue = Math.max(...data.map(item => item.y));
    
    // Create bars
    data.forEach(item => {
        const barHeight = (item.y / maxValue) * chartOptions.height;
        
        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.style.height = `${barHeight}px`;
        bar.style.width = `${chartOptions.barWidth}px`;
        bar.style.backgroundColor = chartOptions.barColor;
        
        if (chartOptions.showTooltips) {
            const tooltip = document.createElement('div');
            tooltip.className = 'chart-tooltip';
            tooltip.textContent = `${item.x}: ${item.y}`;
            bar.appendChild(tooltip);
        }
        
        chartContainer.appendChild(bar);
    });
    
    // Add chart to container
    container.appendChild(chartContainer);
    
    // Add labels if provided
    if (chartOptions.xLabel || chartOptions.yLabel) {
        const labelsContainer = document.createElement('div');
        labelsContainer.className = 'chart-labels';
        
        if (chartOptions.xLabel) {
            const xLabel = document.createElement('div');
            xLabel.className = 'chart-x-label';
            xLabel.textContent = chartOptions.xLabel;
            labelsContainer.appendChild(xLabel);
        }
        
        if (chartOptions.yLabel) {
            const yLabel = document.createElement('div');
            yLabel.className = 'chart-y-label';
            yLabel.textContent = chartOptions.yLabel;
            labelsContainer.appendChild(yLabel);
        }
        
        container.appendChild(labelsContainer);
    }
    
    return chartContainer;
}
/**
 * Dashboard JavaScript for BlogAuto AI
 * Handles dashboard statistics and article management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard charts if element exists
    const statsChart = document.getElementById('statsChart');
    if (statsChart) {
        initializeStatsChart();
    }

    // Setup article filtering for article list
    setupArticleFilters();

    // Setup auto-refresh for dashboard stats
    setupStatsAutoRefresh();

    // Setup article actions (delete, export)
    setupArticleActions();
});

/**
 * Initialize the statistics chart
 */
function initializeStatsChart() {
    const ctx = document.getElementById('statsChart').getContext('2d');
    
    // Get stats data from the page
    const statsElements = document.querySelectorAll('.stats-count');
    const labels = [];
    const data = [];
    const backgroundColors = [];
    
    statsElements.forEach(el => {
        const status = el.dataset.status;
        const count = parseInt(el.textContent);
        
        if (status && count > 0) {
            labels.push(status.charAt(0).toUpperCase() + status.slice(1));
            data.push(count);
            
            // Set colors based on status
            switch(status) {
                case 'draft':
                    backgroundColors.push('#6b7280');
                    break;
                case 'scheduled':
                    backgroundColors.push('#f59e0b');
                    break;
                case 'published':
                    backgroundColors.push('#10b981');
                    break;
                case 'failed':
                    backgroundColors.push('#ef4444');
                    break;
                default:
                    backgroundColors.push('#4a6cf7');
            }
        }
    });
    
    // Create the chart
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * Set up auto-refresh for dashboard statistics
 */
function setupStatsAutoRefresh() {
    // Only set up refresh on dashboard page
    if (!document.getElementById('dashboardStats')) return;
    
    // Refresh stats every 30 seconds
    setInterval(refreshDashboardStats, 30000);
}

/**
 * Refresh dashboard statistics via AJAX
 */
function refreshDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            // Update article counts
            updateStatCount('total', data.stats.total);
            updateStatCount('draft', data.stats.draft);
            updateStatCount('scheduled', data.stats.scheduled);
            updateStatCount('published', data.stats.published);
            updateStatCount('failed', data.stats.failed);
            
            // Update scheduler status
            const schedulerStatus = document.getElementById('schedulerStatus');
            if (schedulerStatus) {
                schedulerStatus.textContent = data.scheduler.status;
                schedulerStatus.className = data.scheduler.status === 'running' 
                    ? 'badge bg-success' 
                    : 'badge bg-danger';
            }
            
            const nextRun = document.getElementById('nextSchedulerRun');
            if (nextRun) {
                nextRun.textContent = data.scheduler.next_run || 'Not scheduled';
            }
        })
        .catch(error => console.error('Error refreshing stats:', error));
}

/**
 * Update a statistic count element
 * @param {string} status - The status type (total, draft, etc.)
 * @param {number} count - The new count value
 */
function updateStatCount(status, count) {
    const element = document.querySelector(`.stats-count[data-status="${status}"]`);
    if (element) {
        // Animate the count change
        const currentCount = parseInt(element.textContent);
        if (currentCount !== count) {
            animateCountChange(element, currentCount, count);
        }
    }
}

/**
 * Animate a count change
 * @param {Element} element - The element to update
 * @param {number} start - The starting count
 * @param {number} end - The ending count
 */
function animateCountChange(element, start, end) {
    const duration = 1000; // 1 second
    const stepTime = 50; // Update every 50ms
    const steps = duration / stepTime;
    const increment = (end - start) / steps;
    let currentCount = start;
    let step = 0;
    
    const interval = setInterval(() => {
        step++;
        currentCount += increment;
        
        if (step >= steps) {
            clearInterval(interval);
            element.textContent = end;
        } else {
            element.textContent = Math.round(currentCount);
        }
    }, stepTime);
}

/**
 * Set up filters for the article list
 */
function setupArticleFilters() {
    const filterForm = document.getElementById('articleFilters');
    if (!filterForm) return;
    
    // Submit form when select filters change
    const selectFilters = filterForm.querySelectorAll('select');
    selectFilters.forEach(select => {
        select.addEventListener('change', () => {
            filterForm.submit();
        });
    });
    
    // Submit form when search button is clicked
    const searchButton = filterForm.querySelector('button[type="submit"]');
    if (searchButton) {
        searchButton.addEventListener('click', (e) => {
            e.preventDefault();
            filterForm.submit();
        });
    }
    
    // Clear filters
    const clearButton = document.getElementById('clearFilters');
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            const inputs = filterForm.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'text') {
                    input.value = '';
                } else if (input.type === 'select-one') {
                    input.selectedIndex = 0;
                }
            });
            filterForm.submit();
        });
    }
}

/**
 * Set up article actions (delete, export)
 */
function setupArticleActions() {
    // Delete article buttons
    const deleteButtons = document.querySelectorAll('.delete-article');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.dataset.articleId;
            const articleTitle = this.dataset.articleTitle;
            
            confirmAction(
                `Are you sure you want to delete the article "${articleTitle}"? This action cannot be undone.`,
                () => deleteArticle(articleId),
                'Delete',
                'btn-danger'
            );
        });
    });
    
    // Export article buttons
    const exportButtons = document.querySelectorAll('.export-article');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.dataset.articleId;
            const format = this.dataset.format;
            
            window.location.href = `/api/export-article/${articleId}/${format}`;
        });
    });
}

/**
 * Delete an article
 * @param {string} articleId - The ID of the article to delete
 */
function deleteArticle(articleId) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/article/${articleId}/delete`;
    
    // Add CSRF token if needed
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
    }
    
    document.body.appendChild(form);
    form.submit();
}

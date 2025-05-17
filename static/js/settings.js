/**
 * Settings JavaScript for BlogAuto AI
 * Handles WordPress and API key configuration
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up WordPress configuration tests
    setupWordPressTests();
    
    // Set up API key tests
    setupApiKeyTests();
    
    // Set up configuration modals
    setupConfigModals();
});

/**
 * Set up WordPress connection tests
 */
function setupWordPressTests() {
    const testButtons = document.querySelectorAll('.test-wordpress');
    if (!testButtons.length) return;
    
    testButtons.forEach(button => {
        button.addEventListener('click', function() {
            const configId = this.dataset.configId;
            
            // If testing existing config
            if (configId) {
                testWordPressConnection({ config_id: configId });
                return;
            }
            
            // If testing new config
            const form = document.getElementById('addWordPressForm');
            if (!form) return;
            
            const siteUrl = form.querySelector('[name="site_url"]').value;
            const username = form.querySelector('[name="username"]').value;
            const appPassword = form.querySelector('[name="app_password"]').value;
            
            if (!siteUrl || !username || !appPassword) {
                showToast('Please fill in all fields before testing the connection.', 'warning');
                return;
            }
            
            testWordPressConnection({
                site_url: siteUrl,
                username: username,
                app_password: appPassword
            });
        });
    });
}

/**
 * Test WordPress connection
 * @param {Object} data - Connection data (either config_id or connection details)
 */
function testWordPressConnection(data) {
    // Get the button that was clicked
    const btn = document.querySelector(`.test-wordpress${data.config_id ? `[data-config-id="${data.config_id}"]` : ''}`);
    if (!btn) return;
    
    // Show loading state
    const originalBtnText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...';
    btn.disabled = true;
    
    // Send AJAX request to test connection
    fetch('/api/test-wordpress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        // Restore button
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
        
        // Show result
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error testing WordPress connection:', error);
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
        showToast('Error testing connection. Please try again.', 'danger');
    });
}

/**
 * Set up API key tests
 */
function setupApiKeyTests() {
    const testButtons = document.querySelectorAll('.test-api-key');
    if (!testButtons.length) return;
    
    testButtons.forEach(button => {
        button.addEventListener('click', function() {
            const apiType = this.dataset.apiType;
            const input = document.querySelector(`input[name="${apiType}_key"]`);
            
            if (!input || !input.value) {
                showToast('Please enter an API key to test.', 'warning');
                return;
            }
            
            testApiKey(apiType, input.value, this);
        });
    });
}

/**
 * Test an API key
 * @param {string} apiType - The type of API (gpt, claude, unsplash)
 * @param {string} apiKey - The API key to test
 * @param {Element} button - The button that was clicked
 */
function testApiKey(apiType, apiKey, button) {
    // Show loading state
    const originalBtnText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...';
    button.disabled = true;
    
    // Send AJAX request to test API key
    fetch('/api/test-api-key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            api_type: apiType,
            api_key: apiKey
        })
    })
    .then(response => response.json())
    .then(data => {
        // Restore button
        button.innerHTML = originalBtnText;
        button.disabled = false;
        
        // Show result
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error testing API key:', error);
        button.innerHTML = originalBtnText;
        button.disabled = false;
        showToast('Error testing API key. Please try again.', 'danger');
    });
}

/**
 * Set up configuration modals
 */
function setupConfigModals() {
    // Edit WordPress configuration
    const editBtns = document.querySelectorAll('.edit-wordpress-config');
    if (editBtns.length) {
        editBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const configId = this.dataset.configId;
                const name = this.dataset.name;
                const siteUrl = this.dataset.siteUrl;
                const username = this.dataset.username;
                const isDefault = this.dataset.isDefault === 'true';
                
                // Populate edit form
                const form = document.getElementById('editWordPressForm');
                if (!form) return;
                
                form.querySelector('[name="config_id"]').value = configId;
                form.querySelector('[name="name"]').value = name;
                form.querySelector('[name="site_url"]').value = siteUrl;
                form.querySelector('[name="username"]').value = username;
                form.querySelector('[name="is_default"]').checked = isDefault;
                
                // Clear password field
                form.querySelector('[name="app_password"]').value = '';
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editWordPressModal'));
                modal.show();
            });
        });
    }
    
    // Delete WordPress configuration
    const deleteBtns = document.querySelectorAll('.delete-wordpress-config');
    if (deleteBtns.length) {
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const configId = this.dataset.configId;
                const name = this.dataset.name;
                
                confirmAction(
                    `Are you sure you want to delete the "${name}" WordPress configuration? This action cannot be undone.`,
                    () => deleteWordPressConfig(configId),
                    'Delete',
                    'btn-danger'
                );
            });
        });
    }
    
    // Delete API key
    const deleteApiKeyBtns = document.querySelectorAll('.delete-api-key');
    if (deleteApiKeyBtns.length) {
        deleteApiKeyBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const apiType = this.dataset.apiType;
                
                confirmAction(
                    `Are you sure you want to delete your ${apiType.toUpperCase()} API key? You will need to add it again to use this service.`,
                    () => deleteApiKey(apiType),
                    'Delete',
                    'btn-danger'
                );
            });
        });
    }
}

/**
 * Delete a WordPress configuration
 * @param {string} configId - The ID of the configuration to delete
 */
function deleteWordPressConfig(configId) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/settings/wordpress';
    
    // Add necessary inputs
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = 'delete';
    form.appendChild(actionInput);
    
    const configIdInput = document.createElement('input');
    configIdInput.type = 'hidden';
    configIdInput.name = 'config_id';
    configIdInput.value = configId;
    form.appendChild(configIdInput);
    
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

/**
 * Delete an API key
 * @param {string} apiType - The type of API key to delete
 */
function deleteApiKey(apiType) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/settings/api-keys/delete/${apiType}`;
    
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

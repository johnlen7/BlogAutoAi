/**
 * Editor JavaScript for BlogAuto AI
 * Handles article creation and editing functionality
 */

let quillEditor;
let generatingContent = false;
let wordpressCategories = [];

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Quill editor if element exists
    const editorContainer = document.getElementById('editor');
    if (editorContainer) {
        initializeQuillEditor();
    }

    // Set up event listeners for content generation
    setupGenerationListeners();

    // Set up event listeners for article saving and publishing
    setupArticleActionListeners();
    
    // Load WordPress categories if the category selector exists
    if (document.getElementById('categorySelector')) {
        loadWordPressCategories();
    }
});

/**
 * Initialize the Quill rich text editor
 */
function initializeQuillEditor() {
    const toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ 'header': 1 }, { 'header': 2 }],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        [{ 'script': 'sub' }, { 'script': 'super' }],
        [{ 'indent': '-1' }, { 'indent': '+1' }],
        [{ 'direction': 'rtl' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'font': [] }],
        [{ 'align': [] }],
        ['clean'],
        ['link', 'image']
    ];

    quillEditor = new Quill('#editor', {
        modules: {
            toolbar: toolbarOptions
        },
        placeholder: 'Write or generate your article content here...',
        theme: 'snow'
    });

    // If we're editing an existing article, load content
    const existingContent = document.getElementById('existingContent');
    if (existingContent && existingContent.value) {
        quillEditor.root.innerHTML = existingContent.value;
    }

    // Update hidden input when editor content changes
    quillEditor.on('text-change', function() {
        document.getElementById('articleContent').value = quillEditor.root.innerHTML;
    });
}

/**
 * Set up event listeners for content generation
 */
function setupGenerationListeners() {
    const generateBtn = document.getElementById('generateContent');
    if (!generateBtn) return;

    generateBtn.addEventListener('click', function() {
        if (generatingContent) return; // Prevent multiple clicks

        const contentType = document.getElementById('contentType').value;
        const contentValue = document.getElementById('contentValue').value;
        const aiModel = document.querySelector('input[name="aiModel"]:checked').value;

        if (!contentValue) {
            showToast(`Please enter a ${contentType} to generate content.`, 'warning');
            return;
        }

        generateArticleContent(contentType, contentValue, aiModel);
    });
}

/**
 * Generate article content using AI
 * @param {string} type - The type of content to generate (keyword or url)
 * @param {string} value - The keyword or URL value
 * @param {string} model - The AI model to use (claude or gpt)
 */
function generateArticleContent(type, value, model) {
    // Mostrar confirmação usando SweetAlert2 antes de gerar
    const confirmMsg = document.documentElement.lang === 'en' ? 
        `Generate content using ${model.toUpperCase()} from ${type}: "${value}"?` : 
        `Gerar conteúdo usando ${model.toUpperCase()} a partir de ${type === 'keyword' ? 'palavra-chave' : 'URL'}: "${value}"?`;
    
    Swal.fire({
        title: document.documentElement.lang === 'en' ? 'Confirm Generation' : 'Confirmar Geração',
        text: confirmMsg,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#6c757d',
        confirmButtonText: document.documentElement.lang === 'en' ? 'Yes, generate' : 'Sim, gerar',
        cancelButtonText: document.documentElement.lang === 'en' ? 'Cancel' : 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Mostrar animação de geração
            Swal.fire({
                title: document.documentElement.lang === 'en' ? 'Generating Content' : 'Gerando Conteúdo',
                html: document.documentElement.lang === 'en' ? 
                    `Creating article with ${model.toUpperCase()}...<br>This may take up to 2 minutes` : 
                    `Criando artigo com ${model.toUpperCase()}...<br>Isso pode levar até 2 minutos`,
                timerProgressBar: true,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Update state
            generatingContent = true;
            const generateBtn = document.getElementById('generateContent');
            generateBtn.disabled = true;

            // Request data
            const requestData = {
                type: type,
                value: value,
                model: model
            };

            // Send AJAX request to generate content
            fetch('/api/generate-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
    .then(response => response.json())
    .then(data => {
        // Close SweetAlert loading
        Swal.close();
        
        // Reset button state
        const generateBtn = document.getElementById('generateContent');
        if (generateBtn) {
            generateBtn.disabled = false;
        }
        generatingContent = false;

        if (data.success) {
            // Mostrar mensagem de sucesso
            Swal.fire({
                icon: 'success',
                title: document.documentElement.lang === 'en' ? 'Success!' : 'Sucesso!',
                text: document.documentElement.lang === 'en' ? 'Content successfully generated!' : 'Conteúdo gerado com sucesso!',
                confirmButtonText: 'OK'
            });
            
            // Populate form fields with generated content
            populateArticleForm(data.content);
        } else {
            Swal.fire({
                icon: 'error',
                title: document.documentElement.lang === 'en' ? 'Error' : 'Erro',
                text: data.message || (document.documentElement.lang === 'en' ? 
                    'Error generating content. Please try again.' : 
                    'Erro ao gerar conteúdo. Por favor, tente novamente.'),
                confirmButtonText: 'OK'
            });
        }
    })
    .catch(error => {
        console.error('Error generating content:', error);
        Swal.close();
        
        // Reset button state
        const generateBtn = document.getElementById('generateContent');
        if (generateBtn) {
            generateBtn.disabled = false;
        }
        generatingContent = false;
        
        Swal.fire({
            icon: 'error',
            title: document.documentElement.lang === 'en' ? 'Error' : 'Erro',
            text: document.documentElement.lang === 'en' ? 
                'Error connecting to AI service. Please verify your API keys and try again.' : 
                'Erro ao conectar ao serviço de IA. Verifique suas chaves de API e tente novamente.',
            confirmButtonText: 'OK'
        });
    });
}

/**
 * Populate the article form with generated content
 * @param {Object} content - The generated content object
 */
function populateArticleForm(content) {
    // Populate title
    document.getElementById('articleTitle').value = content.title;

    // Populate content in editor
    if (quillEditor) {
        quillEditor.root.innerHTML = content.content;
        document.getElementById('articleContent').value = content.content;
    }

    // Populate meta description
    document.getElementById('metaDescription').value = content.meta_description;

    // Populate slug
    document.getElementById('articleSlug').value = content.slug;

    // Populate tags
    document.getElementById('articleTags').value = content.tags.join(', ');

    // Show the editor form that was hidden
    const generationSection = document.getElementById('generationSection');
    const editorSection = document.getElementById('editorSection');
    
    if (generationSection && editorSection) {
        generationSection.classList.add('d-none');
        editorSection.classList.remove('d-none');
    }
}

/**
 * Set up event listeners for article actions (save, publish, schedule)
 */
function setupArticleActionListeners() {
    // Save article as draft
    const saveBtn = document.getElementById('saveArticle');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveArticle('draft');
        });
    }

    // Publish article immediately
    const publishBtn = document.getElementById('publishArticle');
    if (publishBtn) {
        publishBtn.addEventListener('click', function() {
            if (document.getElementById('articleId').value) {
                // If article already exists, confirm and publish
                confirmAction(
                    'Are you sure you want to publish this article immediately?',
                    function() { publishExistingArticle(); },
                    'Publish',
                    'btn-success'
                );
            } else {
                // If new article, save first then publish
                saveArticle('publish');
            }
        });
    }

    // Schedule article for later
    const scheduleBtn = document.getElementById('scheduleArticle');
    if (scheduleBtn) {
        scheduleBtn.addEventListener('click', function() {
            showScheduleModal();
        });
    }

    // Handle schedule form submission
    const scheduleForm = document.getElementById('scheduleForm');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            scheduleArticle();
        });
    }
}

/**
 * Save article as draft or for publishing
 * @param {string} nextAction - The next action after saving (draft, publish)
 */
function saveArticle(nextAction = 'draft') {
    // Validate form
    if (!validateArticleForm()) return;

    // Get form data
    const articleData = getArticleFormData();

    // Show loading state
    const saveBtn = document.getElementById('saveArticle');
    const originalBtnText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    saveBtn.disabled = true;

    // Send AJAX request to save article
    fetch('/api/save-article', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(articleData)
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        saveBtn.innerHTML = originalBtnText;
        saveBtn.disabled = false;

        if (data.success) {
            // Update article ID if new article
            if (data.article_id) {
                document.getElementById('articleId').value = data.article_id;
            }

            showToast(data.message, 'success');

            // Perform next action
            if (nextAction === 'publish') {
                publishExistingArticle();
            } else if (nextAction === 'schedule') {
                showScheduleModal();
            } else if (!document.getElementById('editMode').value) {
                // Redirect to dashboard after short delay for new article save
                setTimeout(() => {
                    window.location.href = '/articles';
                }, 1500);
            }
        } else {
            showToast(data.message || 'Error saving article. Please try again.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving article:', error);
        saveBtn.innerHTML = originalBtnText;
        saveBtn.disabled = false;
        showToast('Error saving article. Please try again.', 'danger');
    });
}

/**
 * Publish an existing article immediately
 */
function publishExistingArticle() {
    const articleId = document.getElementById('articleId').value;
    if (!articleId) {
        showToast('Article must be saved before publishing.', 'warning');
        return;
    }

    // Mostrar confirmação usando SweetAlert2 antes de publicar
    Swal.fire({
        title: document.documentElement.lang === 'en' ? 'Confirm Publication' : 'Confirmar publicação',
        text: document.documentElement.lang === 'en' ? "Are you sure you want to publish this article immediately?" : "Tem certeza que deseja publicar este artigo imediatamente?",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: document.documentElement.lang === 'en' ? 'Yes, publish now' : 'Sim, publicar agora',
        cancelButtonText: document.documentElement.lang === 'en' ? 'Cancel' : 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Mostrar animação de carregamento
            if (window.loadingAnimations) {
                const message = document.documentElement.lang === 'en' ? 'Publishing article in WordPress...' : 'Publicando artigo no WordPress...';
                window.loadingAnimations.show(message, 'publish');
            } else {
                // Fallback para loaders simples se loadingAnimations não estiver disponível
                const publishBtn = document.getElementById('publishArticle');
                const originalBtnText = publishBtn.innerHTML;
                publishBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Publishing...';
                publishBtn.disabled = true;
            }

            // Send AJAX request to publish article
            fetch('/api/publish-article', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    article_id: articleId
                })
            })
    .then(response => response.json())
    .then(data => {
        // Fechar a animação de carregamento
        if (window.loadingAnimations) {
            window.loadingAnimations.hide();
        } else {
            // Reset button state para fallback
            const publishBtn = document.getElementById('publishArticle');
            const originalBtnText = publishBtn ? publishBtn.innerHTML : 'Publish Now';
            if (publishBtn) {
                publishBtn.innerHTML = originalBtnText;
                publishBtn.disabled = false;
            }
        }

        if (data.success) {
            showToast(data.message, 'success');
            
            // Redirect to article list after short delay
            setTimeout(() => {
                window.location.href = '/articles';
            }, 1500);
        } else {
            showToast(data.message || 'Error publishing article. Please try again.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error publishing article:', error);
        // Fechar a animação de carregamento em caso de erro
        if (window.loadingAnimations) {
            window.loadingAnimations.hide();
        } else {
            // Reset button state para fallback
            const publishBtn = document.getElementById('publishArticle');
            const originalBtnText = publishBtn ? publishBtn.innerHTML : 'Publish Now';
            if (publishBtn) {
                publishBtn.innerHTML = originalBtnText;
                publishBtn.disabled = false;
            }
        }
        showToast('Error publishing article. Please try again.', 'danger');
    });
}

/**
 * Show the schedule modal
 */
function showScheduleModal() {
    const articleId = document.getElementById('articleId').value;
    if (!articleId) {
        showToast('Article must be saved before scheduling.', 'warning');
        saveArticle('schedule');
        return;
    }

    // Set the article ID in the schedule form
    document.getElementById('scheduleArticleId').value = articleId;

    // Set the default scheduled date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    
    const scheduleDate = document.getElementById('scheduleDate');
    const year = tomorrow.getFullYear();
    const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const day = String(tomorrow.getDate()).padStart(2, '0');
    scheduleDate.value = `${year}-${month}-${day}`;

    const scheduleTime = document.getElementById('scheduleTime');
    const hours = String(tomorrow.getHours()).padStart(2, '0');
    const minutes = String(tomorrow.getMinutes()).padStart(2, '0');
    scheduleTime.value = `${hours}:${minutes}`;

    // Show the modal
    const scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    scheduleModal.show();
}

/**
 * Schedule an article for future publishing
 */
function scheduleArticle() {
    const articleId = document.getElementById('scheduleArticleId').value;
    const scheduleDate = document.getElementById('scheduleDate').value;
    const scheduleTime = document.getElementById('scheduleTime').value;
    const repeatSchedule = document.getElementById('repeatSchedule').value;

    if (!articleId || !scheduleDate || !scheduleTime) {
        showToast('Please fill all required fields.', 'warning');
        return;
    }

    // Create datetime in ISO format
    const scheduledDateTime = new Date(`${scheduleDate}T${scheduleTime}`);
    const isoDateTime = scheduledDateTime.toISOString();

    // Show loading state
    const submitBtn = document.querySelector('#scheduleForm button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scheduling...';
    submitBtn.disabled = true;

    // Send AJAX request to schedule article
    fetch('/api/schedule-article', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            article_id: articleId,
            scheduled_date: isoDateTime,
            repeat_schedule: repeatSchedule
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;

        if (data.success) {
            // Hide the modal
            const scheduleModal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
            scheduleModal.hide();

            showToast(data.message, 'success');
            
            // Redirect to article list after short delay
            setTimeout(() => {
                window.location.href = '/articles';
            }, 1500);
        } else {
            showToast(data.message || 'Error scheduling article. Please try again.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error scheduling article:', error);
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
        showToast('Error scheduling article. Please try again.', 'danger');
    });
}

/**
 * Validate the article form
 * @returns {boolean} Whether the form is valid
 */
function validateArticleForm() {
    const title = document.getElementById('articleTitle').value;
    const content = document.getElementById('articleContent').value;
    const wordpressConfig = document.getElementById('wordpressConfig').value;

    if (!title) {
        showToast('Please enter a title for your article.', 'warning');
        return false;
    }

    if (!content) {
        showToast('Article content cannot be empty.', 'warning');
        return false;
    }

    if (!wordpressConfig) {
        showToast('Please select a WordPress configuration.', 'warning');
        return false;
    }

    return true;
}

/**
 * Load WordPress categories from API
 */
function loadWordPressCategories() {
    const wpConfigSelect = document.getElementById('wordpressConfig');
    const configId = wpConfigSelect ? wpConfigSelect.value : '';
    
    // If no WordPress config selected yet, add event listener for when it changes
    if (!configId) {
        if (wpConfigSelect) {
            wpConfigSelect.addEventListener('change', function() {
                loadWordPressCategories();
            });
        }
        return;
    }
    
    // Fetch categories from API
    fetch(`/api/wordpress/categories?config_id=${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                wordpressCategories = data.categories;
                updateCategorySelector();
            } else {
                console.error('Error loading WordPress categories:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching WordPress categories:', error);
        });
}

/**
 * Update the category selector with WordPress categories
 */
function updateCategorySelector() {
    const categorySelector = document.getElementById('categorySelector');
    if (!categorySelector) return;
    
    // Clear existing options (keeping the first one)
    while (categorySelector.options.length > 1) {
        categorySelector.remove(1);
    }
    
    // Add categories as options
    wordpressCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categorySelector.appendChild(option);
    });
    
    // Load existing categories if editing an article
    if (document.getElementById('articleCategories').value) {
        displaySelectedCategories(document.getElementById('articleCategories').value.split(','));
    }
}

/**
 * Add selected category to the list
 */
function addSelectedCategory() {
    const categorySelector = document.getElementById('categorySelector');
    const selectedCategoriesElem = document.getElementById('selectedCategories');
    const articleCategories = document.getElementById('articleCategories');
    
    if (!categorySelector || !selectedCategoriesElem || !articleCategories) return;
    
    const categoryId = categorySelector.value;
    if (!categoryId) return;
    
    const categoryName = categorySelector.options[categorySelector.selectedIndex].text;
    
    // Add only if not already added
    let currentCategories = articleCategories.value ? articleCategories.value.split(',') : [];
    if (!currentCategories.includes(categoryId)) {
        currentCategories.push(categoryId);
        articleCategories.value = currentCategories.join(',');
        
        // Update visual display
        displaySelectedCategories(currentCategories);
    }
}

/**
 * Display selected categories in the UI
 * @param {Array} categoryIds - Array of category IDs
 */
function displaySelectedCategories(categoryIds) {
    const selectedCategoriesElem = document.getElementById('selectedCategories');
    if (!selectedCategoriesElem) return;
    
    selectedCategoriesElem.innerHTML = '';
    
    categoryIds.forEach(categoryId => {
        // Find category name
        const category = wordpressCategories.find(cat => cat.id.toString() === categoryId.toString());
        if (!category) return;
        
        // Create badge element
        const badge = document.createElement('span');
        badge.className = 'badge bg-primary me-1 mb-1';
        badge.textContent = category.name;
        
        // Add remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-close btn-close-white ms-1';
        removeBtn.setAttribute('aria-label', 'Remove');
        removeBtn.style.fontSize = '0.5rem';
        
        removeBtn.addEventListener('click', function() {
            removeCategory(categoryId);
        });
        
        badge.appendChild(removeBtn);
        selectedCategoriesElem.appendChild(badge);
    });
}

/**
 * Remove a category from selected categories
 * @param {string} categoryId - The category ID to remove
 */
function removeCategory(categoryId) {
    const articleCategories = document.getElementById('articleCategories');
    if (!articleCategories) return;
    
    let currentCategories = articleCategories.value ? articleCategories.value.split(',') : [];
    currentCategories = currentCategories.filter(id => id.toString() !== categoryId.toString());
    
    articleCategories.value = currentCategories.join(',');
    displaySelectedCategories(currentCategories);
}

/**
 * Get the article form data as an object
 * @returns {Object} The article form data
 */
function getArticleFormData() {
    return {
        article_id: document.getElementById('articleId').value,
        title: document.getElementById('articleTitle').value,
        content: document.getElementById('articleContent').value,
        meta_description: document.getElementById('metaDescription').value,
        slug: document.getElementById('articleSlug').value,
        tags: document.getElementById('articleTags').value,
        categories: document.getElementById('articleCategories').value,
        featured_image_url: document.getElementById('featuredImageUrl').value,
        keyword: document.getElementById('contentValue').value,
        source_url: document.getElementById('contentType').value === 'url' ? document.getElementById('contentValue').value : '',
        ai_model: document.querySelector('input[name="aiModel"]:checked')?.value,
        wordpress_config_id: document.getElementById('wordpressConfig').value
    };
}

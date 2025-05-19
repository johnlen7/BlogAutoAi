/**
 * Seletor de humor com emojis para definir o tom do conteúdo antes da geração
 */

class MoodSelector {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? 
            document.querySelector(container) : container;
        
        this.options = {
            onChange: () => {},
            defaultMood: 'neutral',
            ...options
        };
        
        this.selectedMood = this.options.defaultMood;
        this.moods = [
            { id: 'formal', emoji: '🧐', label: 'Formal', description: 'Tom profissional e formal' },
            { id: 'friendly', emoji: '😊', label: 'Amigável', description: 'Tom conversacional e acolhedor' },
            { id: 'enthusiastic', emoji: '🤩', label: 'Entusiasmado', description: 'Tom animado e motivador' },
            { id: 'neutral', emoji: '😐', label: 'Neutro', description: 'Tom equilibrado e imparcial' },
            { id: 'humorous', emoji: '😄', label: 'Humorístico', description: 'Tom leve e bem-humorado' },
            { id: 'authoritative', emoji: '🧠', label: 'Especialista', description: 'Tom especializado e detalhado' },
            { id: 'casual', emoji: '👋', label: 'Casual', description: 'Tom informal e descontraído' },
            { id: 'inspirational', emoji: '✨', label: 'Inspirador', description: 'Tom motivacional e inspirador' }
        ];
        
        this.render();
        this.addEventListeners();
    }
    
    render() {
        // Criar elemento container
        this.element = document.createElement('div');
        this.element.className = 'mood-selector';
        
        // Título
        const title = document.createElement('h4');
        title.textContent = 'Tom do conteúdo';
        title.className = 'mood-selector-title';
        
        // Descrição
        const description = document.createElement('p');
        description.textContent = 'Escolha o tom que seu conteúdo deve ter:';
        description.className = 'mood-selector-description';
        
        // Container de moods
        const moodsContainer = document.createElement('div');
        moodsContainer.className = 'moods-container';
        
        // Adicionar cada humor
        this.moods.forEach(mood => {
            const moodElement = document.createElement('div');
            moodElement.className = 'mood-item';
            moodElement.dataset.mood = mood.id;
            
            if (mood.id === this.selectedMood) {
                moodElement.classList.add('selected');
            }
            
            const emoji = document.createElement('div');
            emoji.className = 'mood-emoji';
            emoji.textContent = mood.emoji;
            
            const label = document.createElement('div');
            label.className = 'mood-label';
            label.textContent = mood.label;
            
            moodElement.appendChild(emoji);
            moodElement.appendChild(label);
            
            // Adicionar tooltip de descrição
            moodElement.title = mood.description;
            
            moodsContainer.appendChild(moodElement);
        });
        
        // Feedback visual do humor selecionado
        this.feedbackElement = document.createElement('div');
        this.feedbackElement.className = 'mood-feedback';
        this.updateFeedback();
        
        // Campo oculto para formulário
        this.hiddenInput = document.createElement('input');
        this.hiddenInput.type = 'hidden';
        this.hiddenInput.name = 'content_tone';
        this.hiddenInput.value = this.selectedMood;
        
        // Montar estrutura
        this.element.appendChild(title);
        this.element.appendChild(description);
        this.element.appendChild(moodsContainer);
        this.element.appendChild(this.feedbackElement);
        this.element.appendChild(this.hiddenInput);
        
        // Adicionar estilos
        this.addStyles();
        
        // Adicionar ao container
        this.container.appendChild(this.element);
    }
    
    addEventListeners() {
        // Evento de clique nos itens de humor
        const moodItems = this.element.querySelectorAll('.mood-item');
        
        moodItems.forEach(item => {
            item.addEventListener('click', (event) => {
                // Remover seleção anterior
                moodItems.forEach(m => m.classList.remove('selected'));
                
                // Adicionar nova seleção
                item.classList.add('selected');
                
                // Atualizar valor selecionado
                this.selectedMood = item.dataset.mood;
                this.hiddenInput.value = this.selectedMood;
                
                // Atualizar feedback
                this.updateFeedback();
                
                // Chamar callback
                this.options.onChange(this.selectedMood);
                
                // Animação de seleção
                this.animateSelection(item);
            });
        });
    }
    
    updateFeedback() {
        const selectedMood = this.moods.find(m => m.id === this.selectedMood);
        
        if (selectedMood) {
            this.feedbackElement.innerHTML = `
                <div class="selected-mood">
                    <span class="selected-emoji">${selectedMood.emoji}</span>
                    <span class="selected-text">Seu conteúdo terá um tom <strong>${selectedMood.label.toLowerCase()}</strong></span>
                </div>
                <div class="selected-description">${selectedMood.description}</div>
            `;
        }
    }
    
    animateSelection(element) {
        // Adicionar classe para animação
        element.classList.add('pulse');
        
        // Remover após a animação
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 500);
    }
    
    addStyles() {
        // Verificar se os estilos já foram adicionados
        if (document.getElementById('mood-selector-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'mood-selector-styles';
        
        style.textContent = `
            .mood-selector {
                margin: 20px 0;
                padding: 15px;
                border-radius: 8px;
                background-color: #f8f9fa;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                transition: all 0.3s;
            }
            
            .mood-selector:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            
            .mood-selector-title {
                margin: 0 0 10px 0;
                font-size: 1.1rem;
                color: #333;
            }
            
            .mood-selector-description {
                margin: 0 0 15px 0;
                font-size: 0.9rem;
                color: #666;
            }
            
            .moods-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .mood-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 70px;
                height: 70px;
                border-radius: 8px;
                background-color: white;
                cursor: pointer;
                transition: all 0.2s;
                border: 2px solid transparent;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .mood-item:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .mood-item.selected {
                border-color: #0d6efd;
                background-color: #e6f2ff;
            }
            
            .mood-emoji {
                font-size: 1.8rem;
                margin-bottom: 5px;
            }
            
            .mood-label {
                font-size: 0.8rem;
                text-align: center;
                color: #333;
            }
            
            .mood-feedback {
                padding: 10px;
                border-radius: 6px;
                background-color: white;
                margin-top: 10px;
                transition: all 0.3s;
            }
            
            .selected-mood {
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }
            
            .selected-emoji {
                font-size: 1.5rem;
                margin-right: 10px;
            }
            
            .selected-text {
                font-size: 0.9rem;
            }
            
            .selected-description {
                font-size: 0.8rem;
                color: #666;
                font-style: italic;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .pulse {
                animation: pulse 0.5s ease-in-out;
            }
            
            /* Design responsivo */
            @media (max-width: 768px) {
                .moods-container {
                    justify-content: center;
                }
                
                .mood-item {
                    width: 65px;
                    height: 65px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    getValue() {
        return this.selectedMood;
    }
    
    setValue(moodId) {
        if (this.moods.some(m => m.id === moodId)) {
            this.selectedMood = moodId;
            this.hiddenInput.value = moodId;
            
            // Atualizar seleção visual
            const moodItems = this.element.querySelectorAll('.mood-item');
            moodItems.forEach(item => {
                item.classList.toggle('selected', item.dataset.mood === moodId);
            });
            
            // Atualizar feedback
            this.updateFeedback();
        }
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Procurar o container para o seletor de humor
    const container = document.querySelector('#mood-selector-container');
    
    if (container) {
        // Inicializar componente
        const moodSelector = new MoodSelector(container, {
            onChange: (mood) => {
                console.log('Humor selecionado:', mood);
                
                // Você pode adicionar lógica aqui para atualizar a interface com base no humor
                // Por exemplo, alterar o estilo do editor ou sugestões contextuais
            }
        });
        
        // Disponibilizar globalmente se necessário
        window.moodSelector = moodSelector;
    }
});
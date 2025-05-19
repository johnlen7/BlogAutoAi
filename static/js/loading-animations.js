/**
 * Animações de carregamento com ilustrações temáticas de escritor
 */

class LoadingAnimations {
    constructor() {
        this.animationContainer = null;
        this.overlayElement = null;
        this.addStyles();
    }
    
    /**
     * Mostra a animação de carregamento
     * @param {string} message - Mensagem a ser exibida durante o carregamento
     * @param {string} type - Tipo de animação (generate, publish, schedule)
     */
    show(message = 'Processando...', type = 'generate') {
        // Remover animação existente se houver
        this.hide();
        
        // Criar overlay para bloquear a interface
        this.overlayElement = document.createElement('div');
        this.overlayElement.className = 'loading-overlay';
        document.body.appendChild(this.overlayElement);
        
        // Criar container da animação
        this.animationContainer = document.createElement('div');
        this.animationContainer.className = 'loading-animation';
        
        // Selecionar animação com base no tipo
        let animation = '';
        let title = '';
        
        switch (type) {
            case 'generate':
                title = 'Gerando conteúdo...';
                animation = this.getGenerateAnimation();
                break;
            case 'publish':
                title = 'Publicando artigo...';
                animation = this.getPublishAnimation();
                break;
            case 'schedule':
                title = 'Agendando publicação...';
                animation = this.getScheduleAnimation();
                break;
            default:
                title = 'Processando...';
                animation = this.getDefaultAnimation();
        }
        
        // Construir o conteúdo
        this.animationContainer.innerHTML = `
            <div class="loading-content">
                <h3>${title}</h3>
                <div class="animation-wrapper">
                    ${animation}
                </div>
                <p class="loading-message">${message}</p>
                <div class="loading-progress">
                    <div class="progress-bar"></div>
                </div>
            </div>
        `;
        
        // Adicionar ao corpo do documento
        document.body.appendChild(this.animationContainer);
        
        // Adicionar classe para animação de entrada
        setTimeout(() => {
            this.animationContainer.classList.add('visible');
        }, 10);
        
        // Iniciar animação de progresso
        this.startProgress();
    }
    
    /**
     * Oculta a animação de carregamento
     */
    hide() {
        // Remover elementos existentes
        if (this.animationContainer) {
            this.animationContainer.classList.remove('visible');
            
            // Remover após a transição
            setTimeout(() => {
                if (this.animationContainer && this.animationContainer.parentNode) {
                    this.animationContainer.parentNode.removeChild(this.animationContainer);
                }
                this.animationContainer = null;
            }, 300);
        }
        
        if (this.overlayElement) {
            this.overlayElement.parentNode.removeChild(this.overlayElement);
            this.overlayElement = null;
        }
    }
    
    /**
     * Atualiza a mensagem de carregamento
     * @param {string} message - Nova mensagem
     */
    updateMessage(message) {
        if (this.animationContainer) {
            const messageElement = this.animationContainer.querySelector('.loading-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
    }
    
    /**
     * Inicia a animação da barra de progresso
     */
    startProgress() {
        if (!this.animationContainer) return;
        
        const progressBar = this.animationContainer.querySelector('.progress-bar');
        if (progressBar) {
            // Resetar
            progressBar.style.width = '0%';
            
            // Iniciar animação
            setTimeout(() => {
                progressBar.style.width = '20%';
                
                setTimeout(() => {
                    progressBar.style.width = '60%';
                    
                    setTimeout(() => {
                        progressBar.style.width = '80%';
                        
                        setTimeout(() => {
                            progressBar.style.width = '90%';
                        }, 1000);
                    }, 1000);
                }, 800);
            }, 300);
        }
    }
    
    /**
     * Finaliza a barra de progresso (100%)
     */
    completeProgress() {
        if (!this.animationContainer) return;
        
        const progressBar = this.animationContainer.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '100%';
        }
    }
    
    /**
     * Adiciona estilos CSS ao documento
     */
    addStyles() {
        if (document.getElementById('loading-animations-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'loading-animations-styles';
        
        style.textContent = `
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 9998;
            }
            
            .loading-animation {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(0.9);
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                text-align: center;
                z-index: 9999;
                max-width: 400px;
                width: 100%;
                opacity: 0;
                transition: all 0.3s ease;
            }
            
            .loading-animation.visible {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
            
            .loading-content h3 {
                margin-top: 0;
                color: #333;
                font-size: 1.5rem;
                margin-bottom: 20px;
            }
            
            .animation-wrapper {
                height: 200px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .loading-message {
                color: #666;
                margin-bottom: 15px;
                font-size: 1rem;
            }
            
            .loading-progress {
                height: 6px;
                background-color: #f0f0f0;
                border-radius: 3px;
                overflow: hidden;
                margin-top: 20px;
            }
            
            .progress-bar {
                height: 100%;
                background-color: #0d6efd;
                width: 0;
                transition: width 0.5s ease;
            }
            
            /* SVG Animations */
            .writer-svg {
                max-width: 100%;
                height: auto;
            }
            
            .writer-svg .animate-pen {
                animation: movePen 3s infinite ease-in-out;
            }
            
            .writer-svg .animate-paper {
                animation: paperWave 5s infinite ease-in-out;
            }
            
            .writer-svg .animate-face {
                animation: blink 4s infinite;
            }
            
            .writer-svg .animate-calendar {
                animation: flipPage 2s infinite ease-in-out;
            }
            
            .writer-svg .animate-wordpress {
                animation: spin 3s infinite linear;
            }
            
            @keyframes movePen {
                0% { transform: translate(0, 0) rotate(0deg); }
                25% { transform: translate(5px, 2px) rotate(2deg); }
                50% { transform: translate(8px, 0) rotate(0deg); }
                75% { transform: translate(5px, -2px) rotate(-2deg); }
                100% { transform: translate(0, 0) rotate(0deg); }
            }
            
            @keyframes paperWave {
                0% { transform: scaleY(1); }
                50% { transform: scaleY(1.02); }
                100% { transform: scaleY(1); }
            }
            
            @keyframes blink {
                0%, 45%, 55%, 100% { opacity: 1; }
                50% { opacity: 0; }
            }
            
            @keyframes flipPage {
                0% { transform: rotateY(0); }
                50% { transform: rotateY(180deg); }
                100% { transform: rotateY(360deg); }
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Tamanhos responsivos */
            @media (max-width: 768px) {
                .loading-animation {
                    max-width: 90%;
                    padding: 20px;
                }
                
                .animation-wrapper {
                    height: 150px;
                }
                
                .loading-content h3 {
                    font-size: 1.2rem;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Obtém a animação de geração de conteúdo
     * @returns {string} Código SVG animado
     */
    getGenerateAnimation() {
        return `
        <svg class="writer-svg" width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Mesa -->
            <rect x="20" y="140" width="160" height="10" fill="#8B4513" />
            
            <!-- Papel -->
            <rect class="animate-paper" x="40" y="50" width="80" height="100" fill="#fff" stroke="#ccc" />
            <line x1="50" y1="70" x2="110" y2="70" stroke="#ddd" stroke-width="2" />
            <line x1="50" y1="90" x2="110" y2="90" stroke="#ddd" stroke-width="2" />
            <line x1="50" y1="110" x2="110" y2="110" stroke="#ddd" stroke-width="2" />
            <line x1="50" y1="130" x2="90" y2="130" stroke="#ddd" stroke-width="2" />
            
            <!-- Caneta -->
            <g class="animate-pen">
                <rect x="110" y="90" width="50" height="6" rx="2" fill="#1a73e8" transform="rotate(-30 110 90)" />
                <polygon points="110,85 115,88 113,93 108,90" fill="#ff9800" />
            </g>
            
            <!-- Escritor -->
            <g transform="translate(140, 90)">
                <circle cx="0" cy="0" r="15" fill="#f5d8ba" /> <!-- Cabeça -->
                <g class="animate-face">
                    <circle cx="-5" cy="-2" r="2" fill="#333" /> <!-- Olho esquerdo -->
                    <circle cx="5" cy="-2" r="2" fill="#333" /> <!-- Olho direito -->
                </g>
                <path d="M-5,5 C-3,8 3,8 5,5" stroke="#333" stroke-width="1.5" fill="none" /> <!-- Sorriso -->
                <path d="M0,15 L0,50 M0,25 L-15,40 M0,25 L15,40" stroke="#333" stroke-width="3" /> <!-- Corpo e braços -->
            </g>
            
            <!-- Nuvens de pensamento/ideias -->
            <circle cx="150" cy="50" r="8" fill="#e6f7ff" stroke="#b3e5fc" />
            <circle cx="165" cy="45" r="6" fill="#e6f7ff" stroke="#b3e5fc" />
            <circle cx="155" cy="35" r="7" fill="#e6f7ff" stroke="#b3e5fc" />
            <text x="155" y="50" font-size="8" fill="#0d6efd" text-anchor="middle">💡</text>
        </svg>
        `;
    }
    
    /**
     * Obtém a animação de publicação
     * @returns {string} Código SVG animado
     */
    getPublishAnimation() {
        return `
        <svg class="writer-svg" width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Computador -->
            <rect x="40" y="70" width="120" height="80" rx="5" fill="#f0f0f0" stroke="#ccc" />
            <rect x="50" y="80" width="100" height="60" fill="#fff" stroke="#ddd" />
            <rect x="60" y="150" width="80" height="10" fill="#e0e0e0" />
            <rect x="75" y="160" width="50" height="5" fill="#d0d0d0" />
            
            <!-- Tela do WordPress -->
            <rect x="60" y="90" width="80" height="40" fill="#f9f9f9" />
            <g class="animate-wordpress" transform="translate(100, 110) scale(0.2)">
                <circle cx="0" cy="0" r="40" fill="#0073aa" />
                <path d="M-20,-20 L20,20 M-20,20 L20,-20" stroke="#fff" stroke-width="10" />
            </g>
            
            <!-- Artigo sendo publicado -->
            <g transform="translate(70, 85)">
                <rect width="20" height="25" fill="#fff" stroke="#ddd" />
                <line x1="3" y1="5" x2="17" y2="5" stroke="#ccc" />
                <line x1="3" y1="10" x2="17" y2="10" stroke="#ccc" />
                <line x1="3" y1="15" x2="17" y2="15" stroke="#ccc" />
                <line x1="3" y1="20" x2="12" y2="20" stroke="#ccc" />
            </g>
            
            <!-- Setas de upload -->
            <g transform="translate(100, 95)">
                <path d="M0,15 L0,0 L-5,5 M0,0 L5,5" stroke="#0d6efd" stroke-width="2" />
                <path d="M-10,10 L-10,-5 L-15,0 M-10,-5 L-5,0" stroke="#0d6efd" stroke-width="2" opacity="0.7" />
                <path d="M10,10 L10,-5 L5,0 M10,-5 L15,0" stroke="#0d6efd" stroke-width="2" opacity="0.4" />
            </g>
            
            <!-- Nuvem da internet -->
            <path d="M100,40 C125,40 125,60 100,60 C75,60 75,40 100,40" fill="#e6f7ff" stroke="#b3e5fc" />
            <circle cx="85" cy="50" r="10" fill="#e6f7ff" stroke="#b3e5fc" />
            <circle cx="115" cy="50" r="10" fill="#e6f7ff" stroke="#b3e5fc" />
        </svg>
        `;
    }
    
    /**
     * Obtém a animação de agendamento
     * @returns {string} Código SVG animado
     */
    getScheduleAnimation() {
        return `
        <svg class="writer-svg" width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Calendário -->
            <rect x="50" y="60" width="100" height="100" rx="5" fill="#fff" stroke="#ddd" />
            <rect x="50" y="60" width="100" height="20" rx="5" fill="#f44336" />
            
            <!-- Dias da semana -->
            <text x="65" y="75" font-size="8" fill="#fff">S</text>
            <text x="80" y="75" font-size="8" fill="#fff">M</text>
            <text x="95" y="75" font-size="8" fill="#fff">T</text>
            <text x="110" y="75" font-size="8" fill="#fff">W</text>
            <text x="125" y="75" font-size="8" fill="#fff">T</text>
            <text x="140" y="75" font-size="8" fill="#fff">F</text>
            
            <!-- Células do calendário -->
            <g class="animate-calendar">
                <rect x="60" y="90" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="80" y="90" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="100" y="90" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="120" y="90" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                
                <rect x="60" y="110" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="80" y="110" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="100" y="110" width="12" height="12" rx="2" fill="#e3f2fd" stroke="#2196f3" strokeWidth="2" />
                <rect x="120" y="110" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                
                <rect x="60" y="130" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="80" y="130" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="100" y="130" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                <rect x="120" y="130" width="12" height="12" rx="2" fill="#f9f9f9" stroke="#eee" />
                
                <!-- Números -->
                <text x="64" y="99" font-size="8" fill="#333">1</text>
                <text x="84" y="99" font-size="8" fill="#333">2</text>
                <text x="104" y="99" font-size="8" fill="#333">3</text>
                <text x="124" y="99" font-size="8" fill="#333">4</text>
                
                <text x="64" y="119" font-size="8" fill="#333">5</text>
                <text x="84" y="119" font-size="8" fill="#333">6</text>
                <text x="104" y="119" font-size="8" fill="#333">7</text>
                <text x="124" y="119" font-size="8" fill="#333">8</text>
                
                <text x="64" y="139" font-size="8" fill="#333">9</text>
                <text x="83" y="139" font-size="8" fill="#333">10</text>
                <text x="103" y="139" font-size="8" fill="#333">11</text>
                <text x="123" y="139" font-size="8" fill="#333">12</text>
            </g>
            
            <!-- Relógio -->
            <circle cx="160" cy="40" r="15" fill="#fff" stroke="#ddd" />
            <line x1="160" y1="40" x2="160" y2="30" stroke="#333" stroke-width="2" />
            <line x1="160" y1="40" x2="167" y2="45" stroke="#333" stroke-width="1.5" />
            <circle cx="160" cy="40" r="2" fill="#333" />
            
            <!-- Artigo -->
            <g transform="translate(35, 100)">
                <rect width="20" height="25" fill="#fff" stroke="#ddd" />
                <line x1="3" y1="5" x2="17" y2="5" stroke="#ccc" />
                <line x1="3" y1="10" x2="17" y2="10" stroke="#ccc" />
                <line x1="3" y1="15" x2="17" y2="15" stroke="#ccc" />
                <line x1="3" y1="20" x2="12" y2="20" stroke="#ccc" />
            </g>
            
            <!-- Seta -->
            <path d="M65,110 L90,110" stroke="#0d6efd" stroke-width="2" marker-end="url(#arrowhead)" />
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#0d6efd" />
                </marker>
            </defs>
        </svg>
        `;
    }
    
    /**
     * Obtém a animação padrão
     * @returns {string} Código SVG animado
     */
    getDefaultAnimation() {
        return `
        <svg class="writer-svg" width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Círculos de carregamento -->
            <circle cx="100" cy="100" r="50" stroke="#e0e0e0" stroke-width="8" fill="none" />
            <circle cx="100" cy="100" r="50" stroke="#0d6efd" stroke-width="8" fill="none" stroke-dasharray="314" stroke-dashoffset="0" stroke-linecap="round">
                <animateTransform 
                    attributeName="transform" 
                    type="rotate" 
                    from="0 100 100" 
                    to="360 100 100" 
                    dur="2s" 
                    repeatCount="indefinite" />
            </circle>
            
            <!-- Ícone central -->
            <g transform="translate(100, 100) scale(0.5)">
                <rect x="-20" y="-25" width="40" height="50" fill="#fff" stroke="#ddd" />
                <line x1="-12" y1="-15" x2="12" y2="-15" stroke="#ccc" stroke-width="2" />
                <line x1="-12" y1="-5" x2="12" y2="-5" stroke="#ccc" stroke-width="2" />
                <line x1="-12" y1="5" x2="12" y2="5" stroke="#ccc" stroke-width="2" />
                <line x1="-12" y1="15" x2="0" y2="15" stroke="#ccc" stroke-width="2" />
            </g>
        </svg>
        `;
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Criar instância global para animações de carregamento
    window.loadingAnimations = new LoadingAnimations();
    
    // Interceptar cliques em botões de ação para mostrar animações
    const setupLoadingButtons = () => {
        // Botões de geração de conteúdo
        document.querySelectorAll('.btn-generate-content, [data-action="generate"]').forEach(button => {
            const originalClick = button.onclick;
            
            button.onclick = function(e) {
                // Mostrar animação
                window.loadingAnimations.show('A IA está escrevendo seu conteúdo...', 'generate');
                
                // Executar função original após um pequeno delay (simulação)
                if (originalClick) {
                    return originalClick.call(this, e);
                }
            };
        });
        
        // Botões de publicação
        document.querySelectorAll('.btn-publish, [data-action="publish"]').forEach(button => {
            const originalClick = button.onclick;
            
            button.onclick = function(e) {
                // Mostrar animação
                window.loadingAnimations.show('Publicando artigo no WordPress...', 'publish');
                
                // Executar função original
                if (originalClick) {
                    return originalClick.call(this, e);
                }
            };
        });
        
        // Botões de agendamento
        document.querySelectorAll('.btn-schedule, [data-action="schedule"]').forEach(button => {
            const originalClick = button.onclick;
            
            button.onclick = function(e) {
                // Mostrar animação
                window.loadingAnimations.show('Configurando o agendamento...', 'schedule');
                
                // Executar função original
                if (originalClick) {
                    return originalClick.call(this, e);
                }
            };
        });
    };
    
    // Configurar depois que o DOM estiver completamente carregado
    setTimeout(setupLoadingButtons, 500);
});
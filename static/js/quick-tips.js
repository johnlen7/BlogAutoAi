/**
 * Barra lateral de "Dicas Rápidas" que desliza com conselhos contextuais de escrita com IA
 */

class QuickTips {
    constructor(options = {}) {
        this.options = {
            position: 'right', // 'right' ou 'left'
            autoShow: true,    // mostrar automaticamente após carregar
            delay: 1000,       // delay para mostrar automaticamente (ms)
            ...options
        };
        
        this.isOpen = false;
        this.currentTipIndex = 0;
        
        // Conjunto de dicas de escrita
        this.tips = [
            {
                title: "Estrutura clara",
                content: "Use títulos e subtítulos para dividir seu conteúdo em seções lógicas. Isso ajuda os leitores a navegar pelo seu texto e encontrar informações específicas.",
                icon: "fa-heading"
            },
            {
                title: "Comece com o mais importante",
                content: "Coloque as informações mais importantes no início do artigo. Isso ajuda os leitores a obterem rapidamente o que precisam, mesmo que não leiam o texto inteiro.",
                icon: "fa-star"
            },
            {
                title: "Seja conciso",
                content: "Elimine palavras desnecessárias e evite jargões. Frases curtas e diretas são mais fáceis de ler e compreender.",
                icon: "fa-cut"
            },
            {
                title: "Use linguagem ativa",
                content: "Escolha a voz ativa em vez da passiva. Em vez de 'O artigo foi escrito por mim', escreva 'Eu escrevi o artigo'.",
                icon: "fa-bolt"
            },
            {
                title: "Inclua palavras-chave",
                content: "Distribua palavras-chave relacionadas ao seu tópico naturalmente ao longo do texto, especialmente nos títulos e nos primeiros parágrafos.",
                icon: "fa-key"
            },
            {
                title: "Escreva para seu público",
                content: "Adapte seu tom e vocabulário para seu público-alvo. Um artigo técnico para especialistas será diferente de um para iniciantes.",
                icon: "fa-users"
            },
            {
                title: "Use exemplos concretos",
                content: "Ilustre conceitos abstratos com exemplos práticos e histórias. Isso torna seu conteúdo mais envolvente e fácil de entender.",
                icon: "fa-lightbulb"
            },
            {
                title: "Edite e revise",
                content: "A primeira versão raramente é a melhor. Edite seu trabalho para clareza, concisão e correção. Leia em voz alta para identificar problemas de fluxo.",
                icon: "fa-edit"
            },
            {
                title: "Conclusão memorável",
                content: "Termine com uma conclusão forte que reforce sua mensagem principal ou incentive à ação. É sua última chance de deixar uma impressão duradoura.",
                icon: "fa-flag-checkered"
            },
            {
                title: "Verifique os fatos",
                content: "Certifique-se de que todas as informações em seu artigo estão corretas e atualizadas. Cite suas fontes quando necessário para construir credibilidade.",
                icon: "fa-check-double"
            },
            {
                title: "Mantenha parágrafos curtos",
                content: "Parágrafos mais curtos (3-5 linhas) criam mais espaço em branco na página e tornam seu texto menos intimidador, especialmente para leitura online.",
                icon: "fa-indent"
            },
            {
                title: "Use imagens e mídia",
                content: "Adicione imagens, infográficos ou vídeos relevantes para quebrar texto longo e ilustrar pontos importantes. O conteúdo visual aumenta o engajamento.",
                icon: "fa-image"
            }
        ];
        
        this.contextualTips = {
            title: {
                trigger: ["título", "title", "heading", "headline"],
                tips: [
                    {
                        title: "Títulos eficazes",
                        content: "Use números, faça perguntas, ou crie urgência para tornar seus títulos mais atraentes. Por exemplo, '7 maneiras de melhorar sua escrita' ou 'Por que você precisa otimizar seu conteúdo agora?'",
                        icon: "fa-heading"
                    },
                    {
                        title: "SEO para títulos",
                        content: "Coloque palavras-chave importantes no início do seu título para melhor SEO. Mantenha entre 50-60 caracteres para evitar truncamento nos resultados de busca.",
                        icon: "fa-search"
                    }
                ]
            },
            introduction: {
                trigger: ["introdução", "introduction", "começar", "start"],
                tips: [
                    {
                        title: "Introduções cativantes",
                        content: "Comece com uma estatística surpreendente, uma pergunta intrigante ou uma história relevante para capturar a atenção do leitor imediatamente.",
                        icon: "fa-magic"
                    },
                    {
                        title: "Estrutura de introdução",
                        content: "Uma boa introdução estabelece o problema, indica por que é importante e sugere como o artigo vai resolvê-lo ou abordá-lo.",
                        icon: "fa-map"
                    }
                ]
            },
            seo: {
                trigger: ["seo", "search", "busca", "google", "ranking"],
                tips: [
                    {
                        title: "Otimização para SEO",
                        content: "Distribua suas palavras-chave naturalmente em títulos, subtítulos, primeiros 100 palavras e meta descrição. Use variações de palavras-chave e termos relacionados.",
                        icon: "fa-search"
                    },
                    {
                        title: "Links internos e externos",
                        content: "Adicione links para outros conteúdos relevantes em seu site (internos) e para fontes autoritativas externas para melhorar a credibilidade e o SEO.",
                        icon: "fa-link"
                    }
                ]
            }
        };
        
        this.create();
        this.setCurrentTip();
        
        if (this.options.autoShow) {
            setTimeout(() => this.open(), this.options.delay);
        }
    }
    
    create() {
        // Criar elemento container
        this.element = document.createElement('div');
        this.element.className = `quick-tips-panel ${this.options.position}`;
        
        // Botão de alternância
        this.toggleButton = document.createElement('button');
        this.toggleButton.className = 'quick-tips-toggle';
        this.toggleButton.innerHTML = `
            <i class="fas fa-lightbulb"></i>
            <span>Dicas</span>
        `;
        
        // Container de conteúdo
        this.contentContainer = document.createElement('div');
        this.contentContainer.className = 'quick-tips-content';
        
        // Cabeçalho
        const header = document.createElement('div');
        header.className = 'quick-tips-header';
        header.innerHTML = `
            <h3><i class="fas fa-lightbulb"></i> Dicas Rápidas</h3>
            <button class="quick-tips-close"><i class="fas fa-times"></i></button>
        `;
        
        // Container para a dica atual
        this.tipContainer = document.createElement('div');
        this.tipContainer.className = 'quick-tip';
        
        // Navegação entre dicas
        const navigation = document.createElement('div');
        navigation.className = 'quick-tips-navigation';
        navigation.innerHTML = `
            <button class="prev-tip"><i class="fas fa-arrow-left"></i></button>
            <span class="tip-counter"></span>
            <button class="next-tip"><i class="fas fa-arrow-right"></i></button>
        `;
        
        // Montar estrutura
        this.contentContainer.appendChild(header);
        this.contentContainer.appendChild(this.tipContainer);
        this.contentContainer.appendChild(navigation);
        
        this.element.appendChild(this.toggleButton);
        this.element.appendChild(this.contentContainer);
        
        // Adicionar ao corpo do documento
        document.body.appendChild(this.element);
        
        // Adicionar estilos
        this.addStyles();
        
        // Adicionar eventos
        this.addEventListeners();
        
        // Atualizar contador
        this.updateCounter();
    }
    
    addEventListeners() {
        // Botão de alternância
        this.toggleButton.addEventListener('click', () => {
            this.toggle();
        });
        
        // Botão de fechar
        const closeButton = this.contentContainer.querySelector('.quick-tips-close');
        closeButton.addEventListener('click', () => {
            this.close();
        });
        
        // Navegação entre dicas
        const prevButton = this.contentContainer.querySelector('.prev-tip');
        const nextButton = this.contentContainer.querySelector('.next-tip');
        
        prevButton.addEventListener('click', () => {
            this.showPreviousTip();
        });
        
        nextButton.addEventListener('click', () => {
            this.showNextTip();
        });
        
        // Monitorar contexto de escrita
        this.monitorWritingContext();
    }
    
    monitorWritingContext() {
        // Encontrar todos os editores e campos de texto na página
        const editors = document.querySelectorAll('textarea, [contenteditable="true"]');
        
        editors.forEach(editor => {
            editor.addEventListener('input', (event) => {
                const text = editor.value || editor.textContent;
                if (text) {
                    this.checkContextualTips(text);
                }
            });
        });
    }
    
    checkContextualTips(text) {
        // Verificar o texto para gatilhos contextuais
        for (const [context, data] of Object.entries(this.contextualTips)) {
            for (const trigger of data.trigger) {
                if (text.toLowerCase().includes(trigger.toLowerCase())) {
                    // Selecionar uma dica aleatória do contexto
                    const randomTip = data.tips[Math.floor(Math.random() * data.tips.length)];
                    
                    // Mostrar dica contextual
                    this.showContextualTip(randomTip);
                    return;
                }
            }
        }
    }
    
    showContextualTip(tip) {
        // Não mostrar se o painel estiver fechado
        if (!this.isOpen) {
            this.open();
        }
        
        // Atualizar conteúdo
        this.tipContainer.innerHTML = `
            <div class="contextual-badge">Dica Contextual</div>
            <div class="tip-icon"><i class="fas ${tip.icon}"></i></div>
            <h4>${tip.title}</h4>
            <p>${tip.content}</p>
        `;
        
        // Animar para chamar atenção
        this.tipContainer.classList.add('highlight');
        setTimeout(() => {
            this.tipContainer.classList.remove('highlight');
        }, 1000);
    }
    
    setCurrentTip() {
        const tip = this.tips[this.currentTipIndex];
        
        this.tipContainer.innerHTML = `
            <div class="tip-icon"><i class="fas ${tip.icon}"></i></div>
            <h4>${tip.title}</h4>
            <p>${tip.content}</p>
        `;
        
        this.updateCounter();
    }
    
    updateCounter() {
        const counter = this.contentContainer.querySelector('.tip-counter');
        counter.textContent = `${this.currentTipIndex + 1}/${this.tips.length}`;
    }
    
    showNextTip() {
        this.currentTipIndex = (this.currentTipIndex + 1) % this.tips.length;
        this.setCurrentTip();
    }
    
    showPreviousTip() {
        this.currentTipIndex = (this.currentTipIndex - 1 + this.tips.length) % this.tips.length;
        this.setCurrentTip();
    }
    
    open() {
        this.isOpen = true;
        this.element.classList.add('open');
    }
    
    close() {
        this.isOpen = false;
        this.element.classList.remove('open');
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    addStyles() {
        if (document.getElementById('quick-tips-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'quick-tips-styles';
        
        style.textContent = `
            .quick-tips-panel {
                position: fixed;
                top: 50%;
                transform: translateY(-50%);
                z-index: 1000;
                transition: all 0.3s ease;
            }
            
            .quick-tips-panel.right {
                right: -320px;
            }
            
            .quick-tips-panel.left {
                left: -320px;
            }
            
            .quick-tips-panel.open.right {
                right: 0;
            }
            
            .quick-tips-panel.open.left {
                left: 0;
            }
            
            .quick-tips-toggle {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                width: 40px;
                height: 120px;
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 6px 0 0 6px;
                cursor: pointer;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 10px 5px;
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                transition: all 0.2s;
            }
            
            .quick-tips-panel.right .quick-tips-toggle {
                left: -40px;
            }
            
            .quick-tips-panel.left .quick-tips-toggle {
                right: -40px;
                border-radius: 0 6px 6px 0;
            }
            
            .quick-tips-toggle i {
                font-size: 1.2rem;
                margin-bottom: 10px;
            }
            
            .quick-tips-toggle span {
                writing-mode: vertical-rl;
                text-orientation: mixed;
                transform: rotate(180deg);
                font-size: 0.8rem;
                font-weight: bold;
            }
            
            .quick-tips-toggle:hover {
                background-color: #0b5ed7;
            }
            
            .quick-tips-content {
                width: 320px;
                background-color: white;
                border-radius: 8px 0 0 8px;
                box-shadow: -2px 0 15px rgba(0,0,0,0.15);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                max-height: 450px;
                border: 1px solid #ddd;
                border-right: none;
            }
            
            .quick-tips-panel.left .quick-tips-content {
                border-radius: 0 8px 8px 0;
                border: 1px solid #ddd;
                border-left: none;
            }
            
            .quick-tips-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }
            
            .quick-tips-header h3 {
                margin: 0;
                font-size: 1.1rem;
                color: #333;
                display: flex;
                align-items: center;
            }
            
            .quick-tips-header h3 i {
                color: #ffc107;
                margin-right: 8px;
            }
            
            .quick-tips-close {
                background: none;
                border: none;
                color: #6c757d;
                cursor: pointer;
                font-size: 1rem;
                transition: color 0.2s;
            }
            
            .quick-tips-close:hover {
                color: #dc3545;
            }
            
            .quick-tip {
                padding: 20px;
                flex: 1;
                overflow-y: auto;
                transition: all 0.3s;
            }
            
            .quick-tip.highlight {
                background-color: rgba(13, 110, 253, 0.05);
            }
            
            .tip-icon {
                width: 50px;
                height: 50px;
                background-color: rgba(13, 110, 253, 0.1);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 15px;
            }
            
            .tip-icon i {
                font-size: 1.5rem;
                color: #0d6efd;
            }
            
            .quick-tip h4 {
                font-size: 1.1rem;
                text-align: center;
                margin-bottom: 15px;
                color: #333;
            }
            
            .quick-tip p {
                font-size: 0.9rem;
                line-height: 1.6;
                color: #555;
            }
            
            .contextual-badge {
                position: absolute;
                top: 10px;
                right: 10px;
                background-color: #28a745;
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: bold;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 0.7; }
                50% { opacity: 1; }
                100% { opacity: 0.7; }
            }
            
            .quick-tips-navigation {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background-color: #f8f9fa;
                border-top: 1px solid #ddd;
            }
            
            .quick-tips-navigation button {
                background: none;
                border: none;
                color: #0d6efd;
                cursor: pointer;
                padding: 5px 10px;
                border-radius: 4px;
                transition: all 0.2s;
            }
            
            .quick-tips-navigation button:hover {
                background-color: rgba(13, 110, 253, 0.1);
            }
            
            .tip-counter {
                font-size: 0.8rem;
                color: #6c757d;
            }
            
            @media (max-width: 768px) {
                .quick-tips-panel {
                    display: none;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar o componente de dicas rápidas
    const quickTips = new QuickTips({
        position: 'right',
        autoShow: false,
        delay: 3000
    });
    
    // Disponibilizar globalmente
    window.quickTips = quickTips;
});
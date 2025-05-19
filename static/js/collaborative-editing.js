/**
 * Sistema de edição colaborativa em tempo real
 * Implementa indicadores de presença de usuários e sincronização de conteúdo
 */

class CollaborativeEditor {
    constructor(editorElement, options = {}) {
        this.editor = editorElement;
        this.options = {
            syncInterval: 2000, // Intervalo de sincronização em milissegundos
            userColor: this.generateRandomColor(),
            userName: options.userName || 'Usuário',
            ...options
        };
        
        this.presenceIndicators = {};
        this.lastCursorPosition = 0;
        this.lastEditTime = Date.now();
        
        this.setupEditor();
        this.setupPresenceContainer();
        this.setupSyncInterval();
    }
    
    setupEditor() {
        // Adicionar classe ao editor para estilização
        this.editor.classList.add('collaborative-editor');
        
        // Eventos para sincronização
        this.editor.addEventListener('input', this.handleInput.bind(this));
        this.editor.addEventListener('click', this.handleCursorMove.bind(this));
        this.editor.addEventListener('keyup', this.handleCursorMove.bind(this));
    }
    
    setupPresenceContainer() {
        // Criar container para indicadores de presença
        this.presenceContainer = document.createElement('div');
        this.presenceContainer.className = 'presence-indicators';
        
        // Inserir após o editor
        this.editor.parentNode.insertBefore(this.presenceContainer, this.editor.nextSibling);
        
        // Adicionar estilo
        const style = document.createElement('style');
        style.textContent = `
            .presence-indicators {
                display: flex;
                flex-wrap: wrap;
                margin-top: 10px;
                gap: 10px;
            }
            
            .presence-indicator {
                display: flex;
                align-items: center;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                color: white;
                white-space: nowrap;
                animation: appear 0.3s ease-in-out;
            }
            
            .presence-indicator .avatar {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 5px;
                font-weight: bold;
            }
            
            .cursor-indicator {
                position: absolute;
                width: 2px;
                height: 20px;
                animation: blink 1s infinite;
            }
            
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0; }
            }
            
            @keyframes appear {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            
            .editing-feedback {
                position: absolute;
                font-size: 12px;
                padding: 2px 8px;
                border-radius: 4px;
                pointer-events: none;
                opacity: 0;
                transform: translateY(-10px);
                transition: opacity 0.3s, transform 0.3s;
            }
            
            .editing-feedback.show {
                opacity: 1;
                transform: translateY(0);
            }
            
            .collaborative-editor {
                position: relative;
                transition: outline-color 0.3s;
            }
        `;
        
        document.head.appendChild(style);
        
        // Adicionar própria presença
        this.addUserPresence(this.options.userId || 'self', this.options.userName, this.options.userColor);
    }
    
    setupSyncInterval() {
        // Simular sincronização periódica
        this.syncInterval = setInterval(() => {
            this.syncContent();
        }, this.options.syncInterval);
    }
    
    handleInput(event) {
        this.lastEditTime = Date.now();
        this.showEditingFeedback();
        
        // Notificar outros colaboradores (simulado)
        setTimeout(() => {
            this.emitContentUpdate();
        }, 100);
    }
    
    handleCursorMove(event) {
        const cursorPosition = this.editor.selectionStart;
        if (cursorPosition !== this.lastCursorPosition) {
            this.lastCursorPosition = cursorPosition;
            
            // Notificar outros colaboradores (simulado)
            setTimeout(() => {
                this.emitCursorUpdate();
            }, 100);
        }
    }
    
    addUserPresence(userId, userName, color) {
        // Remover indicador existente se já existir
        if (this.presenceIndicators[userId]) {
            this.presenceIndicators[userId].element.remove();
        }
        
        // Criar indicador de presença
        const indicator = document.createElement('div');
        indicator.className = 'presence-indicator';
        indicator.style.backgroundColor = color;
        
        // Criar avatar
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = userName.charAt(0).toUpperCase();
        avatar.style.backgroundColor = this.darkenColor(color, 20);
        
        // Adicionar nome
        const name = document.createElement('span');
        name.textContent = userName;
        
        // Montar indicador
        indicator.appendChild(avatar);
        indicator.appendChild(name);
        
        // Adicionar ao container
        this.presenceContainer.appendChild(indicator);
        
        // Registrar para referência futura
        this.presenceIndicators[userId] = {
            element: indicator,
            color: color,
            name: userName,
            lastSeen: Date.now()
        };
        
        // Retornar referência
        return indicator;
    }
    
    removeUserPresence(userId) {
        if (this.presenceIndicators[userId]) {
            this.presenceIndicators[userId].element.remove();
            delete this.presenceIndicators[userId];
        }
    }
    
    syncContent() {
        // Simulação de sincronização
        const timeSinceLastEdit = Date.now() - this.lastEditTime;
        
        // Se passou um tempo desde a última edição, mostrar status salvo
        if (timeSinceLastEdit > 2000) {
            this.showSavedStatus();
        }
        
        // Simular ocasionalmente outros usuários editando
        this.simulateCollaborators();
    }
    
    simulateCollaborators() {
        // Simulação básica de outros usuários para demonstração
        const shouldSimulate = Math.random() > 0.7; // 30% chance
        
        if (shouldSimulate) {
            const editorNames = [
                'João', 'Maria', 'Carlos', 'Ana', 'Pedro',
                'Lucas', 'Amanda', 'Fernando', 'Juliana', 'Roberto'
            ];
            
            const randomName = editorNames[Math.floor(Math.random() * editorNames.length)];
            const userId = 'user_' + Math.floor(Math.random() * 1000);
            
            if (!this.presenceIndicators[userId]) {
                const color = this.generateRandomColor();
                this.addUserPresence(userId, randomName, color);
                
                // Remover após um tempo aleatório
                setTimeout(() => {
                    this.removeUserPresence(userId);
                }, 10000 + Math.random() * 30000);
            }
        }
    }
    
    showEditingFeedback() {
        // Remover feedback existente
        const existingFeedback = document.querySelector('.editing-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        // Criar novo feedback
        const feedback = document.createElement('div');
        feedback.className = 'editing-feedback';
        feedback.textContent = 'Escrevendo...';
        feedback.style.backgroundColor = this.options.userColor;
        feedback.style.color = this.getContrastColor(this.options.userColor);
        
        // Posicionar relativo ao editor
        const editorRect = this.editor.getBoundingClientRect();
        feedback.style.top = '-25px';
        feedback.style.right = '10px';
        
        // Adicionar ao documento
        this.editor.parentNode.style.position = 'relative';
        this.editor.parentNode.appendChild(feedback);
        
        // Animar
        setTimeout(() => {
            feedback.classList.add('show');
        }, 10);
        
        // Remover após um tempo
        setTimeout(() => {
            feedback.classList.remove('show');
            setTimeout(() => {
                feedback.remove();
            }, 300);
        }, 2000);
    }
    
    showSavedStatus() {
        // Remover feedback existente
        const existingFeedback = document.querySelector('.editing-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        // Criar novo feedback
        const feedback = document.createElement('div');
        feedback.className = 'editing-feedback';
        feedback.textContent = 'Salvo ✓';
        feedback.style.backgroundColor = '#28a745'; // verde
        feedback.style.color = 'white';
        
        // Posicionar relativo ao editor
        const editorRect = this.editor.getBoundingClientRect();
        feedback.style.top = '-25px';
        feedback.style.right = '10px';
        
        // Adicionar ao documento
        this.editor.parentNode.style.position = 'relative';
        this.editor.parentNode.appendChild(feedback);
        
        // Animar
        setTimeout(() => {
            feedback.classList.add('show');
        }, 10);
        
        // Remover após um tempo
        setTimeout(() => {
            feedback.classList.remove('show');
            setTimeout(() => {
                feedback.remove();
            }, 300);
        }, 2000);
    }
    
    emitContentUpdate() {
        // Implementar integração real com websockets aqui
        console.log('Emitindo atualização de conteúdo');
    }
    
    emitCursorUpdate() {
        // Implementar integração real com websockets aqui
        console.log('Emitindo atualização de cursor');
    }
    
    destroy() {
        // Limpar eventos e intervalos
        clearInterval(this.syncInterval);
        this.editor.removeEventListener('input', this.handleInput);
        this.editor.removeEventListener('click', this.handleCursorMove);
        this.editor.removeEventListener('keyup', this.handleCursorMove);
        
        // Remover elementos
        this.presenceContainer.remove();
    }
    
    // Utilitários
    generateRandomColor() {
        const hue = Math.floor(Math.random() * 360);
        return `hsl(${hue}, 70%, 60%)`;
    }
    
    darkenColor(color, percent) {
        // Simplificado para cores HSL
        if (color.startsWith('hsl')) {
            const hsl = color.match(/\d+/g).map(Number);
            return `hsl(${hsl[0]}, ${hsl[1]}%, ${Math.max(0, hsl[2] - percent)}%)`;
        }
        return color;
    }
    
    getContrastColor(color) {
        // Simplificado para cores HSL
        if (color.startsWith('hsl')) {
            const hsl = color.match(/\d+/g).map(Number);
            return hsl[2] > 60 ? '#000' : '#fff';
        }
        return '#fff';
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todos os editores com a classe "collaborative"
    const editors = document.querySelectorAll('textarea.collaborative, div[contenteditable="true"].collaborative');
    
    editors.forEach(editor => {
        // Obter nome de usuário do elemento de dados ou padrão
        const userName = editor.dataset.username || 'Usuário';
        
        // Inicializar editor colaborativo
        const collaborativeEditor = new CollaborativeEditor(editor, {
            userName: userName
        });
        
        // Armazenar referência no elemento
        editor.collaborativeEditor = collaborativeEditor;
    });
});
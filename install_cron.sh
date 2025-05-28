#!/bin/bash
# Script para instalar e configurar CRON jobs para BlogAuto AI

echo "🔧 Configurando automação CRON para BlogAuto AI"

# Obter diretório atual do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"
CRON_SCRIPT="$PROJECT_DIR/automation_cron.py"

echo "📁 Diretório do projeto: $PROJECT_DIR"
echo "🐍 Python path: $PYTHON_PATH"

# Verificar se o script de automação existe
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "❌ Erro: Script de automação não encontrado em $CRON_SCRIPT"
    exit 1
fi

# Tornar o script executável
chmod +x "$CRON_SCRIPT"
echo "✅ Script de automação tornado executável"

# Criar diretório de logs se não existir
mkdir -p "$PROJECT_DIR/logs"
echo "✅ Diretório de logs criado"

# Backup do crontab atual
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "ℹ️ Nenhum crontab existente para backup"

# Configurar novos CRON jobs
echo "📝 Configurando CRON jobs..."

# Temporário para novo crontab
TEMP_CRON=$(mktemp)

# Preservar CRON jobs existentes (exceto os do BlogAuto)
crontab -l 2>/dev/null | grep -v "BlogAuto AI" > "$TEMP_CRON" || true

# Adicionar novos CRON jobs para BlogAuto AI
cat >> "$TEMP_CRON" << EOF

# BlogAuto AI - Automação de artigos
# Executa a cada 15 minutos para verificar artigos agendados
*/15 * * * * cd "$PROJECT_DIR" && "$PYTHON_PATH" automation_cron.py >> logs/cron.log 2>&1

# BlogAuto AI - Processamento de feeds RSS
# Executa a cada 2 horas para buscar novos conteúdos
0 */2 * * * cd "$PROJECT_DIR" && "$PYTHON_PATH" automation_cron.py >> logs/cron.log 2>&1

# BlogAuto AI - Limpeza noturna
# Executa às 2h da madrugada para limpeza de dados
0 2 * * * cd "$PROJECT_DIR" && "$PYTHON_PATH" automation_cron.py >> logs/cron.log 2>&1

EOF

# Instalar novo crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ CRON jobs instalados com sucesso!"
echo ""
echo "📋 Jobs configurados:"
echo "   • A cada 15 minutos: Verificação de artigos agendados"
echo "   • A cada 2 horas: Processamento de feeds RSS"
echo "   • Diariamente às 2h: Limpeza de dados antigos"
echo ""
echo "📄 Logs serão salvos em: $PROJECT_DIR/logs/"
echo ""
echo "🔍 Para verificar os CRON jobs instalados:"
echo "   crontab -l"
echo ""
echo "🗑️ Para remover os CRON jobs:"
echo "   crontab -e  # Remova as linhas com 'BlogAuto AI'"
echo ""
echo "✨ Automação configurada! O sistema agora funcionará automaticamente."
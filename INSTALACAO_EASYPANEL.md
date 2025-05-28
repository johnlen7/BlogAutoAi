# 🚀 Instalação Completa do BlogAuto AI no EasyPanel

## Passo 1: Preparar o Código

1. **Faça upload deste projeto para seu GitHub:**
   - Crie um repositório novo no GitHub
   - Faça upload de todos os arquivos deste projeto
   - Certifique-se que está na branch `main`

## Passo 2: Configurar no EasyPanel

### 2.1 Criar Novo Projeto
1. Entre no seu painel EasyPanel
2. Clique em **"New Project"**
3. Dê o nome: `blogauto-ai`

### 2.2 Adicionar Banco MySQL
1. Dentro do projeto, clique em **"Add Service"**
2. Escolha **"MySQL"**
3. Configure:
   - **Service Name:** `mysql`
   - **Database Name:** `blogauto`
   - **Username:** `blogauto`
   - **Password:** (deixe gerar automaticamente)
   - **Root Password:** (deixe gerar automaticamente)

### 2.3 Adicionar Aplicação Principal
1. Clique em **"Add Service"** novamente
2. Escolha **"App"**
3. Configure:

**Básico:**
- **Service Name:** `app`
- **Source:** GitHub
- **Repository:** `seu-usuario/seu-repositorio`
- **Branch:** `main`

**Build:**
- **Build Type:** Dockerfile
- **Dockerfile Path:** `Dockerfile`

**Deploy:**
- **Port:** `5000`
- **Command:** (deixe vazio)

**Domain:**
- Adicione seu domínio ou use o subdomínio do EasyPanel

**Environment Variables:**
```
SECRET_KEY=sua_chave_secreta_aqui
DB_HOST=mysql
DB_USER=blogauto
DB_PASSWORD=senha_do_mysql_gerada
DB_NAME=blogauto
OPENAI_API_KEY=sua_chave_openai_aqui
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui
```

### 2.4 Adicionar Worker de Automação
1. Clique em **"Add Service"** mais uma vez
2. Escolha **"App"**
3. Configure:

**Básico:**
- **Service Name:** `automation`
- **Source:** GitHub (mesmo repositório)
- **Repository:** `seu-usuario/seu-repositorio`
- **Branch:** `main`

**Build:**
- **Build Type:** Dockerfile
- **Dockerfile Path:** `Dockerfile`

**Deploy:**
- **Command:** `python automation_daemon.py`
- **No Port** (é um worker, não web app)

**Environment Variables:**
(As mesmas da aplicação principal)

## Passo 3: Deploy e Configuração

### 3.1 Fazer Deploy
1. Clique em **"Deploy"** em todos os serviços
2. Aguarde o build completar (pode levar alguns minutos)
3. Verifique se todos os serviços estão "Running"

### 3.2 Primeira Configuração
1. Acesse seu domínio da aplicação
2. Crie sua primeira conta de administrador
3. Configure:
   - **APIs:** Adicione suas chaves OpenAI/Claude
   - **WordPress:** Configure seu site WordPress
   - **Temas:** Adicione temas para automação
   - **Feeds RSS:** Configure feeds de notícias

### 3.3 Ativar Automação
1. Vá em **"Automação"** no menu
2. Configure horários de funcionamento
3. Ative a automação
4. O sistema começará a funcionar automaticamente!

## Passo 4: Monitoramento

### 4.1 Verificar Logs
- No EasyPanel, clique em cada serviço
- Vá na aba **"Logs"** para monitorar
- Logs de automação aparecerão no serviço `automation`

### 4.2 Verificar Funcionamento
- O worker de automação roda 24/7
- Busca feeds RSS automaticamente
- Gera artigos baseados em temas
- Publica automaticamente no WordPress

## 🎯 Variáveis de Ambiente Importantes

```bash
# Obrigatórias
SECRET_KEY=gere_uma_chave_secreta_forte
DB_HOST=mysql
DB_USER=blogauto
DB_PASSWORD=senha_gerada_pelo_easypanel
DB_NAME=blogauto

# APIs de IA (pelo menos uma é necessária)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Opcional
REDIS_URL=redis://redis:6379/0  # Se adicionar Redis
```

## 🔧 Dicas Importantes

1. **Backup:** EasyPanel faz backup automático do MySQL
2. **SSL:** É configurado automaticamente
3. **Domínio:** Você pode usar um domínio personalizado
4. **Escalabilidade:** Pode aumentar recursos conforme necessário
5. **Updates:** Basta fazer push no GitHub que atualiza automaticamente

## 🆘 Resolução de Problemas

### App não inicia:
- Verifique as variáveis de ambiente
- Confirme se o MySQL está rodando
- Veja os logs para erros específicos

### Automação não funciona:
- Verifique se o serviço `automation` está rodando
- Confirme se as chaves de API estão corretas
- Verifique se a automação está ativada no painel

### Banco de dados:
- Use as credenciais geradas pelo EasyPanel
- O MySQL roda automaticamente no mesmo projeto

## ✅ Pronto!

Após seguir estes passos, você terá:
- ✅ BlogAuto AI rodando 24/7
- ✅ Automação completa funcionando
- ✅ Banco MySQL configurado
- ✅ SSL automático
- ✅ Backups automáticos
- ✅ Monitoramento integrado

O sistema agora funciona completamente automático - gerando e publicando conteúdo sem você precisar fazer nada!
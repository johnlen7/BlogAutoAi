# 🚀 Instalação Definitiva do BlogAuto AI no EasyPanel

## ✅ Solução Mais Simples - Um Só Container

Como o EasyPanel tem limitações com workers separados, criei uma solução tudo-em-um que funciona perfeitamente:

### 📋 Passos para Instalar:

#### 1. **Subir Código para GitHub**
- Faça upload de todo este projeto para um repositório GitHub
- Certifique-se que está na branch `main`

#### 2. **No EasyPanel - Criar MySQL**
1. Novo Projeto → Nome: `blogauto-ai`
2. Add Service → **MySQL**
3. Configurações:
   - Database: `blogauto`
   - Username: `blogauto`
   - Password: (deixe auto-gerar)

#### 3. **No EasyPanel - Criar App Principal**
1. Add Service → **App**
2. Configurações básicas:
   - **Source:** GitHub
   - **Repository:** `seu-usuario/blogauto-ai`
   - **Branch:** `main`

3. **Build Settings:**
   - **Build Type:** Dockerfile
   - **Dockerfile:** `Dockerfile.easypanel`

4. **Deploy Settings:**
   - **Port:** `5000`
   - **Command:** (deixe vazio)

5. **Environment Variables:**
```
SECRET_KEY=gere_uma_chave_secreta_forte
DB_HOST=mysql
DB_USER=blogauto
DB_PASSWORD=senha_gerada_pelo_mysql
DB_NAME=blogauto
OPENAI_API_KEY=sua_chave_openai
ANTHROPIC_API_KEY=sua_chave_claude
```

#### 4. **Deploy**
- Clique em Deploy
- Aguarde o build (3-5 minutos)
- Acesse o domínio gerado

## 🎯 Como Funciona

Este setup único roda **dois processos** dentro do mesmo container:
- **Interface Web** (porta 5000)
- **Sistema de Automação** (background)

Ambos funcionam 24/7 automaticamente!

## 🔧 Configuração Inicial

Após o deploy:

1. **Acesse a aplicação** no domínio do EasyPanel
2. **Crie sua conta** de administrador  
3. **Configure APIs:**
   - Vá em Configurações → APIs
   - Adicione suas chaves OpenAI e/ou Claude
4. **Configure WordPress:**
   - Vá em Configurações → WordPress
   - Adicione sua URL e credenciais
5. **Configure Temas:**
   - Vá em Automação → Temas
   - Adicione palavras-chave dos seus nichos
6. **Ative a Automação:**
   - Configure horários de funcionamento
   - Defina intervalos de postagem
   - Ative o sistema

## ✨ Resultado Final

Depois de configurado, o sistema:
- ✅ Busca feeds RSS automaticamente
- ✅ Gera artigos únicos com IA
- ✅ Agenda publicações inteligentemente  
- ✅ Publica no WordPress automaticamente
- ✅ Funciona 24/7 sem intervenção

## 🆘 Se Precisar de Ajuda

- **Logs:** Veja na aba "Logs" do serviço no EasyPanel
- **Status:** Verifique se o serviço está "Running"
- **Banco:** As credenciais são geradas automaticamente

**Está pronto para começar?** O sistema é realmente plug-and-play - depois de configurado roda sozinho!
# BlogAuto AI

Uma aplicação web avançada para automação de criação e publicação de conteúdo para WordPress usando IA.

## 🚀 Funcionalidades Principais

- **Geração de Artigos com IA**: Utilize modelos avançados como Claude e GPT para criar conteúdo de qualidade
- **Automação de Publicação**: Agende posts para serem publicados automaticamente
- **Integração com WordPress**: Publique diretamente em seu site WordPress
- **Pesquisa Temática**: Configure temas de interesse para geração automática
- **Análise de Feeds RSS**: Monitore e transforme notícias em conteúdo original
- **Interface Bilíngue**: Suporte completo para Português e Inglês

## 📋 Requisitos

- Python 3.9+
- MySQL/MariaDB
- Chaves de API para Claude (Anthropic) e/ou GPT (OpenAI)
- Acesso administrativo a um site WordPress

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://seu-repositorio/blogauto-ai.git
cd blogauto-ai
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o banco de dados MySQL:
```bash
python setup_mysql.py
```

4. Inicie a aplicação:
```bash
python main.py
```

5. Acesse a aplicação no navegador: http://localhost:5000

## ⚙️ Configuração

1. Crie uma conta de usuário no primeiro acesso
2. Configure suas chaves de API em Configurações > APIs
3. Adicione sua configuração do WordPress em Configurações > WordPress
4. (Opcional) Configure temas e feeds RSS para automação

## 🔑 Variáveis de Ambiente

- `DB_USER`: Usuário do MySQL
- `DB_PASSWORD`: Senha do MySQL
- `DB_HOST`: Host do servidor MySQL (padrão: localhost)
- `DB_PORT`: Porta do MySQL (padrão: 3306)
- `DB_NAME`: Nome do banco de dados (padrão: blogauto)
- `SECRET_KEY`: Chave secreta para sessões (gerada automaticamente se não definida)

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

Se você tiver dúvidas ou precisar de ajuda, crie uma issue no repositório ou contate o suporte.
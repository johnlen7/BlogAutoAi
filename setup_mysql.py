#!/usr/bin/env python
"""
Script para configurar o banco de dados MySQL/MariaDB para o BlogAuto AI
Este script cria o banco de dados necessário se ele não existir
"""

import pymysql
import os
import sys
import getpass
from config import Config

def create_database():
    """Cria o banco de dados para a aplicação se não existir"""
    # Obter as configurações do ambiente ou usar valores padrão
    db_user = os.environ.get('DB_USER') or input("Digite o usuário MySQL (padrão: root): ") or "root"
    db_password = os.environ.get('DB_PASSWORD') or getpass.getpass(f"Digite a senha para {db_user}: ")
    db_host = os.environ.get('DB_HOST') or input("Digite o host MySQL (padrão: localhost): ") or "localhost"
    db_port = int(os.environ.get('DB_PORT') or input("Digite a porta MySQL (padrão: 3306): ") or "3306")
    db_name = os.environ.get('DB_NAME') or input("Digite o nome do banco de dados (padrão: blogauto): ") or "blogauto"

    # Armazenar os valores no ambiente para uso na aplicação
    os.environ['DB_USER'] = db_user
    os.environ['DB_PASSWORD'] = db_password
    os.environ['DB_HOST'] = db_host
    os.environ['DB_PORT'] = str(db_port)
    os.environ['DB_NAME'] = db_name

    # Primeiro conectar sem especificar um banco de dados
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        
        print(f"✅ Conectado ao servidor MySQL em {db_host}:{db_port}")
        
        # Criar o banco de dados se não existir
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Banco de dados '{db_name}' criado ou já existente")
            
            # Garantir que o usuário tem todos os privilégios necessários
            cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"✅ Privilégios concedidos ao usuário '{db_user}'")
        
        connection.close()
        
        # Tentar conectar ao banco de dados específico para verificar
        test_connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        test_connection.close()
        print(f"✅ Teste de conexão ao banco '{db_name}' bem sucedido")
        
        # Gerar a string de conexão para referência
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        print("\n🔗 String de conexão (DATABASE_URL):")
        print(f"DATABASE_URL={connection_string}")
        
        print("\n✨ Configuração do banco de dados concluída com sucesso!")
        print("Agora você pode iniciar a aplicação usando 'python main.py'")
        print("A aplicação criará automaticamente as tabelas necessárias no primeiro acesso.")
        
        return True
    
    except pymysql.MySQLError as e:
        print(f"❌ Erro ao conectar ou configurar o MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configurando banco de dados MySQL/MariaDB para BlogAuto AI\n")
    if not create_database():
        sys.exit(1)
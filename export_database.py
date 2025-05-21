#!/usr/bin/env python
"""
Script para exportar o esquema e dados do banco de dados para SQL
Isso permite recriar o banco de dados em um ambiente local MySQL
"""

import os
import sys
import datetime
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.schema import CreateTable, DropTable
from config import Config

def export_database():
    """Exporta o esquema do banco de dados para SQL"""
    try:
        # Obter a URL de conexão do ambiente ou configuração
        database_url = os.environ.get('DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI
        
        # Para ambientes de produção com PostgreSQL, converter para MySQL
        if database_url.startswith('postgres'):
            print("⚠️ Detectada URL PostgreSQL - convertendo para formato MySQL")
            # Extrair informações do PostgreSQL URL
            # Formato típico: postgres://user:pass@host:port/dbname
            parts = database_url.replace('postgres://', '').replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            host_port = host_db[0].split(':')
            
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '3306'
            dbname = host_db[1] if len(host_db) > 1 else 'blogauto'
            
            # Criar URL MySQL correspondente
            # Não usar a URL diretamente, apenas as partes para não expor senhas
            print(f"🔄 Informações extraídas: user={user}, host={host}, dbname={dbname}")
            mysql_url = f"mysql+pymysql://{user}:{password}@localhost:3306/{dbname}"
        else:
            mysql_url = database_url
            
        # Conectar ao banco de dados
        engine = create_engine(mysql_url)
        print(f"✅ Conectado ao banco de dados")
        
        # Timestamp para nome do arquivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blogauto_schema_{timestamp}.sql"
        
        # Criar o arquivo SQL
        with open(filename, 'w') as f:
            # Cabeçalho
            f.write("-- BlogAuto AI - Esquema do Banco de Dados\n")
            f.write(f"-- Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Para MySQL/MariaDB\n\n")
            
            # Começar com declaração de criação do banco de dados
            f.write("-- Criar o banco de dados (se não existir)\n")
            db_name = os.environ.get('DB_NAME', 'blogauto')
            f.write(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n")
            f.write(f"USE `{db_name}`;\n\n")
            
            # Obter metadata
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            # Criar instruções DROP TABLE para facilitar reimportação
            f.write("-- Remover tabelas existentes (se existirem)\n")
            for table in reversed(metadata.sorted_tables):
                drop_statement = str(DropTable(table, if_exists=True)).replace('\n', ' ').replace('  ', ' ')
                drop_statement = drop_statement.replace('DROP TABLE', 'DROP TABLE IF EXISTS')
                f.write(f"{drop_statement};\n")
            f.write("\n")
            
            # Gerar CREATE TABLE para cada tabela
            f.write("-- Criar tabelas\n")
            for table in metadata.sorted_tables:
                # Converter de PostgreSQL para MySQL se necessário
                create_statement = str(CreateTable(table))
                
                # Substituir tipos específicos do PostgreSQL para MySQL
                if database_url.startswith('postgres'):
                    create_statement = create_statement.replace('SERIAL', 'INT AUTO_INCREMENT')
                    create_statement = create_statement.replace('INTEGER', 'INT')
                    create_statement = create_statement.replace('BOOLEAN', 'TINYINT(1)')
                    create_statement = create_statement.replace('TEXT', 'LONGTEXT')
                    create_statement = create_statement.replace('TIMESTAMP WITHOUT TIME ZONE', 'DATETIME')
                    
                # Remover esquema se existir
                create_statement = create_statement.replace('CREATE TABLE public.', 'CREATE TABLE ')
                
                # Adicionar ENGINE e CHARACTER SET para MySQL
                create_statement = create_statement.rstrip() + " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n"
                
                f.write(f"{create_statement}\n")
            
            # Adicionar instruções para inserir registros importantes como configurações padrão
            f.write("-- Inserir dados iniciais\n")
            f.write("-- Adicione aqui seus inserts para dados iniciais\n\n")
            
            # Adicionar informações sobre como importar
            f.write("-- Para importar este esquema, execute:\n")
            f.write("-- mysql -u [usuario] -p [banco_de_dados] < este_arquivo.sql\n")
        
        print(f"✅ Esquema SQL exportado para {filename}")
        print(f"\nPara importar este esquema na sua máquina local:")
        print(f"1. Crie um banco de dados MySQL vazio")
        print(f"2. Execute: mysql -u seu_usuario -p seu_banco_de_dados < {filename}")
        print(f"   ou importe usando phpMyAdmin ou outro gerenciador MySQL")
        
        return True
    
    except Exception as e:
        print(f"❌ Erro ao exportar banco de dados: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Exportando esquema do banco de dados para SQL (formato MySQL)\n")
    export_database()
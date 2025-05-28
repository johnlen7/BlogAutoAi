#!/usr/bin/env python3
"""
Script principal para executar o sistema de automação do BlogAuto AI
Este script pode ser executado manualmente ou via CRON para automação completa
"""

import os
import sys
import logging
from pathlib import Path

# Configurar o ambiente
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Configurar logging
log_dir = project_dir / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'automation.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Executa o ciclo de automação"""
    try:
        logger.info("🚀 Iniciando BlogAuto AI - Sistema de Automação")
        
        # Importar e executar o motor de automação
        from services.automation_engine import AutomationEngine
        
        engine = AutomationEngine()
        engine.run_automation_cycle()
        
        logger.info("✅ Ciclo de automação concluído com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro crítico na automação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
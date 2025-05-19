import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app import db
from models import Article, ArticleStatus, SchedulerLog, LogType, AutomationSettings

logger = logging.getLogger(__name__)

class AutomationMonitor:
    """
    Serviço para monitorar e registrar o progresso da automação de conteúdo.
    Esta classe fornece métodos para acompanhar o status das tarefas de automação,
    registrar eventos no histórico e gerar relatórios.
    """
    
    @staticmethod
    def register_event(user_id: int, action_type: str, details: str, status: str = 'success') -> None:
        """
        Registra um evento no histórico de automação
        
        Args:
            user_id: ID do usuário
            action_type: Tipo de ação (generate, schedule, publish)
            details: Detalhes da ação
            status: Status da ação (success, failure)
        """
        log_type = LogType.SUCCESS if status == 'success' else LogType.ERROR
        
        log = SchedulerLog(
            message=f"{action_type}: {details}",
            log_type=log_type,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(log)
            db.session.commit()
            logger.info(f"Evento de automação registrado: {action_type} - {details}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao registrar evento de automação: {str(e)}")
    
    @staticmethod
    def get_automation_status(user_id: int) -> Dict[str, Any]:
        """
        Obtém o status atual da automação para um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com estatísticas e status da automação
        """
        try:
            # Contagem de artigos por status
            pending_count = Article.query.filter_by(
                user_id=user_id, 
                status=ArticleStatus.SCHEDULED,
                is_automated=True
            ).count()
            
            published_count = Article.query.filter_by(
                user_id=user_id, 
                status=ArticleStatus.PUBLISHED,
                is_automated=True
            ).count()
            
            failed_count = Article.query.filter_by(
                user_id=user_id, 
                status=ArticleStatus.FAILED,
                is_automated=True
            ).count()
            
            # Próxima execução agendada
            settings = AutomationSettings.query.filter_by(user_id=user_id).first()
            next_run = settings.next_scheduled_run if settings else None
            
            # Últimos logs
            logs = SchedulerLog.query.order_by(SchedulerLog.created_at.desc()).limit(10).all()
            
            return {
                'status': {
                    'is_active': settings.is_active if settings else False,
                    'pending_count': pending_count,
                    'published_count': published_count,
                    'failed_count': failed_count,
                    'next_run': next_run
                },
                'logs': [
                    {
                        'timestamp': log.created_at,
                        'message': log.message,
                        'type': log.log_type.value
                    } for log in logs
                ]
            }
        
        except Exception as e:
            logger.error(f"Erro ao obter status da automação: {str(e)}")
            return {
                'status': {
                    'is_active': False,
                    'pending_count': 0,
                    'published_count': 0,
                    'failed_count': 0,
                    'next_run': None
                },
                'logs': []
            }
    
    @staticmethod
    def check_health() -> Dict[str, Any]:
        """
        Verifica a saúde do sistema de automação
        
        Returns:
            Dicionário com status e detalhes do diagnóstico
        """
        issues = []
        status = "healthy"
        
        # Verificar problemas comuns
        failed_articles = Article.query.filter_by(status=ArticleStatus.FAILED).count()
        if failed_articles > 0:
            issues.append(f"Existem {failed_articles} artigos com falha na publicação")
            status = "warning"
        
        # Verificar artigos agendados sem data
        invalid_articles = Article.query.filter(
            Article.status == ArticleStatus.SCHEDULED,
            Article.scheduled_date == None
        ).count()
        
        if invalid_articles > 0:
            issues.append(f"Existem {invalid_articles} artigos agendados sem data definida")
            status = "warning"
        
        # Verificar se há configurações com WordPress inválidas
        settings_no_wp = AutomationSettings.query.filter(
            AutomationSettings.is_active == True,
            AutomationSettings.wordpress_config_id == None
        ).count()
        
        if settings_no_wp > 0:
            issues.append("Existem configurações de automação ativas sem WordPress configurado")
            status = "warning"
        
        # Verificar falhas frequentes
        recent_failures = SchedulerLog.query.filter_by(
            log_type=LogType.ERROR
        ).filter(
            SchedulerLog.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        if recent_failures > 5:
            issues.append(f"Há um número alto de falhas recentes: {recent_failures} nas últimas 24h")
            status = "error"
        
        return {
            "status": status,
            "issues": issues,
            "timestamp": datetime.utcnow()
        }
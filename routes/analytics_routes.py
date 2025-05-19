from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
import json

from models import Article, ArticleMetrics, ContentDistribution, ContentQualityScore
from app import db

analytics = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics.route('/')
@login_required
def index():
    """Página principal de análise e insights"""
    # Obter todas as métricas de artigos do usuário
    articles = Article.query.filter_by(user_id=current_user.id).all()
    
    # Estatísticas gerais
    total_articles = len(articles)
    published_articles = len([a for a in articles if a.status.value == 'published'])
    total_views = sum([a.metrics.page_views if a.metrics else 0 for a in articles])
    avg_quality = _calculate_avg_quality_score(articles)
    
    # Top artigos por visualizações
    top_articles = sorted(
        [a for a in articles if a.metrics],
        key=lambda x: x.metrics.page_views, 
        reverse=True
    )[:5]
    
    # Dados para gráfico de desempenho dos últimos 7 dias
    performance_data = _generate_performance_data(articles)
    
    # Dados para gráfico de qualidade de conteúdo
    quality_distribution = _calculate_quality_distribution(articles)
    
    return render_template(
        'analytics/index.html',
        total_articles=total_articles,
        published_articles=published_articles,
        total_views=total_views,
        avg_quality=avg_quality,
        top_articles=top_articles,
        performance_data=json.dumps(performance_data),
        quality_distribution=json.dumps(quality_distribution)
    )


@analytics.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    """Página de análise detalhada de um único artigo"""
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    
    # Obter métricas - criar objeto padrão se não existir
    metrics = article.metrics
    if not metrics:
        metrics = ArticleMetrics(article_id=article.id)
        db.session.add(metrics)
        db.session.commit()
    
    # Distribuição em redes sociais
    social_distributions = ContentDistribution.query.filter_by(article_id=article.id).all()
    
    # Dados para gráfico de visualizações ao longo do tempo - simulado para demonstração
    date_views = _generate_daily_views_data(article)
    
    # Dados para gráfico de engajamento por plataforma - simulado para demonstração
    platform_engagement = _generate_platform_engagement(social_distributions)
    
    # Sugestões de melhoria com base nos dados
    improvement_suggestions = _generate_improvement_suggestions(article, metrics)
    
    return render_template(
        'analytics/article_detail.html',
        article=article,
        metrics=metrics,
        social_distributions=social_distributions,
        date_views=json.dumps(date_views),
        platform_engagement=json.dumps(platform_engagement),
        improvement_suggestions=improvement_suggestions
    )


@analytics.route('/update-metrics/<int:article_id>', methods=['POST'])
@login_required
def update_metrics(article_id):
    """API para atualizar manualmente as métricas de um artigo"""
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    
    # Obter ou criar métricas para o artigo
    metrics = ArticleMetrics.query.filter_by(article_id=article.id).first()
    if not metrics:
        metrics = ArticleMetrics(article_id=article.id)
        db.session.add(metrics)
    
    # Atualizar campos com dados do formulário
    form_data = request.form
    
    try:
        # Métricas básicas
        metrics.page_views = int(form_data.get('page_views', metrics.page_views))
        metrics.unique_visitors = int(form_data.get('unique_visitors', metrics.unique_visitors))
        metrics.avg_time_on_page = float(form_data.get('avg_time_on_page', metrics.avg_time_on_page))
        
        # Métricas de engajamento
        metrics.social_shares = int(form_data.get('social_shares', metrics.social_shares))
        metrics.comments = int(form_data.get('comments', metrics.comments))
        metrics.likes = int(form_data.get('likes', metrics.likes))
        
        # Atualizar timestamp
        metrics.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash('Métricas atualizadas com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar métricas: {str(e)}', 'danger')
    
    return redirect(url_for('analytics.article_detail', article_id=article.id))


@analytics.route('/seo-analysis/<int:article_id>')
@login_required
def seo_analysis(article_id):
    """Página de análise SEO detalhada para um artigo"""
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    
    # Análise de densidade de palavras-chave
    keyword_analysis = _analyze_keyword_density(article)
    
    # Sugestões de links internos
    internal_link_suggestions = _suggest_internal_links(article)
    
    # Avaliação geral de SEO
    seo_evaluation = _evaluate_seo_score(article)
    
    return render_template(
        'analytics/seo_analysis.html',
        article=article,
        keyword_analysis=keyword_analysis,
        internal_link_suggestions=internal_link_suggestions,
        seo_evaluation=seo_evaluation
    )


@analytics.route('/report')
@login_required
def performance_report():
    """Gerar relatório de desempenho para todos os artigos"""
    # Período do relatório
    period = request.args.get('period', 'weekly')
    if period == 'monthly':
        start_date = datetime.utcnow() - timedelta(days=30)
        title = "Relatório Mensal de Desempenho"
    else:  # weekly default
        start_date = datetime.utcnow() - timedelta(days=7)
        title = "Relatório Semanal de Desempenho"
    
    # Obter artigos publicados no período
    articles = Article.query.filter(
        Article.user_id == current_user.id,
        Article.status.value == 'published',
        Article.created_at >= start_date
    ).all()
    
    # Calcular métricas gerais
    total_views = sum([a.metrics.page_views if a.metrics else 0 for a in articles])
    total_engagement = sum([
        (a.metrics.social_shares + a.metrics.comments + a.metrics.likes) if a.metrics else 0 
        for a in articles
    ])
    
    return render_template(
        'analytics/report.html',
        title=title,
        period=period,
        start_date=start_date,
        articles=articles,
        total_views=total_views,
        total_engagement=total_engagement
    )


# Funções auxiliares para cálculos de métricas e estatísticas

def _calculate_avg_quality_score(articles):
    """Calcular pontuação de qualidade média dos artigos"""
    articles_with_metrics = [a for a in articles if a.metrics and a.metrics.quality_score]
    if not articles_with_metrics:
        return "N/A"
    
    # Mapeamento de enum para valor numérico
    score_map = {
        ContentQualityScore.LOW: 25,
        ContentQualityScore.MEDIUM: 50,
        ContentQualityScore.HIGH: 75,
        ContentQualityScore.EXCELLENT: 100
    }
    
    total = sum([score_map[a.metrics.quality_score] for a in articles_with_metrics])
    return f"{total / len(articles_with_metrics):.1f}/100"


def _calculate_quality_distribution(articles):
    """Calcular distribuição de pontuações de qualidade"""
    distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "excellent": 0
    }
    
    for article in articles:
        if article.metrics and article.metrics.quality_score:
            distribution[article.metrics.quality_score.value] += 1
    
    # Formatado para gráfico
    return {
        "labels": ["Baixa", "Média", "Alta", "Excelente"],
        "data": [
            distribution["low"],
            distribution["medium"],
            distribution["high"],
            distribution["excellent"]
        ]
    }


def _generate_performance_data(articles):
    """Gerar dados de desempenho para gráficos"""
    # Para demonstração, gerar dados simulados dos últimos 7 dias
    dates = []
    views = []
    engagement = []
    
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=6-i)
        dates.append(date.strftime("%d/%m"))
        
        # Simular dados para demonstração
        daily_views = random.randint(100, 500)
        daily_engagement = random.randint(10, 100)
        
        views.append(daily_views)
        engagement.append(daily_engagement)
    
    return {
        "dates": dates,
        "views": views,
        "engagement": engagement
    }


def _generate_daily_views_data(article):
    """Gerar dados simulados de visualizações diárias para um artigo"""
    dates = []
    views = []
    
    # Simulação de 14 dias de dados
    for i in range(14):
        date = datetime.utcnow() - timedelta(days=13-i)
        dates.append(date.strftime("%d/%m"))
        
        # Visualizações diárias aumentando com o tempo, com algumas flutuações aleatórias
        daily_views = max(0, int((i * 1.5) + random.randint(-3, 5)))
        views.append(daily_views)
    
    return {
        "dates": dates,
        "views": views
    }


def _generate_platform_engagement(distributions):
    """Gerar dados de engajamento por plataforma (simulado)"""
    platforms = [d.platform for d in distributions]
    
    # Se não houver distribuições, criar dados simulados
    if not platforms:
        platforms = ["facebook", "twitter", "linkedin"]
    
    engagement_data = {}
    
    for platform in set(platforms):
        # Simular dados para demonstração
        engagement_data[platform] = {
            "impressions": random.randint(100, 1000),
            "clicks": random.randint(5, 100),
            "shares": random.randint(1, 20)
        }
    
    return engagement_data


def _generate_improvement_suggestions(article, metrics):
    """Gerar sugestões de melhoria com base nos dados do artigo"""
    suggestions = []
    
    # Verificar comprimento do artigo
    word_count = article.word_count or 0
    if word_count < 700:
        suggestions.append({
            "type": "content",
            "title": "Aumentar comprimento do conteúdo",
            "description": "Artigos mais longos (1000+ palavras) geralmente têm melhor desempenho em SEO."
        })
    
    # Verificar densidade de palavras-chave
    if metrics.keyword_density and (metrics.keyword_density < 0.5 or metrics.keyword_density > 2.5):
        suggestions.append({
            "type": "seo",
            "title": "Otimizar densidade de palavras-chave",
            "description": "A densidade ideal é entre 0.5% e 2.5%. Ajuste o uso de sua palavra-chave principal."
        })
    
    # Verificar métricas de engajamento
    if metrics.bounce_rate and metrics.bounce_rate > 70:
        suggestions.append({
            "type": "engagement",
            "title": "Reduzir taxa de rejeição",
            "description": "Sua taxa de rejeição está alta. Adicione links internos e CTAs mais fortes."
        })
    
    # Sugestões para mídias
    if not article.has_custom_images:
        suggestions.append({
            "type": "media",
            "title": "Adicionar imagens personalizadas",
            "description": "Artigos com imagens personalizadas têm 94% mais visualizações."
        })
    
    if not article.has_infographic:
        suggestions.append({
            "type": "media",
            "title": "Incluir infográfico",
            "description": "Infográficos são compartilhados 3x mais que outros tipos de conteúdo."
        })
    
    # Se não houver sugestões específicas, adicionar uma genérica
    if not suggestions:
        suggestions.append({
            "type": "general",
            "title": "Promover nas redes sociais",
            "description": "Seu conteúdo está bom! Tente promovê-lo mais nas redes sociais para aumentar o alcance."
        })
    
    return suggestions


def _analyze_keyword_density(article):
    """Analisar densidade de palavras-chave no artigo"""
    keyword_analysis = {
        "main_keyword": article.focus_keyword or article.keyword or "",
        "secondary_keywords": []
    }
    
    # Verificar se temos a palavra-chave principal
    if not keyword_analysis["main_keyword"]:
        return {
            "main_keyword": "",
            "density": 0,
            "occurrences": 0,
            "status": "missing",
            "secondary_keywords": []
        }
    
    # Contar ocorrências (simulado para demonstração)
    content_text = article.content.lower()
    word_count = len(content_text.split())
    
    # Contar ocorrências da palavra-chave principal
    main_keyword_lower = keyword_analysis["main_keyword"].lower()
    occurrences = content_text.count(main_keyword_lower)
    
    # Calcular densidade
    density = (occurrences * len(main_keyword_lower.split())) / max(1, word_count) * 100
    
    # Adicionar palavras-chave secundárias
    if article.secondary_keywords:
        for kw in article.secondary_keywords.split(','):
            kw = kw.strip().lower()
            if kw:
                kw_occurrences = content_text.count(kw)
                kw_density = (kw_occurrences * len(kw.split())) / max(1, word_count) * 100
                
                keyword_analysis["secondary_keywords"].append({
                    "keyword": kw,
                    "occurrences": kw_occurrences,
                    "density": round(kw_density, 2)
                })
    
    # Determinar status da densidade
    status = "optimal"
    if density < 0.5:
        status = "low"
    elif density > 2.5:
        status = "high"
    
    return {
        "main_keyword": keyword_analysis["main_keyword"],
        "density": round(density, 2),
        "occurrences": occurrences,
        "status": status,
        "secondary_keywords": keyword_analysis["secondary_keywords"]
    }


def _suggest_internal_links(article):
    """Sugerir links internos para outros artigos relevantes"""
    suggestions = []
    
    # Obter artigos do mesmo usuário, excluindo o atual
    user_articles = Article.query.filter(
        Article.user_id == current_user.id,
        Article.id != article.id,
        Article.status.value == 'published'
    ).limit(10).all()
    
    main_keyword = article.focus_keyword or article.keyword or ""
    
    if main_keyword:
        # Encontrar artigos relacionados por palavras-chave
        for other_article in user_articles:
            other_keyword = other_article.focus_keyword or other_article.keyword or ""
            score = 0
            
            # Verificar keywords
            if other_keyword and (main_keyword.lower() in other_keyword.lower() or 
                                 other_keyword.lower() in main_keyword.lower()):
                score += 3
            
            # Verificar título
            if main_keyword.lower() in other_article.title.lower():
                score += 2
            
            # Verificar tags
            if article.tags and other_article.tags:
                article_tags = set([t.strip().lower() for t in article.tags.split(',')])
                other_tags = set([t.strip().lower() for t in other_article.tags.split(',')])
                common_tags = article_tags.intersection(other_tags)
                score += len(common_tags)
            
            if score > 0:
                suggestions.append({
                    "article_id": other_article.id,
                    "title": other_article.title,
                    "relevance_score": score,
                    "url": url_for('dashboard.article_detail', article_id=other_article.id)
                })
    
    # Ordenar por relevância
    suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
    return suggestions


def _evaluate_seo_score(article):
    """Avaliar pontuação SEO geral do artigo"""
    score = 0
    max_score = 100
    evaluation = {}
    
    # Título (20 pontos)
    title_score = min(20, len(article.title) / 2)  # 1 ponto por caractere, até 20
    evaluation["title"] = {
        "score": round(title_score, 1),
        "max": 20,
        "feedback": "Título bom" if title_score >= 15 else "Título muito curto"
    }
    score += title_score
    
    # Meta descrição (15 pontos)
    meta_score = 0
    if article.meta_description:
        meta_length = len(article.meta_description)
        if meta_length >= 120 and meta_length <= 156:
            meta_score = 15  # Comprimento ótimo
        else:
            meta_score = max(0, 15 - abs(meta_length - 138) / 10)  # Penalizar por afastamento do ideal
    
    evaluation["meta_description"] = {
        "score": round(meta_score, 1),
        "max": 15,
        "feedback": "Meta descrição ideal" if meta_score >= 12 else "Meta descrição ausente ou com comprimento inadequado"
    }
    score += meta_score
    
    # Palavra-chave no conteúdo (15 pontos)
    keyword_score = 0
    if article.focus_keyword or article.keyword:
        kw = (article.focus_keyword or article.keyword).lower()
        # Verificar se a palavra-chave está no título
        if kw in article.title.lower():
            keyword_score += 5
        
        # Verificar densidade (simulado)
        content_text = article.content.lower()
        occurrences = content_text.count(kw)
        word_count = len(content_text.split())
        density = (occurrences * len(kw.split())) / max(1, word_count) * 100
        
        if density >= 0.5 and density <= 2.5:
            keyword_score += 10
        elif density > 0:
            keyword_score += 5
    
    evaluation["keyword_usage"] = {
        "score": round(keyword_score, 1),
        "max": 15,
        "feedback": "Uso adequado da palavra-chave" if keyword_score >= 10 else "Melhorar o uso da palavra-chave no conteúdo"
    }
    score += keyword_score
    
    # Comprimento do conteúdo (20 pontos)
    content_score = 0
    word_count = article.word_count or 0
    if word_count >= 1500:
        content_score = 20
    elif word_count >= 1000:
        content_score = 15
    elif word_count >= 700:
        content_score = 10
    elif word_count >= 400:
        content_score = 5
    
    evaluation["content_length"] = {
        "score": round(content_score, 1),
        "max": 20,
        "feedback": "Conteúdo com boa extensão" if content_score >= 15 else "Conteúdo curto, considere expandir"
    }
    score += content_score
    
    # Links internos e externos (15 pontos)
    link_score = 0
    internal_links = article.internal_links_count or 0
    external_links = article.external_links_count or 0
    
    if internal_links >= 3:
        link_score += 10
    elif internal_links > 0:
        link_score += 5
    
    if external_links >= 2:
        link_score += 5
    elif external_links > 0:
        link_score += 2
    
    evaluation["links"] = {
        "score": round(link_score, 1),
        "max": 15,
        "feedback": "Boa estrutura de links" if link_score >= 10 else "Adicionar mais links internos e externos"
    }
    score += link_score
    
    # Imagens e mídia (15 pontos)
    media_score = 0
    has_featured = bool(article.featured_image_url)
    has_custom = article.has_custom_images
    has_infographic = article.has_infographic
    
    if has_featured:
        media_score += 5
    if has_custom:
        media_score += 5
    if has_infographic:
        media_score += 5
    
    evaluation["media"] = {
        "score": round(media_score, 1),
        "max": 15,
        "feedback": "Bom uso de mídias" if media_score >= 10 else "Adicionar mais imagens e mídias"
    }
    score += media_score
    
    # Resultado final
    final_score = round(score, 1)
    if final_score >= 80:
        grade = "A"
        status = "excellent"
    elif final_score >= 60:
        grade = "B"
        status = "good"
    elif final_score >= 40:
        grade = "C"
        status = "average"
    else:
        grade = "D"
        status = "poor"
    
    return {
        "score": final_score,
        "max_score": max_score,
        "grade": grade,
        "status": status,
        "evaluation": evaluation
    }
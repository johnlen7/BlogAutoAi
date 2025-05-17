import logging
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

automation_bp = Blueprint('automation', __name__, url_prefix='/automation')

@automation_bp.route('/', methods=['GET'])
@login_required
def index():
    """Página inicial de automação - placeholder durante desenvolvimento"""
    return render_template('automation/placeholder.html')

@automation_bp.route('/themes', methods=['GET'])
@login_required
def themes_list():
    """Lista de temas para automação - redirecionando para placeholder"""
    flash('As funcionalidades de automação de temas estão em desenvolvimento.', 'info')
    return redirect(url_for('automation.index'))

@automation_bp.route('/feeds', methods=['GET'])
@login_required
def feeds_list():
    """Lista de feeds RSS - redirecionando para placeholder"""
    flash('As funcionalidades de feeds RSS estão em desenvolvimento.', 'info')
    return redirect(url_for('automation.index'))
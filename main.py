from app import app  # noqa: F401
from flask import request, session, redirect, url_for

@app.route('/set_language/<lang>')
def set_language(lang):
    """Set the user's preferred language"""
    # Store language preference in session
    session['language'] = lang
    # Redirect back to previous page
    return redirect(request.referrer or url_for('dashboard.index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

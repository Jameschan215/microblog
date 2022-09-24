from flask import render_template
from app import db
from app.errors import bp


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('/errors/404.html'), 404


# The error handler for the 500 errors could be invoked after a database error,
# which was actually the case with the username duplicate above. To make sure any
# failed database sessions do not interfere with any database accesses triggered by
# the template, I issue a session rollback. This resets the session to a clean state.
@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('/errors/500.html'), 500



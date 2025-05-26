# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

from flask import render_template
from app import db
from app.errors import bp
import os

ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "realiselab@gmail.com")

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html", admin_emails=ADMIN_EMAILS), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html", admin_emails=ADMIN_EMAILS), 500

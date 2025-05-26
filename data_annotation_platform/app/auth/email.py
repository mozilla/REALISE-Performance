# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

from flask import current_app, render_template

from app.email import send_email
import os

DNS_NAME = os.getenv("DNS_NAME", "localhost")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "realiselab@gmail.com")

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        "[AnnotateChange] Reset your password",
        sender=current_app.config["MAIL_FROM"],
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt", user=user, token=token, dns_name=DNS_NAME, admin_emails=ADMIN_EMAILS
        ),
        html_body=render_template(
            "email/reset_password.html", user=user, token=token, dns_name=DNS_NAME, admin_emails=ADMIN_EMAILS
        ),
    )


def send_email_confirmation_email(user):
    token = user.get_email_confirmation_token()
    send_email(
        "[AnnotateChange] Confirm your email",
        sender=current_app.config["MAIL_FROM"],
        recipients=[user.email],
        text_body=render_template(
            "email/confirm_email.txt", user=user, token=token, dns_name=DNS_NAME, admin_emails=ADMIN_EMAILS
        ),
        html_body=render_template(
            "email/confirm_email.html", user=user, token=token, dns_name=DNS_NAME, admin_emails=ADMIN_EMAILS
        ),
    )

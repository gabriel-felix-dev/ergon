"""Ponto de entrada WSGI para Cloudflare Python Workers."""

from workers import wsgi

from app import app

Default = wsgi.entrypoint(app)

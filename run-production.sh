#!/bin/sh

gunicorn questions.wsgi -b :8000 --workers 16
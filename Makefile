SHELL=/bin/bash

all: messages compile-messages

messages: venv
	django-admin makemessages --ignore venv -a

compile-messages: venv
	django-admin compilemessages --ignore venv

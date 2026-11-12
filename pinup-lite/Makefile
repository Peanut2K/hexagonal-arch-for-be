.PHONY: dev up down build logs sh restart

DC ?= $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo docker-compose)

dev:     ## start in foreground with logs; Ctrl-C stops and runs down
	trap true INT; $(DC) up --build; $(DC) down
up:      ## start dev server (hot reload) on :8000
	$(DC) up -d --build
down:    ## stop
	$(DC) down
build:   ## rebuild image (after changing requirements.txt)
	$(DC) build
logs:    ## follow logs
	$(DC) logs -f api
sh:      ## shell into container
	$(DC) exec api bash
restart: ## restart container
	$(DC) restart api

up:
	docker compose build --no-cache && docker compose up -d 

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

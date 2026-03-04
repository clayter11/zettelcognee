.PHONY: up down test logs reset ui

# Start everything (backend + db + redis + UI)
up:
	docker compose up --build -d
	@echo ""
	@echo "✅ Готово!"
	@echo "  API:  http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  UI:   http://localhost:8501"
	@echo ""

# Stop everything
down:
	docker compose down

# Run tests (locally, without docker)
test:
	cd backend && python -m pytest tests/ -v

# View logs
logs:
	docker compose logs -f backend ui

# Full reset — drop volumes, rebuild
reset:
	docker compose down -v
	docker compose up --build -d

# Open UI in browser
ui:
	open http://localhost:8501

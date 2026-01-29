# Colors
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
CYAN := \033[1;36m
ORANGE := \033[0;33m
PURPLE := \033[1;35m
WHITE := \033[1;37m
NC := \033[0m

# Variables
IMAGE_FULLNAME = "zaphiro_fastapi:poc"

#################################################
# SYSTEM UTILITY
#################################################
.PHONY: clean  ## Clear local caches and artifacts
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .pytest_cache
	rm -rf .ruff_cache

#################################################
# UV UTILITY
#################################################
.PHONY: lint ## Lint Python source files
lint:
	uv run ruff check --fix

.PHONY: format ## Format Python source files
format:
	uv run ruff format

.PHONY: test ## Run the Python test suite
test:
	uv run pytest -v

.PHONY: check ## Type check Python source files
check:
	uv run pyrefly check

#################################################
# DOCKER UTILITY
#################################################
.PHONY: docker-build
docker-build: ## Build a docker image
	@echo -e "${YELLOW}building docker image...${NC}"
	docker build -t ${IMAGE_FULLNAME} -f Dockerfile .
	docker system prune -f
	@echo -e "${GREEN}build done${NC}"

.PHONY: docker-run ## Run a docker container
docker-run:
	@echo -e "${YELLOW}starting docker container...${NC}"
	docker run --rm -it -p 8080:8000 ${IMAGE_FULLNAME}
	@echo -e "${GREEN}done${NC}"

.PHONY: docker-build-push ## Build and run a docker container
docker-build-push: docker-build docker-push

#################################################
# HELPER
#################################################
.PHONY: help ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'
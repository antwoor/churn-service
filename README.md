# Dino diet service

Сервис предсказывает, был ли динозавр хищником (`carnivorous`), по типу, длине, геологическому периоду и региону находки.

Данные: [Jurassic Park — The Exhaustive Dinosaur Dataset](https://www.kaggle.com/datasets/kjanjua/jurassic-park-the-exhaustive-dinosaur-dataset) (Kaggle / каталог NHM). 

Обучение: `notebooks/train_dino_diet.ipynb`. Артефакт: `artifact/model.joblib` (pipeline + metadata).

Отчёт к ДЗ: [docs/REPORT.md](docs/REPORT.md).

## Проверка

Для запуска выполните три команды

### 1. Тесты

```bash
uv sync --frozen
uv run pytest
```

### 2. Docker Compose

```bash
docker compose up -d --build
curl -s -X POST localhost:8000/v1/predict -H "Content-Type: application/json" -d @good.json
docker compose exec db psql -U postgres -d dino -c "SELECT request_id, score, status_code, latency_ms, features FROM predictions;"
```

### 3. Kind

```bash
docker build -t dino-service:1.0 .
kind create cluster --name mlpro
kind load docker-image dino-service:1.0 --name mlpro
kubectl create secret generic dino-secrets \
  --from-literal=POSTGRES_PASSWORD=postgres \
  --from-literal=DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dino
kubectl apply -f k8s/
kubectl rollout status deploy/postgres --timeout=180s
kubectl rollout status deploy/dino-service --timeout=120s
kubectl port-forward svc/dino-service 8080:80
```

В другом терминале:

```bash
curl -s -X POST localhost:8080/v1/predict -H "Content-Type: application/json" -d @good.json
kubectl get pods
```

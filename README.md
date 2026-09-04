# Pi Dashboard

Pi Dashboard is a small FastAPI app that shows a live overview of Docker containers on the host. It polls the Docker daemon, calculates CPU and memory usage, and renders the results in a simple browser dashboard.

## Features

- Live container list with name, status, CPU %, and memory %
- Automatic refresh of container stats every 3 seconds
- Clickable container cards when a `url` label is present on the container
- Simple, responsive HTML dashboard with no frontend build step

## Requirements

- Python 3.14+
- Docker Engine running locally or remotely
- Access to the Docker daemon from the process running the app

## Configuration

The app does not require environment variables for basic use.

- `PORT` controls the HTTP port when running the Docker image. Default: `8000`
- Containers can expose a link by setting the Docker label `url`

## Running locally

For local development, use the FastAPI CLI if it is available:

```bash
fastapi dev main.py
```

If you prefer running the ASGI app directly, use Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

### Running with Docker

Build and run the image:

```bash
docker build -t pi-dashboard .
docker run --rm -p 8000:8000 -e PORT=8000 -v /var/run/docker.sock:/var/run/docker.sock pi-dashboard
```

The container must be able to talk to the Docker daemon it is monitoring. On Linux, mounting `/var/run/docker.sock` is the simplest option.

## How it works

- `main.py` connects to Docker with `docker.from_env()`
- A background task refreshes container stats in memory
- The `/` route renders `templates/index.html`

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import docker
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

docker_client = docker.from_env()


def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
        print(json.dumps(stats, indent=4))

        memory = None
        try:
            if (
                "memory_stats" in stats
                and "usage" in stats["memory_stats"]
                and "limit" in stats["memory_stats"]
            ):
                used_memory = (
                    stats["memory_stats"]["usage"]
                    - stats["memory_stats"]["stats"]["inactive_file"]
                )
                memory = used_memory / stats["memory_stats"]["limit"] * 100
        except KeyError as e:
            print(
                f"KeyError while calculating memory usage for container {container.name}: {e}"
            )
            memory = None

        cpu = None
        try:
            if "cpu_stats" in stats and "cpu_usage" in stats["cpu_stats"]:
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_cpu_delta = (
                    stats["cpu_stats"]["system_cpu_usage"]
                    - stats["precpu_stats"]["system_cpu_usage"]
                )
                number_cpus = stats["cpu_stats"]["online_cpus"]
                cpu = (
                    (cpu_delta / system_cpu_delta) * number_cpus * 100
                    if system_cpu_delta > 0
                    else 0
                )
        except KeyError as e:
            print(
                f"KeyError while calculating CPU usage for container {container.name}: {e}"
            )
            cpu = None

        return {
            "name": container.name,
            "url": container.labels.get("url", None),
            "status": container.status,
            "memory": memory,
            "cpu": cpu,
        }
    except Exception as e:
        print(f"Error getting stats for container {container.name}: {e}")
        return None


def get_all_container_stats():
    all_containers = docker_client.containers.list(all=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_container_stats, all_containers)
        return [res for res in results if res is not None]


containers = []


async def update_stats_bg():
    global containers
    while True:
        containers = await asyncio.to_thread(get_all_container_stats)
        print("Updated container stats.")
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(update_stats_bg())
    yield
    task.cancel()


templates = Jinja2Templates(directory="templates")
app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"containers": containers},
    )

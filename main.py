import json

import docker
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

docker_client = docker.from_env()

templates = Jinja2Templates(directory="templates")
app = FastAPI()


def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
        print(json.dumps(stats, indent=4))

        memory = None
        try:
            if "memory_stats" in stats and "usage" in stats["memory_stats"] and "limit" in stats["memory_stats"]:
                used_memory = (
                    stats["memory_stats"]["usage"]
                    - stats["memory_stats"]["stats"]["inactive_file"]
                )
                memory = used_memory / stats["memory_stats"]["limit"] * 100
        except KeyError as e:
            print(f"KeyError while calculating memory usage for container {container.name}: {e}")
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
            print(f"KeyError while calculating CPU usage for container {container.name}: {e}")
            cpu = None

        return {
            "name": container.name,
            "status": container.status,
            "memory": memory,
            "cpu": cpu,
        }
    except Exception as e:
        print(f"Error getting stats for container {container.name}: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    containers = docker_client.containers.list(all=True)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"containers": [get_container_stats(c) for c in containers]},
    )

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
        used_memory = (
            stats["memory_stats"]["usage"]
            - stats["memory_stats"]["stats"]["inactive_file"]
        )

        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_cpu_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        number_cpus = stats["cpu_stats"]["online_cpus"]
        return {
            "name": container.name,
            "status": container.status,
            "memory": used_memory / stats["memory_stats"]["limit"] * 100,
            "cpu": (
                (cpu_delta / system_cpu_delta) * number_cpus * 100
                if system_cpu_delta > 0
                else 0
            ),
        }
    except Exception as e:
        return None


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    containers = docker_client.containers.list(all=True)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"containers": [get_container_stats(c) for c in containers]},
    )

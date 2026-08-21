import docker
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

docker_client = docker.from_env()

templates = Jinja2Templates(directory="templates")
app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    containers = docker_client.containers.list(all=True)
    return templates.TemplateResponse(
        request=request, name="index.html", context={"containers": [c.name for c in containers]}
    )

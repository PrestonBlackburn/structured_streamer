from python_on_whales import docker
import requests
import pytest
from pytest import fixture
import logging
import time

_logger = logging.getLogger(__name__)


@fixture(scope="module")
def fastapi_env():
    # expect to run from project root
    env = {
        "path": "./tests/app",
        "image_name": "struct_strm_server",
        "container_name": "struct_strm_server",
        "port": "8000",
    }

    return env


@fixture(scope="module")
def build_fastapi_image(fastapi_env):
    # potentially may just keep a build of this in gh later

    docker.build("./", file="tests/02_app/Dockerfile", tags="struct_strm_server:latest")
    yield True


@fixture(scope="module")
def start_fastapi(build_fastapi_image, fastapi_env):
    # we'll get images from gh or local
    env = fastapi_env
    container_name = env["container_name"]
    docker.run(
        f"{env['image_name']}:latest",
        name=container_name,
        publish=[(env["port"], env["port"])],
        detach=True,
        remove=True,
    )
    yield True
    docker.stop(container_name)


@fixture(scope="module")
def wait_for_fastapi(start_fastapi, fastapi_env):
    env = fastapi_env
    container_name = env["container_name"]
    # includes build time
    timeout = 30
    while timeout > 0:
        try:
            r = requests.get(f"http://localhost:{fastapi_env['port']}", timeout=1)
            _logger.debug(r.text)
            if r.status_code == 200:
                break
        except Exception as e:
            _logger.error(e)
            pass
        timeout -= 1
        time.sleep(1)
    if timeout == 0:
        pytest.fail("FastAPI did not become available within the timeout")

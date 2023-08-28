import pytest
import platform
import asyncio
from typing import Any
from pytest_docker.plugin import Services  # pyright: ignore


@pytest.fixture(scope="session")
def docker_compose_command() -> str:
    return "docker-compose"


@pytest.fixture(scope="session")
def redis_basic_server(docker_ip: str, docker_services: Services):
    port: Any = docker_services.port_for("redis-basic", 6379)  # pyright: ignore
    yield (docker_ip, port)


@pytest.fixture(scope="session")
def redis_uds_server(docker_services: Services):
    if platform.system().lower() == "darwin":
        pytest.skip("Fixture not supported on OSX")
    docker_services.port_for("redis-uds", 6379)  # pyright: ignore
    yield "/tmp/aiorediantic.redis.sock"


@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop

    for task in [t for t in asyncio.all_tasks(loop) if not (t.done() or t.cancelled())]:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except:  # noqa
            pass
    loop.close()

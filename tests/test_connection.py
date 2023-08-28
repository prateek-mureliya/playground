from __future__ import annotations

import socket
import pytest

from typing import Tuple, Any
from asyncio import AbstractEventLoop
from playground.connection import Connection, UnixDomainSocketConnection
from coredis.exceptions import TimeoutError

pytest_marks = pytest.mark.asyncio


async def test_connect_tcp(redis_basic_server: Tuple[str, int]):
    conn = Connection()
    assert conn.host == "127.0.0.1"
    assert conn.port == 6379
    assert str(conn) == "Connection<host=127.0.0.1,port=6379,db=0>"
    request = await conn.create_request(b"PING")
    res = await request
    assert res == b"PONG"
    assert conn._transport is not None  # pyright: ignore
    conn.disconnect()
    assert conn._transport is None  # pyright: ignore


@pytest.mark.os("linux")
async def test_connect_tcp_keepalive_options(redis_basic_server: Tuple[str, int]):
    conn = Connection(
        socket_keepalive=True,
        socket_keepalive_options={
            socket.TCP_KEEPIDLE: 1,
            socket.TCP_KEEPINTVL: 1,
            socket.TCP_KEEPCNT: 3,
        },
    )
    await conn._connect()  # pyright: ignore
    sock = conn._transport.get_extra_info("socket")  # pyright: ignore
    assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) == 1
    for k, v in (
        (socket.TCP_KEEPIDLE, 1),
        (socket.TCP_KEEPINTVL, 1),
        (socket.TCP_KEEPCNT, 3),
    ):
        assert sock.getsockopt(socket.SOL_TCP, k) == v
    conn.disconnect()


@pytest.mark.parametrize("option", ["UNKNOWN", 999])
async def test_connect_tcp_wrong_socket_opt_raises(
    event_loop: AbstractEventLoop, option: Any, redis_basic_server: Tuple[str, int]
):
    conn = Connection(socket_keepalive=True, socket_keepalive_options={option: 1})
    with pytest.raises((socket.error, TypeError)):
        await conn._connect()  # pyright: ignore
    # verify that the connection isn't left open
    assert conn._transport.is_closing()  # pyright: ignore


# only test during dev
async def test_connect_unix_socket(redis_uds_server: str):
    path = redis_uds_server
    conn = UnixDomainSocketConnection(path)
    await conn.connect()
    assert conn.path == path
    assert str(conn) == f"UnixDomainSocketConnection<path={path},db=0>"
    req = await conn.create_request(b"PING")
    res = await req
    assert res == b"PONG"
    assert conn._transport is not None  # pyright: ignore
    conn.disconnect()
    assert conn._transport is None  # pyright: ignore


async def test_stream_timeout(redis_basic_server: Tuple[str, int]):
    conn = Connection(stream_timeout=0.01)
    await conn.connect() is None  # pyright: ignore
    req = await conn.create_request(b"debug", "sleep", 0.05)
    with pytest.raises(TimeoutError):
        await req


# async def test_lag(redis_basic_server: Tuple[str, int]):
#     connection = await redis_basic.connection_pool.get_connection(b"ping")
#     assert connection.lag == 0
#     ping_request = await connection.create_request(b"ping")
#     assert connection.lag != 0
#     await ping_request
#     assert connection.lag == 0


# async def test_estimated_time_to_idle(redis_basic_server: Tuple[str, int]):
#     connection = await redis_basic.connection_pool.get_connection(b"ping")
#     assert connection.estimated_time_to_idle == 0
#     requests = [await connection.create_request(b"ping") for _ in range(10)]
#     assert connection.estimated_time_to_idle > 0
#     await asyncio.gather(*requests)
#     assert connection.estimated_time_to_idle == 0

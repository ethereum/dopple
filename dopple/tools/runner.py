import logging
import pathlib
import socket
import tempfile
import time
from typing import AsyncIterator, Callable

import trio

try:
    from contextlib import asynccontextmanager
except ImportError:
    # We use this as a fallback to support Python 3.6
    from async_generator import asynccontextmanager  # type: ignore


DOPPLE_FILE = pathlib.Path(__file__).parent.parent / "dopple.py"


@asynccontextmanager
async def run_eth_client_in_docker(
    generate_cmd_fn: Callable[[pathlib.Path], str],
    generate_ipc_path_fn: Callable[[pathlib.Path], pathlib.Path],
) -> AsyncIterator[pathlib.Path]:
    """
    Create an ``asynccontextmanager`` that runs an Ethereum client within docker
    under the user account of the host user. A temporary directory is created on
    the host system and should be mapped into the docker container to allow the
    client to share IPC files with the host system. Yield the IPC path of the client.

    :param generate_cmd_fn: A function taking the ``Path`` of the temporary directory
    and generating the relevant part of the docker command to launch the client with
    the mapped directory.

    :param generate_ipc_path_fn: A function taking the ``Path`` of the temprorary directory
    and generating the ``Path`` of the IPC file that dopple can connect to.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = pathlib.Path(tmpdir)

        start_cmd = (
            f"docker run --rm --name {temp_dir.name} "
            f"--user $(id -u):$(id -g) {generate_cmd_fn(temp_dir)}"
        )
        stop_cmd = f"docker stop {temp_dir.name}"

        ipc_path = generate_ipc_path_fn(temp_dir)
        logging.debug(f"Starting client, ipc path: {ipc_path}")
        async with await trio.open_process(start_cmd, shell=True):
            logging.debug("Started client, waiting for IPC socket to be ready")
            wait_for_socket(ipc_path)
            logging.debug("IPC ready")
            yield ipc_path
            logging.debug("Killing client")
            await trio.run_process(stop_cmd, shell=True)
            logging.debug("Killed client")


@asynccontextmanager
async def run_dopple_as_script(ipc_path: pathlib.Path) -> AsyncIterator[None]:
    """
    Run geth, then run dopple as a script file to connect to it.
    """
    logging.debug("Starting dopple")
    async with await trio.open_process([DOPPLE_FILE, ipc_path]) as proc:
        logging.debug("Started dopple")
        await trio.sleep(0.5)
        yield
        logging.debug("Terminating dopple")
        proc.terminate()
        await proc.wait()
        logging.debug("Terminated dopple")


def wait_for_socket(ipc_path: pathlib.Path, timeout: int = 10) -> None:
    """
    Wait for the ``ipc_path`` to be ready.
    """
    start = time.monotonic()
    while time.monotonic() < start + timeout:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(ipc_path))
            sock.settimeout(timeout)
        except (FileNotFoundError, socket.error):
            time.sleep(0.01)
        else:
            break

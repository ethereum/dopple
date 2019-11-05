from dopple.tools.runner import run_dopple_as_script, run_eth_client_in_docker
import pytest
import requests

# The following tests invoke dopple as a pure file (as opposed to a package installed through pip)
# and test it's functionality against different clients.


def geth_cmd(tmpdir):
    return (
        f"-v {tmpdir}:/tmp/.ethereum ethereum/client-go:v1.9.6 --datadir /tmp/.ethereum"
    )


def generate_geth_ipc_path(tmpdir):
    return tmpdir / "geth.ipc"


def aleth_cmd(tmpdir):
    return f"-v {tmpdir}:/.ethereum ethereum/aleth:1.6.0"


GETH_LAUNCH_FNS = geth_cmd, generate_geth_ipc_path
# Not a bug, aleth names its IPC file `geth.ipc`
ALETH_LAUNCH_FNS = aleth_cmd, generate_geth_ipc_path

# Test cases *must* follow this order to label each test case to the correct client
TEST_IDS = ("geth", "aleth")


@pytest.mark.parametrize(
    "client_config", (GETH_LAUNCH_FNS, ALETH_LAUNCH_FNS), ids=TEST_IDS
)
@pytest.mark.trio
async def test_run_and_get_info(client_config):
    async with run_eth_client_in_docker(*client_config) as ipc_path:
        async with run_dopple_as_script(ipc_path):
            ret = requests.get("http://127.0.0.1:8545")
            assert str(ipc_path) in ret.text
            assert "connected: True" in ret.text


@pytest.mark.parametrize(
    "client_config", (GETH_LAUNCH_FNS, ALETH_LAUNCH_FNS), ids=TEST_IDS
)
@pytest.mark.trio
async def test_can_request_data(client_config):
    data = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["0x0", True],
        "id": 1,
    }
    async with run_eth_client_in_docker(*client_config) as ipc_path:
        async with run_dopple_as_script(ipc_path):
            ret = requests.post("http://127.0.0.1:8545", json=data)
            # Assert the genesis block hash is in the result
            assert (
                "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
                in ret.text
            )

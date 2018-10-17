# JSON-RPC Proxy

This Python script (found in `scripts/jsonrpcproxy.py`) provides HTTP proxy to Unix Socket based JSON-RPC servers.
Check out --help option for more information.

## Use

```bash
jsonrpcproxy.py --backend_path ~/.ethereum/geth.ipc --proxy_url http://127.0.0.1:8545
```

These values above are the default ones too. If they match your current configuration, they can be ommitted.

## License

Apache-2.0

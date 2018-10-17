# Dopple

This Python script (found in `dopple.py`) provides HTTP proxy to Unix Socket based JSON-RPC servers.
Check out --help option for more information.

## Use

```bash
dopple.py --backend_path ~/.ethereum/geth.ipc --proxy_url http://127.0.0.1:8545
```

These values above are the default ones too. If they match your current configuration, they can be ommitted.

## License

Apache-2.0

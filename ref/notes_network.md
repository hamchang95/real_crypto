![network diagram]()

- This is a Windows setup using Windows Subsystem for Linux (WSL2). 
- Redpanda has two listeners
    - internal listners: job manager & task manager
    - external listner: producer
- Port-wise, 
    - Host port 9092 is mapped to container port 9092.
    - Host port 29092 is mapped to container port 29092.
    - Flink containers reach redpanda:9092 directly inside the Docker network. 
    - The WebSocket producer connects to host port 29092, which Docker forwards to container port 29092.
- With Docker network, containers can reach other without any additional configuration.
- However, specifying expose in `docker-compose.yml adds clarity, signalling which ports other containers are expected to use. 
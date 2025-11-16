import time
from typing import Dict, List, Optional

import docker
from docker.errors import ContainerError, ImageNotFound


def execute_code_in_docker(
    code: str,
    image: str = "python:3.11-slim",
    packages: Optional[List[str]] = None,
    timeout: int = 30,
) -> Dict[str, str]:

    client = docker.from_env()
    
    # Prepare the install command if packages are specified
    install_cmd = ""
    if packages:
        install_cmd = f"pip install --quiet --no-cache-dir {' '.join(packages)} > /dev/null 2>&1 && "
    
    # Full command: install packages (if any) then run the code
    full_command = f'{install_cmd}python -c "{code}"'
    
    try:
        # Pull image if not available locally
        try:
            client.images.get(image)
        except ImageNotFound:
            print(f"Pulling image {image}...")
            client.images.pull(image)
        
        # Run the container
        container = client.containers.run(
            image=image,
            command=["sh", "-c", full_command],
            detach=True,
            remove=False,  # Keep container to get logs even on error
        )
        
        # Wait for container to finish (with timeout)
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            if container.status in ["exited", "dead"]:
                break
            time.sleep(0.5)
        else:
            # Timeout reached
            container.stop(timeout=5)
            container.remove()
            return {
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "exit_code": -1,
            }
        
        # Get logs and exit code
        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        exit_code = container.attrs["State"]["ExitCode"]
        
        # Clean up
        container.remove()
        
        if exit_code == 0:
            return {
                "output": logs,
                "error": "",
                "exit_code": exit_code,
            }
        else:
            return {
                "output": "",
                "error": logs,
                "exit_code": exit_code,
            }
            
    except ContainerError as e:
        return {
            "output": "",
            "error": f"Container error: {str(e)}",
            "exit_code": e.exit_status,
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Unexpected error: {str(e)}",
            "exit_code": -1,
        }


# Example usage / test
if __name__ == "__main__":
    # Test 1: Simple calculation
    print("Test 1: Simple calculation")
    result = execute_code_in_docker(
        code="print('Hello from Docker!'); print(2 + 2)"
    )
    print(f"Output: {result['output']}")
    print(f"Error: {result['error']}")
    print(f"Exit code: {result['exit_code']}")
    print()
    
    # Test 2: With package installation
    print("Test 2: With numpy package")
    result = execute_code_in_docker(
        code="import numpy as np; arr = np.array([1, 2, 3]); print(f'Array: {arr}'); print(f'Sum: {arr.sum()}')",
        packages=["numpy"]
    )
    print(f"Output: {result['output']}")
    print(f"Error: {result['error']}")
    print(f"Exit code: {result['exit_code']}")
    print()
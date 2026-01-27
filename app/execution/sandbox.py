"""Secure Python sandbox execution using Docker."""

import ast
import json
import logging
import tarfile
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import docker
from docker.errors import ContainerError, ImageNotFound
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Dangerous patterns to reject
FORBIDDEN_PATTERNS = {
    "eval",
    "exec",
    "__import__",
    "compile",
    "open",
    "os.system",
    "subprocess",
    "requests",
    "urllib",
    "socket",
    "http.client",
    "ftplib",
    "smtplib",
    "telnetlib",
}

FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "requests",
    "urllib",
    "socket",
    "http",
    "ftplib",
    "smtplib",
    "telnetlib",
    "pickle",
    "marshal",
}


class SandboxResult(BaseModel):
    """Result of sandbox execution."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    output: dict[str, Any] = {}
    execution_time_ms: int = 0
    error: Optional[str] = None


class CodeValidator:
    """Validates Python code for security issues before execution."""

    @staticmethod
    def validate(code: str) -> tuple[bool, Optional[str]]:
        """Validate Python code for dangerous patterns.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for forbidden patterns in raw code
        code_lower = code.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in code_lower:
                return False, f"Forbidden pattern detected: {pattern}"

        # Parse and analyze AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                        return False, f"Forbidden module import: {alias.name}"

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
                    return False, f"Forbidden module import: {node.module}"

            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in {"eval", "exec", "compile", "open"}:
                        return False, f"Forbidden function call: {node.func.id}"

                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"system", "popen", "spawn"}:
                        return False, f"Forbidden method call: {node.func.attr}"

        return True, None


class SecureSandbox:
    """Secure Python execution sandbox using Docker."""

    SANDBOX_IMAGE = "analytics-sandbox:latest"
    FALLBACK_IMAGE = "python:3.11-slim"

    def __init__(
        self,
        timeout: int = 30,
        memory_limit: str = "512m",
        cpu_quota: int = 50000,
    ):
        """Initialize the sandbox.

        Args:
            timeout: Maximum execution time in seconds
            memory_limit: Container memory limit (e.g., '512m')
            cpu_quota: CPU quota (50000 = 50%)
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota
        self.validator = CodeValidator()

        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            logger.warning(f"Docker not available: {e}")
            self.client = None

    def _ensure_image(self) -> str:
        """Ensure sandbox image exists, fall back to base Python if needed."""
        if not self.client:
            raise RuntimeError("Docker client not available")

        try:
            self.client.images.get(self.SANDBOX_IMAGE)
            return self.SANDBOX_IMAGE
        except ImageNotFound:
            logger.info(f"Custom image not found, using {self.FALLBACK_IMAGE}")
            try:
                self.client.images.pull(self.FALLBACK_IMAGE)
            except Exception as e:
                logger.error(f"Failed to pull fallback image: {e}")
                raise
            return self.FALLBACK_IMAGE

    def _create_tar_archive(self, files: dict[str, bytes]) -> bytes:
        """Create a tar archive from files dictionary.

        Args:
            files: Dictionary of filename -> content

        Returns:
            Tar archive as bytes
        """
        tar_buffer = BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            for name, content in files.items():
                file_buffer = BytesIO(content)
                tarinfo = tarfile.TarInfo(name=name)
                tarinfo.size = len(content)
                tar.addfile(tarinfo, file_buffer)
        tar_buffer.seek(0)
        return tar_buffer.read()

    def _extract_from_tar(self, tar_bytes: bytes, filename: str) -> Optional[dict]:
        """Extract a file from tar archive.

        Args:
            tar_bytes: Tar archive bytes
            filename: File to extract

        Returns:
            Parsed JSON content or None
        """
        try:
            tar_buffer = BytesIO(tar_bytes)
            with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
                for member in tar.getmembers():
                    if member.name == filename or member.name.endswith(f"/{filename}"):
                        f = tar.extractfile(member)
                        if f:
                            return json.loads(f.read().decode())
        except Exception as e:
            logger.debug(f"Failed to extract {filename}: {e}")
        return None

    def execute(
        self,
        code: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> SandboxResult:
        """Execute Python code in isolated container.

        Args:
            code: Python code to execute
            input_data: Dictionary of data to make available

        Returns:
            SandboxResult with execution details
        """
        start_time = time.time()

        # Validate code first
        is_valid, error = self.validator.validate(code)
        if not is_valid:
            return SandboxResult(
                success=False,
                error=f"Code validation failed: {error}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        if not self.client:
            return SandboxResult(
                success=False,
                error="Docker not available",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Prepare execution script
        exec_script = self._create_execution_script(code)
        input_json = json.dumps(input_data or {}).encode()

        try:
            image = self._ensure_image()

            # Create container
            container = self.client.containers.create(
                image,
                command=["python3", "/workspace/run.py"],
                detach=True,
                network_disabled=True,
                mem_limit=self.memory_limit,
                nano_cpus=self.cpu_quota * 10000,
                read_only=True,
                tmpfs={"/tmp": "size=100M"},
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
            )

            try:
                # Copy files to container
                tar_data = self._create_tar_archive(
                    {
                        "run.py": exec_script.encode(),
                        "input.json": input_json,
                    }
                )
                container.put_archive("/workspace", tar_data)

                # Start execution
                container.start()

                # Wait for completion
                result = container.wait(timeout=self.timeout)
                exit_code = result.get("StatusCode", -1)

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode()
                stderr = container.logs(stdout=False, stderr=True).decode()

                # Try to get output file
                output_data = {}
                try:
                    bits, _ = container.get_archive("/tmp/output.json")
                    tar_content = b"".join(bits)
                    output_data = self._extract_from_tar(tar_content, "output.json") or {}
                except Exception:
                    pass

                execution_time_ms = int((time.time() - start_time) * 1000)

                if exit_code == 0:
                    return SandboxResult(
                        success=True,
                        stdout=stdout,
                        stderr=stderr,
                        output=output_data,
                        execution_time_ms=execution_time_ms,
                    )
                else:
                    return SandboxResult(
                        success=False,
                        stdout=stdout,
                        stderr=stderr,
                        output=output_data,
                        execution_time_ms=execution_time_ms,
                        error=f"Execution failed with exit code {exit_code}",
                    )

            finally:
                # Cleanup container
                try:
                    container.remove(force=True)
                except Exception:
                    pass

        except ContainerError as e:
            return SandboxResult(
                success=False,
                stderr=str(e),
                error=f"Container error: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return SandboxResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    def _create_execution_script(self, user_code: str) -> str:
        """Create the execution wrapper script.

        Args:
            user_code: User's Python code

        Returns:
            Complete execution script
        """
        # Indent user code for try block
        indented_code = "\n".join(f"    {line}" for line in user_code.split("\n"))

        return f'''
import json
import sys

# Load input data
try:
    with open('/workspace/input.json', 'r') as f:
        data = json.load(f)
except:
    data = {{}}

# Available imports
import pandas as pd
import numpy as np

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# Execute user code
output = {{}}
try:
{indented_code}

    # Capture common output variables
    if 'result' in dir():
        if isinstance(result, pd.DataFrame):
            output['result'] = result.to_dict(orient='records')
        else:
            output['result'] = result

    if 'df' in dir() and isinstance(df, pd.DataFrame):
        output['dataframe'] = df.to_dict(orient='records')

    if 'fig' in dir():
        if hasattr(fig, 'to_json'):
            output['figure'] = fig.to_json()
        elif hasattr(fig, 'savefig'):
            fig.savefig('/tmp/plot.png', dpi=100, bbox_inches='tight')
            output['plot_saved'] = True

except Exception as e:
    print(f"ERROR: {{str(e)}}", file=sys.stderr)
    sys.exit(1)

# Save output
with open('/tmp/output.json', 'w') as f:
    json.dump(output, f)
'''

    def execute_simple(self, code: str) -> SandboxResult:
        """Execute simple code without Docker (for testing).

        WARNING: This is NOT secure and should only be used for testing.

        Args:
            code: Python code to execute

        Returns:
            SandboxResult with execution details
        """
        start_time = time.time()

        # Validate code
        is_valid, error = self.validator.validate(code)
        if not is_valid:
            return SandboxResult(
                success=False,
                error=f"Code validation failed: {error}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Execute in restricted namespace
        namespace = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
            }
        }

        try:
            import pandas as pd
            import numpy as np

            namespace["pd"] = pd
            namespace["np"] = np
            namespace["data"] = {}

            exec(code, namespace)

            output = {}
            if "result" in namespace:
                result = namespace["result"]
                if isinstance(result, pd.DataFrame):
                    output["result"] = result.to_dict(orient="records")
                else:
                    output["result"] = result

            return SandboxResult(
                success=True,
                output=output,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return SandboxResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

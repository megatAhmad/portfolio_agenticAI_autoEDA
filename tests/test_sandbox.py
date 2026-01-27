"""Tests for the Secure Sandbox."""

import pytest

from app.execution.sandbox import CodeValidator, SandboxResult, SecureSandbox


class TestCodeValidator:
    """Test suite for CodeValidator."""

    def test_valid_simple_code(self):
        """Test validation of simple valid code."""
        validator = CodeValidator()
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
result = df.sum()
"""
        is_valid, error = validator.validate(code)
        assert is_valid is True
        assert error is None

    def test_reject_eval(self):
        """Test rejection of eval() call."""
        validator = CodeValidator()
        code = "result = eval('1+1')"
        is_valid, error = validator.validate(code)
        assert is_valid is False
        assert "eval" in error.lower()

    def test_reject_exec(self):
        """Test rejection of exec() call."""
        validator = CodeValidator()
        code = "exec('print(1)')"
        is_valid, error = validator.validate(code)
        assert is_valid is False
        assert "exec" in error.lower()

    def test_reject_os_import(self):
        """Test rejection of os module import."""
        validator = CodeValidator()
        code = "import os\nos.system('ls')"
        is_valid, error = validator.validate(code)
        assert is_valid is False
        assert "os" in error.lower() or "forbidden" in error.lower()

    def test_reject_subprocess(self):
        """Test rejection of subprocess module."""
        validator = CodeValidator()
        code = "import subprocess\nsubprocess.run(['ls'])"
        is_valid, error = validator.validate(code)
        assert is_valid is False

    def test_reject_requests(self):
        """Test rejection of requests library."""
        validator = CodeValidator()
        code = "import requests\nrequests.get('http://example.com')"
        is_valid, error = validator.validate(code)
        assert is_valid is False

    def test_reject_socket(self):
        """Test rejection of socket module."""
        validator = CodeValidator()
        code = "import socket\ns = socket.socket()"
        is_valid, error = validator.validate(code)
        assert is_valid is False

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        validator = CodeValidator()
        code = "def broken(\nprint('hi')"
        is_valid, error = validator.validate(code)
        assert is_valid is False
        assert "syntax" in error.lower()

    def test_valid_pandas_operations(self):
        """Test validation of valid pandas code."""
        validator = CodeValidator()
        code = """
import pandas as pd
import numpy as np

df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
mean = df['x'].mean()
std = np.std(df['y'])
result = df.groupby('x').sum()
"""
        is_valid, error = validator.validate(code)
        assert is_valid is True


class TestSandboxResult:
    """Test suite for SandboxResult model."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = SandboxResult(
            success=True,
            stdout="Hello",
            output={"result": 42},
            execution_time_ms=100,
        )
        assert result.success is True
        assert result.output["result"] == 42

    def test_failed_result(self):
        """Test creating a failed result."""
        result = SandboxResult(
            success=False,
            error="Division by zero",
            execution_time_ms=50,
        )
        assert result.success is False
        assert result.error == "Division by zero"


class TestSecureSandbox:
    """Test suite for SecureSandbox."""

    def test_init_defaults(self):
        """Test sandbox initialization with defaults."""
        sandbox = SecureSandbox()
        assert sandbox.timeout == 30
        assert sandbox.memory_limit == "512m"

    def test_init_custom_values(self):
        """Test sandbox initialization with custom values."""
        sandbox = SecureSandbox(timeout=60, memory_limit="1g")
        assert sandbox.timeout == 60
        assert sandbox.memory_limit == "1g"

    def test_execute_simple_validates_code(self):
        """Test that execute_simple validates code."""
        sandbox = SecureSandbox()

        # Should reject dangerous code
        result = sandbox.execute_simple("import os; os.system('rm -rf /')")
        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_execute_simple_valid_code(self):
        """Test execute_simple with valid code."""
        sandbox = SecureSandbox()
        code = """
result = sum([1, 2, 3, 4, 5])
"""
        result = sandbox.execute_simple(code)
        assert result.success is True
        assert result.output.get("result") == 15

    def test_execute_simple_with_pandas(self):
        """Test execute_simple with pandas operations."""
        sandbox = SecureSandbox()
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
result = int(df['a'].sum())
"""
        result = sandbox.execute_simple(code)
        assert result.success is True
        assert result.output.get("result") == 6

"""
Runtime manager for Metupy.

Manages Bun/Node.js runtime and Pyodide installation
for executing Python code in .pym files.
"""

import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class RuntimeManager:
    """Manage Bun/Node.js runtime and Pyodide."""

    BUN_VERSION = "1.2.0"
    PYODIDE_VERSION = "0.26.4"

    def __init__(self, engine=None):
        """
        Initialize RuntimeManager.

        Args:
            engine: Optional MetupyEngine instance.
        """
        self.engine = engine
        self.metupy_dir = Path.home() / '.metupy'
        self.runtime_dir = self.metupy_dir / 'runtime'
        self.pyodide_dir = self.metupy_dir / 'pyodide'
        self.bun_dir = self.runtime_dir / 'bun'
        self.temp_dir = self.metupy_dir / 'temp'
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories."""
        self.metupy_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """
        Get runtime installation status.

        Returns:
            Dictionary with runtime status.
        """
        return {
            'bun': self.is_bun_available(),
            'node': self.is_node_available(),
            'pyodide': self.is_pyodide_available(),
            'runtime': self.detect_runtime(),
            'metupy_dir': str(self.metupy_dir),
        }

    def is_bun_available(self) -> bool:
        """
        Check if Bun is available.

        Returns:
            True if Bun is in PATH or installed locally.
        """
        try:
            result = subprocess.run(
                ['bun', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        bun_binary = self.bun_dir / self._get_platform() / 'bun'
        if bun_binary.exists():
            return True

        bun_exe = self.bun_dir / self._get_platform() / 'bun.exe'
        return bun_exe.exists()

    def is_node_available(self) -> bool:
        """
        Check if Node.js is available.

        Returns:
            True if Node.js is in PATH.
        """
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_pyodide_available(self) -> bool:
        """
        Check if Pyodide is installed.

        Returns:
            True if pyodide.js exists.
        """
        return (self.pyodide_dir / 'pyodide.js').exists()

    def detect_runtime(self) -> Optional[str]:
        """
        Detect available JavaScript runtime.

        Returns:
            'bun', 'node', or None.
        """
        if self.is_bun_available():
            return 'bun'
        if self.is_node_available():
            return 'node'
        return None

    def _get_platform(self) -> str:
        """
        Detect current platform.

        Returns:
            Platform identifier string.
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == 'linux':
            if 'arm' in machine or 'aarch64' in machine:
                return 'linux-arm64'
            return 'linux-x64'
        elif system == 'darwin':
            if 'arm' in machine or 'aarch64' in machine:
                return 'darwin-arm64'
            return 'darwin-x64'
        elif system == 'windows':
            return 'windows-x64'
        return 'linux-x64'

    def install_bun(self) -> bool:
        """
        Download and install Bun.

        Returns:
            True if installation successful.
        """
        if self.is_bun_available():
            print("  Bun already available")
            return True

        platform_name = self._get_platform()
        url = (
            f"https://github.com/oven-sh/bun/releases/download/"
            f"bun-v{self.BUN_VERSION}/bun-{platform_name}.zip"
        )

        print(f"  Downloading Bun v{self.BUN_VERSION} for {platform_name}...")

        import urllib.request
        import zipfile
        import tempfile

        try:
            target_dir = self.bun_dir / platform_name
            target_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                urllib.request.urlretrieve(url, tmp.name)
                with zipfile.ZipFile(tmp.name, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)

            bun_binary = target_dir / 'bun'
            if bun_binary.exists():
                bun_binary.chmod(0o755)

            print("  Bun installed successfully")
            return True

        except Exception as e:
            print(f"  Bun install failed: {e}")
            return False

    def install_pyodide(self) -> bool:
        """
        Download and install Pyodide.

        Returns:
            True if installation successful.
        """
        if self.is_pyodide_available():
            print("  Pyodide already available")
            return True

        url = (
            f"https://cdn.jsdelivr.net/pyodide/"
            f"v{self.PYODIDE_VERSION}/full/pyodide.tar.gz"
        )

        print("  Downloading Pyodide...")

        import urllib.request
        import tarfile
        import tempfile

        try:
            self.pyodide_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                urllib.request.urlretrieve(url, tmp.name)
                with tarfile.open(tmp.name, 'r:gz') as tar:
                    tar.extractall(self.pyodide_dir)

            print("  Pyodide installed successfully")
            return True

        except Exception as e:
            print(f"  Pyodide install failed: {e}")
            return False

    def setup_all(self) -> Dict[str, Any]:
        """
        Install all required runtime components.

        Returns:
            Dictionary with setup results.
        """
        print("\n=== Runtime Setup ===\n")

        results = {
            'bun': self.install_bun(),
            'pyodide': self.install_pyodide(),
            'runtime': self.detect_runtime(),
        }

        return results

    def execute_python(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Python code using Bun/Node.js + Pyodide.

        Args:
            code: Python code to execute.
            context: Optional context variables.

        Returns:
            Dictionary of resulting variables.
        """
        runtime = self.detect_runtime()

        if not runtime:
            return {'__error__': 'No JavaScript runtime available'}

        if not self.is_pyodide_available():
            return {'__error__': 'Pyodide not installed'}

        script = self._create_execution_script(code, context)
        script_file = self.temp_dir / 'pym_execute.js'
        script_file.write_text(script, encoding='utf-8')

        try:
            result = subprocess.run(
                [runtime, str(script_file)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.metupy_dir)
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return {'__error__': result.stderr}

        except subprocess.TimeoutExpired:
            return {'__error__': 'Execution timeout'}
        except Exception as e:
            return {'__error__': str(e)}

    def _create_execution_script(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JavaScript execution script.

        Args:
            code: Python code to execute.
            context: Context variables.

        Returns:
            JavaScript code string.
        """
        context_json = json.dumps(context or {})
        code_json = json.dumps(code)
        pyodide_path = str(self.pyodide_dir).replace('\\', '/')

        return f"""
const pyodidePath = '{pyodide_path}/pyodide.js';

async function main() {{
    const {{ loadPyodide }} = await import(pyodidePath);

    const pyodide = await loadPyodide({{
        indexURL: '{pyodide_path}/'
    }});

    const context = {context_json};
    for (const [key, value] of Object.entries(context)) {{
        pyodide.globals.set(key, value);
    }}

    const code = {code_json};

    try {{
        await pyodide.runPythonAsync(code);

        const result = {{}};
        const vars = pyodide.globals.keys();

        for (const key of vars) {{
            if (!key.startsWith('__')) {{
                try {{
                    const value = pyodide.globals.get(key);
                    if (typeof value === 'object' && value !== null) {{
                        result[key] = JSON.parse(JSON.stringify(value));
                    }} else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {{
                        result[key] = value;
                    }}
                }} catch (e) {{
                    // Skip non-serializable values
                }}
            }}
        }}

        console.log(JSON.stringify(result));
    }} catch (e) {{
        console.error(e.message);
        process.exit(1);
    }}
}}

main();
"""
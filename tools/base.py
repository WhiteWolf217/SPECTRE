import subprocess
import shutil
from abc import ABC, abstractmethod
from datetime import datetime


class BaseTool(ABC):
    """Base class for all SPECTRE tools."""

    name: str = ""
    description: str = ""
    requires_confirmation: bool = False  # destructive tools set this True

    def check_installed(self) -> bool:
        return shutil.which(self.name) is not None

    def run(self, **kwargs) -> dict:
        if not self.check_installed():
            return self._error(f"Tool '{self.name}' not found. Install it first.")
        return self._run(**kwargs)

    @abstractmethod
    def _run(self, **kwargs) -> dict:
        pass

    def _exec(self, cmd: list, timeout: int = 300) -> dict:
        """Run a subprocess command and return structured output."""
        start = datetime.now()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = (datetime.now() - start).seconds
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "returncode": proc.returncode,
                "command": " ".join(cmd),
                "elapsed_seconds": elapsed,
                "timestamp": start.isoformat(),
            }
        except subprocess.TimeoutExpired:
            return self._error(f"Tool timed out after {timeout}s", cmd=" ".join(cmd))
        except FileNotFoundError:
            return self._error(f"Binary not found: {cmd[0]}", cmd=" ".join(cmd))
        except Exception as e:
            return self._error(str(e), cmd=" ".join(cmd))

    def _error(self, message: str, cmd: str = "") -> dict:
        return {
            "success": False,
            "stdout": "",
            "stderr": message,
            "returncode": -1,
            "command": cmd,
            "elapsed_seconds": 0,
            "timestamp": datetime.now().isoformat(),
        }

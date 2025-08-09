from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    executable_path: Optional[Path] = None


def _run_command(command: List[str], cwd: Path | None = None, input_text: str | None = None, timeout: int = 20) -> ExecutionResult:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            input=input_text.encode("utf-8") if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return ExecutionResult(
            returncode=completed.returncode,
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
        )
    except subprocess.TimeoutExpired as exc:
        return ExecutionResult(returncode=124, stdout=exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "", stderr=f"Timeout after {timeout}s")
    except FileNotFoundError as exc:
        return ExecutionResult(returncode=127, stdout="", stderr=f"Command not found: {exc}")


def _which(name: str) -> bool:
    return shutil.which(name) is not None


def execute(language: str, source_path: Path, args: Optional[List[str]] = None, stdin_text: Optional[str] = None, timeout: int = 20) -> ExecutionResult:
    language_lower = language.lower()
    args = args or []

    if not source_path.exists():
        return ExecutionResult(returncode=2, stdout="", stderr=f"Source file not found: {source_path}")

    with tempfile.TemporaryDirectory(prefix="exec_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        if language_lower in {"c", "c99", "c11"}:
            if not _which("gcc"):
                return ExecutionResult(returncode=127, stdout="", stderr="gcc not found. Please install GCC.")
            output = tmp_dir / "program_c.exe" if os.name == "nt" else tmp_dir / "program_c"
            compile_cmd = ["gcc", str(source_path), "-O2", "-std=c11", "-o", str(output)]
            comp = _run_command(compile_cmd, cwd=tmp_dir, timeout=timeout)
            if comp.returncode != 0:
                return comp
            run_cmd = [str(output), *args]
            res = _run_command(run_cmd, cwd=tmp_dir, input_text=stdin_text, timeout=timeout)
            res.executable_path = output
            return res

        if language_lower in {"cpp", "c++", "cxx"}:
            if not _which("g++"):
                return ExecutionResult(returncode=127, stdout="", stderr="g++ not found. Please install G++.")
            output = tmp_dir / "program_cpp.exe" if os.name == "nt" else tmp_dir / "program_cpp"
            compile_cmd = ["g++", str(source_path), "-O2", "-std=c++17", "-o", str(output)]
            comp = _run_command(compile_cmd, cwd=tmp_dir, timeout=timeout)
            if comp.returncode != 0:
                return comp
            run_cmd = [str(output), *args]
            res = _run_command(run_cmd, cwd=tmp_dir, input_text=stdin_text, timeout=timeout)
            res.executable_path = output
            return res

        if language_lower in {"c#", "csharp", "cs"}:
            # Prefer csc if available (ships with .NET SDK on Windows)
            if _which("csc"):
                output = tmp_dir / ("Program.exe" if os.name == "nt" else "Program.exe")
                comp = _run_command(["csc", "/nologo", f"/out:{output}", str(source_path)], cwd=tmp_dir, timeout=timeout)
                if comp.returncode != 0:
                    return comp
                run_cmd = [str(output), *args]
                return _run_command(run_cmd, cwd=tmp_dir, input_text=stdin_text, timeout=timeout)
            return ExecutionResult(returncode=127, stdout="", stderr="C# compiler not found (csc). Install .NET SDK and ensure 'csc' is in PATH.")

        if language_lower in {"shell", "bash", "sh", "powershell", "pwsh"}:
            # Choose interpreter based on OS and language
            if language_lower in {"powershell", "pwsh"} or (os.name == "nt" and source_path.suffix.lower() == ".ps1"):
                pwsh = shutil.which("pwsh") or shutil.which("powershell")
                if not pwsh:
                    return ExecutionResult(returncode=127, stdout="", stderr="PowerShell not found.")
                cmd = [pwsh, "-NoProfile", "-File", str(source_path), *args]
                return _run_command(cmd, cwd=source_path.parent, input_text=stdin_text, timeout=timeout)
            # default to bash/sh
            bash = shutil.which("bash") or shutil.which("sh")
            if not bash:
                return ExecutionResult(returncode=127, stdout="", stderr="bash/sh not found.")
            cmd = [bash, str(source_path), *args]
            return _run_command(cmd, cwd=source_path.parent, input_text=stdin_text, timeout=timeout)

        return ExecutionResult(returncode=2, stdout="", stderr=f"Unsupported language: {language}")



"""
Model Download & Setup Script for Gita Realtime Voice Assistance RAG
Downloads and verifies all local neural models required for the pipeline:
1. Faster-Whisper (ASR / STT)
2. Silero VAD (Voice Activity Detection)
3. BGE Embeddings (Dense Vector Search)
4. BGE Reranker (Cross-Encoder Re-ranking)
5. Kokoro-82M (TTS / Speech Synthesis)
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import torch
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from huggingface_hub import snapshot_download
# pyrefly: ignore [missing-import]
from src.config import settings

console = Console(highlight=False)


def print_system_info():
    """Display environment, CUDA and system info."""
    table = Table(title="System & Environment Overview", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Python Executable", sys.executable)
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("PyTorch Version", torch.__version__)
    
    cuda_available = torch.cuda.is_available()
    table.add_row("CUDA Available", "[bold green]YES[/bold green]" if cuda_available else "[yellow]NO (CPU Mode)[/yellow]")
    
    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        table.add_row("GPU Device", f"{device_name} ({vram_gb:.2f} GB VRAM)")
        table.add_row("Compute Type", settings.COMPUTE_TYPE)

    console.print(table)
    console.print()


def download_whisper(model_name: str = settings.WHISPER_MODEL_NAME, output_dir: Path = settings.WHISPER_MODEL_DIR):
    """Download Faster-Whisper model."""
    console.print(f"[bold yellow]-> Downloading Faster-Whisper Model ('{model_name}')...[/bold yellow]")
    try:
        from faster_whisper import download_model
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = download_model(model_name, output_dir=str(output_dir))
        console.print(f"[bold green][OK] Faster-Whisper model ready at:[/bold green] {model_path}\n")
        return True
    except Exception as e:
        console.print(f"[bold red][ERR] Failed downloading Whisper model:[/bold red] {e}\n")
        return False


def download_vad():
    """Pre-cache and verify Silero VAD model."""
    console.print("[bold yellow]-> Loading / Caching Silero VAD Model...[/bold yellow]")
    try:
        import silero_vad
        model = silero_vad.load_silero_vad()
        console.print("[bold green][OK] Silero VAD model loaded & verified successfully![/bold green]\n")
        return True
    except Exception as e:
        console.print(f"[bold red][ERR] Failed loading Silero VAD:[/bold red] {e}\n")
        return False


def download_embeddings(repo_id: str = settings.EMBEDDING_MODEL_NAME, output_dir: Path = settings.EMBEDDING_MODEL_DIR):
    """Download BGE Embedding Model via Hugging Face Hub."""
    console.print(f"[bold yellow]-> Downloading Embedding Model ('{repo_id}')...[/bold yellow]")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=str(output_dir),
            ignore_patterns=["*.msgpack", "*.h5", "*.tflite", "*.ot", "*.onnx", "*.onnx_data"]
        )
        console.print(f"[bold green][OK] Embedding model ready at:[/bold green] {path}\n")
        return True
    except Exception as e:
        console.print(f"[bold red][ERR] Failed downloading Embedding model:[/bold red] {e}\n")
        return False


def download_reranker(repo_id: str = settings.RERANKER_MODEL_NAME, output_dir: Path = settings.RERANKER_MODEL_DIR):
    """Download BGE Reranker Model via Hugging Face Hub."""
    console.print(f"[bold yellow]-> Downloading Reranker Model ('{repo_id}')...[/bold yellow]")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=str(output_dir),
            ignore_patterns=["*.msgpack", "*.h5", "*.tflite", "*.ot", "*.onnx", "*.onnx_data", "pytorch_model.bin"]
        )
        console.print(f"[bold green][OK] Reranker model ready at:[/bold green] {path}\n")
        return True
    except Exception as e:
        console.print(f"[bold red][ERR] Failed downloading Reranker model:[/bold red] {e}\n")
        return False


def download_kokoro(repo_id: str = settings.KOKORO_MODEL_NAME, output_dir: Path = settings.KOKORO_MODEL_DIR):
    """Download Kokoro-82M TTS Model & Voices via Hugging Face Hub."""
    console.print(f"[bold yellow]-> Downloading Kokoro-82M TTS Model & Voices ('{repo_id}')...[/bold yellow]")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=str(output_dir),
            ignore_patterns=["*.msgpack", "*.h5", "*.tflite", "*.ot"]
        )
        console.print(f"[bold green][OK] Kokoro TTS model & voices ready at:[/bold green] {path}\n")
        return True
    except Exception as e:
        console.print(f"[bold red][ERR] Failed downloading Kokoro TTS model:[/bold red] {e}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download all models required for Gita Voice Assistant RAG")
    parser.add_argument("--all", action="store_true", default=False, help="Download all models")
    parser.add_argument("--whisper", action="store_true", help="Download only Faster-Whisper model")
    parser.add_argument("--vad", action="store_true", help="Download only Silero VAD model")
    parser.add_argument("--embeddings", action="store_true", help="Download only Embeddings model")
    parser.add_argument("--reranker", action="store_true", help="Download only Reranker model")
    parser.add_argument("--tts", action="store_true", help="Download only Kokoro-82M TTS model")
    parser.add_argument("--whisper-name", type=str, default=settings.WHISPER_MODEL_NAME, help="Whisper model size (base/small/medium)")

    args = parser.parse_args()
    
    console.print(Panel.fit("[bold magenta]Gita Realtime Voice Assistance RAG -- Model Setup[/bold magenta]", border_style="cyan"))
    print_system_info()

    # Determine what to download: if no specific flag passed, default to downloading all
    selective = any([args.whisper, args.vad, args.embeddings, args.reranker, args.tts])
    download_all = args.all or not selective

    results = {}

    if download_all or args.whisper:
        results["Faster-Whisper (STT)"] = download_whisper(model_name=args.whisper_name)
    
    if download_all or args.vad:
        results["Silero VAD"] = download_vad()

    if download_all or args.embeddings:
        results["BGE Embeddings"] = download_embeddings()

    if download_all or args.reranker:
        results["BGE Reranker"] = download_reranker()

    if download_all or args.tts:
        results["Kokoro-82M (TTS)"] = download_kokoro()

    # Summary table
    summary_table = Table(title="Model Download Status Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Component", style="bold")
    summary_table.add_column("Status")

    for component, success in results.items():
        summary_table.add_row(component, "[green]Ready[/green]" if success else "[red]Failed[/red]")

    console.print(summary_table)
    console.print("[bold green]Setup completed! You are ready to build the RAG pipeline.[/bold green]\n")


if __name__ == "__main__":
    main()

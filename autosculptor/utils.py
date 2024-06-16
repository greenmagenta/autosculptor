import sys
import subprocess

def ensure_gradio_installed():
    try:
        import gradio_client
        return True
    except ImportError:
        return False

def install_gradio():
    python_executable = sys.executable
    subprocess.check_call([python_executable, '-m', 'ensurepip'])
    subprocess.check_call([python_executable, '-m', 'pip', 'install', 'gradio_client==1.0.1'])

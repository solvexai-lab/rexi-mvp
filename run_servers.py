"""Start backend and frontend servers as detached Windows processes."""
import subprocess
import sys
import os
import time

def start_backend():
    log = open(r'd:\rexi-kn\rexi-mvp\backend\server.log', 'w')
    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
        cwd=r'd:\rexi-kn\rexi-mvp\backend',
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )
    return proc.pid

def start_frontend():
    log = open(r'd:\rexi-kn\rexi-mvp\frontend\server.log', 'w')
    proc = subprocess.Popen(
        [sys.executable, '-m', 'http.server', '5173', '--directory', 'dist'],
        cwd=r'd:\rexi-kn\rexi-mvp\frontend',
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )
    return proc.pid

if __name__ == '__main__':
    backend_pid = start_backend()
    print(f'Backend started on PID {backend_pid}')
    time.sleep(2)
    frontend_pid = start_frontend()
    print(f'Frontend started on PID {frontend_pid}')
    print('Both servers should be up in ~40 seconds.')
    print('Backend: http://127.0.0.1:8000')
    print('Frontend: http://127.0.0.1:5173')

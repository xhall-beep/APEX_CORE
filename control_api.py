import os, pty, subprocess, select, json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='./deliveries')
socketio = SocketIO(app, cors_allowed_origins="*")

# Create the Physical Shell Pipe
fd, child_pid = pty.fork()
if child_pid == 0:
    os.execvp('bash', ['bash'])

def read_and_forward():
    while True:
        socketio.sleep(0.01)
        if fd:
            (data_ready, _, _) = select.select([fd], [], [], 0)
            if data_ready:
                output = os.read(fd, 1024).decode('utf-8', 'ignore')
                socketio.emit('terminal_output', {'output': output})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scout_supreme')
def scout_supreme():
    # Targeted search for Trinity, Arbigent, and Aegis
    repos = ["takahirom/arbigent", "VersusControl/ai-infrastructure-agent", "GetBindu/Bindu"]
    return jsonify({"targets": repos, "status": "🔱 SUPREME TARGETS IDENTIFIED"})

@socketio.on('terminal_input')
def handle_input(data):
    os.write(fd, data['input'].encode())

if __name__ == "__main__":
    socketio.start_background_task(target=read_and_forward)
    socketio.run(app, host='0.0.0.0', port=8080)

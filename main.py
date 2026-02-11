#!/usr/bin/env python3
import os, sys, json, subprocess, socket, threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock

class ExecutionBridge:
    """The Multi-Bridge: Talks to Termux Daemon to bypass APK limits."""
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port

    def execute(self, command):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(30)
            s.connect((self.host, self.port))
            s.send(command.encode())
            resp = s.recv(16384).decode()
            s.close()
            return True, resp, ""
        except Exception as e:
            return False, f"❌ Bridge Error: Ensure Daemon is running.\n{str(e)}", ""

class AgentTerminal(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.bridge = ExecutionBridge()
        self.pending_command = None
        
        self.add_widget(Label(text="🔱 APEX 600 : SOVEREIGN SEED", size_hint_y=0.1, bold=True))
        
        self.output = TextInput(text="🔱 SYSTEM INITIALIZED\nControl Plane: STANDBY\nExecution Plane: CONNECTED\nWaiting for command...", 
                                readonly=True, background_color=(0,0,0,1), 
                                foreground_color=(0,1,0,1), font_size='14sp')
        self.add_widget(self.output)
        
        self.input_field = TextInput(hint_text="Enter Agentic Command...", size_hint_y=0.12, multiline=False)
        self.input_field.bind(on_text_validate=self.stage_command)
        self.add_widget(self.input_field)
        
        self.confirm_btn = Button(text="CONFIRM AGENTIC ACTION", size_hint_y=0.15, 
                                 background_color=(0.8, 0, 0, 1), disabled=True, bold=True)
        self.confirm_btn.bind(on_release=self.commit_execution)
        self.add_widget(self.confirm_btn)

    def stage_command(self, instance):
        if instance.text.strip():
            self.pending_command = instance.text
            self.output.text += f"\n\n🔱 [STAGED]: {self.pending_command}\n[MEDIATION]: Confirm to grant local execution privilege."
            self.confirm_btn.disabled = False
            self.confirm_btn.background_color = (0, 0.7, 0.3, 1)

    def commit_execution(self, instance):
        if self.pending_command:
            self.output.text += "\n🔱 Executing via Sovereign Multi-Bridge..."
            threading.Thread(target=self._run_task, args=(self.pending_command,)).start()
            self.pending_command = None
            self.confirm_btn.disabled = True
            self.confirm_btn.background_color = (0.8, 0, 0, 1)
            self.input_field.text = ""

    def _run_task(self, cmd):
        success, stdout, stderr = self.bridge.execute(cmd)
        def update_ui(dt):
            self.output.text += f"\n[RESULT]:\n{stdout}{stderr}"
        Clock.schedule_once(update_ui)

class AgentApp(App):
    def build(self):
        return AgentTerminal()

if __name__ == "__main__":
    AgentApp().run()

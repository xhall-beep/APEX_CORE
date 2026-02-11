import os
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

class ApexCoreApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.status_label = Label(text="🔱 APEX CORE V84.3: SYSTEM ONLINE", font_size='20sp')
        
        # Action Buttons for our specific capabilities
        btn_hook = Button(text="ENGAGE HOOKER (SSL UNPIN)")
        btn_hook.bind(on_press=self.run_hooker)
        
        btn_reason = Button(text="LOCAL REASONING (PANDAS/SKLEARN)")
        btn_reason.bind(on_press=self.run_reasoning)

        layout.add_widget(self.status_label)
        layout.add_widget(btn_hook)
        layout.add_widget(btn_reason)
        return layout

    def run_hooker(self, instance):
        self.status_label.text = "🔱 STATUS: INJECTING HOOKER PAYLOADS..."
        # Logic to call frida-tools from the requirements
        os.system("frida --version") 

    def run_reasoning(self, instance):
        self.status_label.text = "🔱 STATUS: REASONING WITHOUT APIs..."
        import local_reasoning
        local_reasoning.analyze_and_act({"agent": "APEX_V84"})

if __name__ == "__main__":
    ApexCoreApp().run()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
import requests

ESP_IP = "192.168.1.150"   # 🔹 your ESP32 IP here
REFRESH_INTERVAL = 5       # seconds


class SmartFarming(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        # IP Input
        self.ip_input = TextInput(text=ESP_IP, hint_text='ESP32 IP (e.g. 192.168.1.150)', size_hint_y=None, height=40)
        self.add_widget(self.ip_input)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        refresh_btn = Button(text='🔄 Refresh', on_press=self.refresh_data)
        live_btn = Button(text='▶️ Live Start', on_press=self.start_live)
        stop_btn = Button(text='⏹ Stop', on_press=self.stop_live)
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(live_btn)
        btn_layout.add_widget(stop_btn)
        self.add_widget(btn_layout)

        # Image
        self.plant_img = AsyncImage(source='', size_hint_y=None, height=200)
        self.add_widget(self.plant_img)

        # Labels
        self.soil = Label(text='Soil: -- %')
        self.temp = Label(text='Temp: -- °C')
        self.hum = Label(text='Humidity: -- %')
        self.tank = Label(text='Tank: --')
        self.ai = Label(text='Plant: --')
        self.solution = Label(text='Solution: --', halign='left', valign='top')

        for lbl in [self.soil, self.temp, self.hum, self.tank, self.ai, self.solution]:
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

        self.status = Label(text='Status: Waiting...')
        self.add_widget(self.status)

        self.event = None

    def refresh_data(self, *args):
        ip = self.ip_input.text.strip()
        if not ip:
            self.show_popup("Please enter ESP32 IP address.")
            return
        try:
            url = f"http://{ip}/data"
            self.status.text = f"Connecting to {url} ..."
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            data = response.text.strip()
            self.parse_data(data)
        except Exception as e:
            self.status.text = f"⚠️ Error: {e}"
            print("Error:", e)

    def parse_data(self, text):
        data_dict = {}
        for part in text.split(";"):
            if ":" in part:
                key, val = part.split(":", 1)
                data_dict[key.strip()] = val.strip()

        self.soil.text = f"Soil: {data_dict.get('soil', '--')} %"
        self.temp.text = f"Temp: {data_dict.get('temp', '--')} °C"
        self.hum.text = f"Humidity: {data_dict.get('hum', '--')} %"
        self.tank.text = f"Tank: {data_dict.get('tank', '--')}"
        self.ai.text = f"Plant: {data_dict.get('ai', '--')}"

        # Suggestion logic
        plant = data_dict.get('ai', 'Healthy').lower()
        if "bacterial" in plant:
            suggestion = "Spray copper fungicide; remove infected leaves."
        elif "blight" in plant:
            suggestion = "Apply Mancozeb fungicide once."
        elif "dry" in plant:
            suggestion = "Increase watering; check soil moisture."
        elif "animal" in plant:
            suggestion = "⚠️ Animal detected! Check your farm."
        else:
            suggestion = "Plant looks healthy 🌿"
        self.solution.text = f"Solution: {suggestion}"

        # Image update
        img_url = data_dict.get('img', '')
        if img_url:
            self.plant_img.source = img_url

        self.status.text = "✅ Updated successfully"

    def show_popup(self, msg):
        popup = Popup(title='Notice', content=Label(text=msg), size_hint=(0.8, 0.3))
        popup.open()

    def start_live(self, *args):
        self.status.text = "🔁 Live update started..."
        if not self.event:
            self.event = Clock.schedule_interval(self.refresh_data, REFRESH_INTERVAL)

    def stop_live(self, *args):
        self.status.text = "⏹ Live update stopped."
        if self.event:
            self.event.cancel()
            self.event = None


class SmartFarmingApp(App):
    def build(self):
        return SmartFarming()


if __name__ == '__main__':
    SmartFarmingApp().run()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.utils import platform
from plyer import notification
import websocket
import threading
import json
import requests

# Main App UI
class SafetyApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Connect to WebSocket server
        self.ws_url = "ws://127.0.0.1:5000/socket.io"  # Replace with your Flask server URL
        self.connect_websocket()

        # SOS Button
        self.sos_button = Button(text="Trigger SOS", size_hint=(1, 0.2))
        self.sos_button.bind(on_press=self.trigger_sos)
        self.layout.add_widget(self.sos_button)

        # Save Contacts Section
        self.contact_name_input = TextInput(hint_text="Contact Name", size_hint=(1, 0.1))
        self.contact_phone_input = TextInput(hint_text="Contact Phone", size_hint=(1, 0.1))
        self.save_contact_button = Button(text="Save Contact", size_hint=(1, 0.2))
        self.save_contact_button.bind(on_press=self.save_contact)
        self.layout.add_widget(self.contact_name_input)
        self.layout.add_widget(self.contact_phone_input)
        self.layout.add_widget(self.save_contact_button)

        # Fake Call Button
        self.fake_call_button = Button(text="Fake Call", size_hint=(1, 0.2))
        self.fake_call_button.bind(on_press=self.show_fake_call)
        self.layout.add_widget(self.fake_call_button)

        # Start GPS
        self.start_gps()

        return self.layout

    # Connect to WebSocket server
    def connect_websocket(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        threading.Thread(target=self.ws.run_forever).start()

    # Handle incoming WebSocket messages
    def on_message(self, ws, message):
        print(f"Received message: {message}")
        alert_data = json.loads(message)
        self.show_notification("SOS Alert", f"User {alert_data['userId']} needs help at {alert_data['location']}")

    # Handle WebSocket errors
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    # Handle WebSocket connection close
    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    # Trigger SOS Alert
    def trigger_sos(self, instance):
        # Get current location
        if hasattr(self, 'location'):
            location = self.location
        else:
            location = {"lat": 12.34, "lng": 56.78}  # Default location if GPS fails

        # Send SOS request to Flask backend
        try:
            response = requests.post("http://127.0.0.1:5000/sos", json={
                "userId": 1,  # Replace with actual user ID
                "location": location
            })
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print("Invalid response from server")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Save Emergency Contact
    def save_contact(self, instance):
        contact_name = self.contact_name_input.text
        contact_phone = self.contact_phone_input.text

        # Send contact data to Flask backend
        response = requests.post("http://127.0.0.1:5000/save-contacts", json={
            "userId": 1,  # Replace with actual user ID
            "contacts": [{"name": contact_name, "phone": contact_phone}]
        })
        print(response.json())

    # Show Fake Call Screen
    def show_fake_call(self, instance):
        view = ModalView(size_hint=(0.8, 0.4))
        view.add_widget(Label(text="Fake Call\nIncoming..."))
        view.open()

    # Start GPS for Live Location
    def start_gps(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION])

            from plyer import gps
            gps.configure(on_location=self.on_location)
            gps.start()
        else:
            print("GPS is only supported on Android devices.")

    # GPS Location Callback
    def on_location(self, **kwargs):
        self.location = {"lat": kwargs['lat'], "lng": kwargs['lon']}
        print(f"Current Location: {self.location}")

    # Show Notification
    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name="Safety App"
        )

# Run the Kivy App
if __name__ == '__main__':
    SafetyApp().run()
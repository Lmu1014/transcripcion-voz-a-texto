import tkinter as tk
import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient
from PIL import Image, ImageTk
import time

def get_speech_config():
    speech_key = '999fcb4d3f34436ab454ec47920febe0'
    service_region = 'centralus'
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "es-CO"
    speech_config.speech_synthesis_language = "es-CO"
    speech_config.speech_synthesis_voice_name = "es-CO-GonzaloNeural"
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "6000")
    return speech_config

class SpeechApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Registro Bitacoras")
        self.geometry("300x500")
        
        self.speech_config = get_speech_config()
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        
        self.create_widgets()
        self.fields = ["nombre", "cargo", "ciudad", "actividades"]
        self.responses = {}
        self.current_field = 0
        self.after(1000, self.wait_for_start_command)

    def create_widgets(self):
        original = Image.open(r"C:\Users\Iac\OneDrive - IAC SAS\Documentos\DemoSpeech\Despliegue\logo.png")
        resized = original.resize((200, 110), Image.Resampling.LANCZOS)
        self.logo = ImageTk.PhotoImage(resized)
        tk.Label(self, image=self.logo).pack(pady=20)
        
        self.status_label = tk.Label(self, text="Di 'iniciar registro' para empezar.", wraplength=280, font=("Times New Roman", 12, "bold"), bg="white", fg="black")
        self.status_label.pack(pady=10, padx=10, fill="both")

        self.response_text = tk.Text(self, wrap="word", font=("Times New Roman", 12))
        self.response_text.pack(pady=10, padx=10, fill="both", expand=True)

    def update_status(self, message):
        self.status_label.config(text=message)
        self.update()

    def speak_and_listen(self, prompt):
        self.update_status(prompt)
        self.speech_synthesizer.speak_text_async(prompt)
        result = self.speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            self.update_status("Error en el reconocimiento de voz.")
            return None

    def wait_for_start_command(self):
        self.update_status("Di 'iniciar registro' para empezar.")
        command = self.speak_and_listen("Esperando comando para iniciar.")
        if command and "iniciar registro" in command.lower():
            self.start_interaction()
        else:
            self.after(1000, self.wait_for_start_command)

    def start_interaction(self):
        self.update_status("Iniciando registro de datos...")
        for field in self.fields:
            valid_response = False
            while not valid_response:
                response = self.speak_and_listen(f"Por favor di tu {field}.")
                if response:
                    self.response_text.insert(tk.END, f"{field}: {response}\n")
                    self.response_text.see(tk.END)
                    valid_response = self.confirm_response(response)
            self.responses[field] = response
        
        self.update_status("Verifica si tus datos están correctos y di 'guardar registro' para guardar.")
        self.wait_for_save_command()

    def confirm_response(self, response):
        confirmation = self.speak_and_listen(f"Confirmas que dijiste: {response}? Di sí o no.")
        if confirmation and "sí" in confirmation.lower():
            return True
        elif confirmation and "no" in confirmation.lower():
            return False
        else:
            return self.confirm_response(response)

    def wait_for_save_command(self):
        command = self.speak_and_listen("Di 'guardar registro' para guardar los datos.")
        if command and "guardar registro" in command.lower():
            self.save_to_blob()
        else:
            self.after(1000, self.wait_for_save_command)

    def save_to_blob(self):
        connect_str = 'DefaultEndpointsProtocol=https;AccountName=registrobitacora;AccountKey=y1ypSZq0b/bhuADyaLzu7SWLPWhIYVgM3TGa1Ux4q/66eAU7XdPm2xBaiUGM96rIce76+nenCFWs+AStSDfYmA==;EndpointSuffix=core.windows.net'
        container_name = 'registros'
        blob_name = f"{self.responses['nombre']}.txt"
        data = ", ".join(f"{key}: {value}" for key, value in self.responses.items())  # Concatenación de datos como una cadena de texto

        # Imprimir el contenido de la cadena de datos antes de cargarla en el Blob Storage
        print("Contenido de la cadena de datos:")
        print(data)

        try:
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data.encode('utf-8'), overwrite=True)  # Cargar la cadena de datos en el Blob Storage
            self.update_status("Datos guardados correctamente.")
        except Exception as e:
            self.update_status(f"Error al guardar datos: {e}")

if __name__ == "__main__":
    app = SpeechApp()
    app.mainloop()

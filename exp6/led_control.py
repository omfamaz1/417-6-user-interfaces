import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time


class LEDController:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Brightness Control")
        self.root.geometry("450x400")

        self.ser = None

        # Port selection
        port_frame = ttk.Frame(root, padding="10")
        port_frame.pack(fill=tk.X)

        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, width=15)
        self.refresh_ports()
        self.port_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(port_frame, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT, padx=2)
        self.connect_btn = ttk.Button(port_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT)

        # Control frame
        control_frame = ttk.Frame(root, padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True)

        # Brightness slider
        ttk.Label(control_frame, text="Brightness (0-255):").pack(pady=5)
        self.brightness_var = tk.IntVar(value=128)
        self.brightness_slider = ttk.Scale(
            control_frame,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.brightness_var,
            command=self.update_brightness
        )
        self.brightness_slider.pack(fill=tk.X, pady=5)

        # Value display
        self.value_label = ttk.Label(control_frame, text="Value: 128")
        self.value_label.pack(pady=5)

        # Buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="LED ON", command=self.led_on).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="LED OFF", command=self.led_off).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Send PWM", command=self.send_pwm).pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = ttk.Label(control_frame, text="Not connected", foreground="red", font=('Arial', 9, 'bold'))
        self.status_label.pack(pady=10)

        # Console output
        console_frame = ttk.LabelFrame(control_frame, text="Console Output", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(console_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.console = tk.Text(console_frame, height=6, width=50, yscrollcommand=scrollbar.set)
        self.console.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.console.yview)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            self.log(f"Available ports: {', '.join(port_list)}")
        else:
            self.log("No ports found!")

    def log(self, message):
        try:
            self.console.insert(tk.END, message + "\n")
            self.console.see(tk.END)
        except:
            pass

    def connect(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.connect_btn.config(text="Connect")
                self.status_label.config(text="Disconnected", foreground="red")
                self.log(">>> Disconnected")
            else:
                port = self.port_var.get()
                if not port:
                    self.status_label.config(text="Please select a port!", foreground="red")
                    self.log("ERROR: No port selected")
                    return

                self.log(f">>> Connecting to {port}...")
                self.ser = serial.Serial(port, 9600, timeout=2)
                time.sleep(2)  # Arduino'nun resetlenmesini bekle

                # Arduino'dan gelen ilk mesajı oku
                while self.ser.in_waiting:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.log(f"Arduino says: {response}")

                self.connect_btn.config(text="Disconnect")
                self.status_label.config(text=f"Connected to {port}", foreground="green")
                self.log(f">>> Successfully connected!")

        except serial.SerialException as e:
            self.status_label.config(text="Connection failed!", foreground="red")
            self.log(f"ERROR: {str(e)}")
            if self.ser:
                self.ser.close()
        except Exception as e:
            self.status_label.config(text=f"Error!", foreground="red")
            self.log(f"ERROR: {str(e)}")

    def send_command(self, command):
        if not self.ser or not self.ser.is_open:
            self.status_label.config(text="Not connected!", foreground="red")
            self.log("ERROR: Not connected to Arduino")
            return False

        try:
            # Komutu gönder
            cmd = command + "\r\n"
            self.ser.write(cmd.encode())
            self.log(f">>> Sent: {command}")
            time.sleep(0.15)

            # Arduino'dan yanıtı oku
            while self.ser.in_waiting:
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    self.log(f"Arduino says: {response}")

            return True

        except Exception as e:
            self.log(f"ERROR sending command: {str(e)}")
            self.status_label.config(text="Send error!", foreground="red")
            return False

    def update_brightness(self, value):
        brightness = int(float(value))
        self.value_label.config(text=f"Value: {brightness}")

    def send_pwm(self):
        brightness = self.brightness_var.get()
        if self.send_command(f"PWM {brightness}"):
            self.status_label.config(text=f"PWM: {brightness}", foreground="blue")

    def led_on(self):
        if self.send_command("ON"):
            self.status_label.config(text="LED ON", foreground="blue")

    def led_off(self):
        if self.send_command("OFF"):
            self.status_label.config(text="LED OFF", foreground="blue")


if __name__ == "__main__":
    root = tk.Tk()
    app = LEDController(root)
    root.mainloop()
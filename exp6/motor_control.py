import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time


class MotorController:
    def __init__(self, root):
        self.root = root
        self.root.title("DC Motor Control")
        self.root.geometry("500x550")

        self.ser = None

        # ===== CONNECTION FRAME =====
        conn_frame = ttk.LabelFrame(root, text="Connection", padding="10")
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conn_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.refresh_ports()
        self.port_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT, padx=2)
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # ===== DIRECTION FRAME =====
        dir_frame = ttk.LabelFrame(root, text="Direction Control", padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=5)

        self.direction_var = tk.StringVar(value="CW")

        ttk.Radiobutton(
            dir_frame,
            text="Clockwise (CW)",
            variable=self.direction_var,
            value="CW",
            command=self.set_direction
        ).pack(anchor=tk.W, pady=3)

        ttk.Radiobutton(
            dir_frame,
            text="Counter-Clockwise (CCW)",
            variable=self.direction_var,
            value="CCW",
            command=self.set_direction
        ).pack(anchor=tk.W, pady=3)

        # ===== SPEED CONTROL FRAME =====
        speed_frame = ttk.LabelFrame(root, text="Speed Control (PWM 0-255)", padding="10")
        speed_frame.pack(fill=tk.X, padx=10, pady=5)

        # Manual PWM Slider
        self.pwm_var = tk.IntVar(value=0)
        self.pwm_slider = ttk.Scale(
            speed_frame,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.pwm_var,
            command=self.update_pwm_display
        )
        self.pwm_slider.pack(fill=tk.X, pady=5)

        self.pwm_label = ttk.Label(speed_frame, text="PWM Value: 0 (0%)", font=('Arial', 10, 'bold'))
        self.pwm_label.pack(pady=5)

        ttk.Button(speed_frame, text="Set Speed", command=self.set_speed, width=15).pack(pady=5)

        # Preset Speed Buttons
        ttk.Label(speed_frame, text="Preset Speed Levels:").pack(pady=5)
        preset_frame = ttk.Frame(speed_frame)
        preset_frame.pack(pady=5)

        speeds = [
            ("25%", 64),
            ("50%", 128),
            ("75%", 191),
            ("100%", 255)
        ]

        for label, value in speeds:
            ttk.Button(
                preset_frame,
                text=label,
                command=lambda v=value: self.set_preset_speed(v),
                width=10
            ).pack(side=tk.LEFT, padx=3)

        # ===== CONTROL BUTTONS FRAME =====
        control_frame = ttk.LabelFrame(root, text="Motor Control", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()

        ttk.Button(
            btn_frame,
            text="STOP",
            command=self.stop_motor,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="BRAKE",
            command=self.brake_motor,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # ===== STATUS =====
        self.status_label = ttk.Label(
            root,
            text="Not connected",
            foreground="red",
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(pady=10)

        # ===== CONSOLE =====
        console_frame = ttk.LabelFrame(root, text="Console Output", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(console_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.console = tk.Text(console_frame, height=8, width=60, yscrollcommand=scrollbar.set)
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
                time.sleep(2)  # Wait for Arduino reset

                # Read initial message from Arduino
                while self.ser.in_waiting:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.log(f"Arduino: {response}")

                self.connect_btn.config(text="Disconnect")
                self.status_label.config(text=f"Connected to {port}", foreground="green")
                self.log(">>> Successfully connected!")

        except Exception as e:
            self.status_label.config(text="Connection failed!", foreground="red")
            self.log(f"ERROR: {str(e)}")
            if self.ser:
                self.ser.close()

    def send_command(self, command):
        if not self.ser or not self.ser.is_open:
            self.status_label.config(text="Not connected!", foreground="red")
            self.log("ERROR: Not connected")
            return False

        try:
            cmd = command + "\r\n"
            self.ser.write(cmd.encode())
            self.log(f">>> Sent: {command}")
            time.sleep(0.15)

            # Read response from Arduino
            while self.ser.in_waiting:
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    self.log(f"Arduino: {response}")

            return True

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.status_label.config(text="Send error!", foreground="red")
            return False

    def update_pwm_display(self, value):
        pwm = int(float(value))
        percentage = int((pwm / 255) * 100)
        self.pwm_label.config(text=f"PWM Value: {pwm} ({percentage}%)")

    def set_direction(self):
        direction = self.direction_var.get()
        if self.send_command(direction):
            dir_text = "Clockwise" if direction == "CW" else "Counter-Clockwise"
            self.status_label.config(text=f"Direction: {dir_text}", foreground="blue")

    def set_speed(self):
        speed = self.pwm_var.get()
        if self.send_command(f"SPEED {speed}"):
            percentage = int((speed / 255) * 100)
            self.status_label.config(text=f"Speed: {speed} ({percentage}%)", foreground="blue")

    def set_preset_speed(self, speed):
        self.pwm_var.set(speed)
        self.pwm_slider.set(speed)
        if self.send_command(f"SPEED {speed}"):
            percentage = int((speed / 255) * 100)
            self.status_label.config(text=f"Speed: {speed} ({percentage}%)", foreground="blue")

    def stop_motor(self):
        if self.send_command("STOP"):
            self.pwm_var.set(0)
            self.status_label.config(text="Motor STOPPED", foreground="orange")

    def brake_motor(self):
        if self.send_command("BRAKE"):
            self.status_label.config(text="Motor BRAKE", foreground="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = MotorController(root)
    root.mainloop()
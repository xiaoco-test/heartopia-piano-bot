import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import mido
import time
import threading
from pynput.keyboard import Controller, Key, Listener

# --- คีย์แมปปิ้งพื้นฐาน (สามารถปรับแต่งให้ตรงกับปุ่มในเกมได้) ---
DEFAULT_MAP = {
    "60": "1", "62": "2", "64": "3", "65": "4", "67": "5", "69": "6", "71": "7",
    "72": "8", "74": "9", "76": "0", "77": "q", "79": "w", "81": "e", "83": "r"
}

class HeartopiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Heartopia Maestro v1.0")
        self.root.geometry("450x550")
        self.root.resizable(False, False)

        self.keyboard = Controller()
        self.midi_path = tk.StringVar()
        self.is_playing = False
        self.transpose_val = tk.IntVar(value=0)
        self.delay_val = tk.IntVar(value=5)
        
        self.setup_ui()

    def setup_ui(self):
        ui_frame = ttk.Frame(self.root, padding="20")
        ui_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(ui_frame, text="Heartopia Auto Piano", font=("Helvetica", 18, "bold")).pack(pady=10)
        
        # ส่วนเลือกไฟล์
        file_frame = ttk.LabelFrame(ui_frame, text=" เลือกไฟล์เพลง (MIDI) ", padding="10")
        file_frame.pack(fill=tk.X, pady=10)
        ttk.Entry(file_frame, textvariable=self.midi_path, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # ส่วนตั้งค่า
        config_frame = ttk.LabelFrame(ui_frame, text=" การตั้งค่า ", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        ttk.Label(config_frame, text="ปรับคีย์ (Transpose):").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=-24, to=24, textvariable=self.transpose_val, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(config_frame, text="เวลารอก่อนเริ่ม (วินาที):").grid(row=1, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.delay_val, width=5).grid(row=1, column=1, padx=5, pady=5)

        # สถานะ
        self.status_label = ttk.Label(ui_frame, text="สถานะ: พร้อมใช้งาน", foreground="blue")
        self.status_label.pack(pady=10)

        # ปุ่มควบคุม
        self.start_btn = ttk.Button(ui_frame, text="▶ เริ่มเล่นเพลง", command=self.start_playback_thread)
        self.start_btn.pack(fill=tk.X, pady=5)
        self.stop_btn = ttk.Button(ui_frame, text="■ หยุดเล่น (ESC)", command=self.stop_playback, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)

        ttk.Label(ui_frame, text="วิธีใช้: กด Start แล้วรีบสลับหน้าจอเข้าเกม\nกด ESC บนคีย์บอร์ดเพื่อหยุดทันที", 
                  font=("Helvetica", 9), foreground="gray", justify=tk.CENTER).pack(pady=20)

    def browse_file(self):
        file = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid;*.midi")])
        if file: self.midi_path.set(file)

    def start_playback_thread(self):
        if not self.midi_path.get():
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ MIDI ก่อน!")
            return
        self.is_playing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        thread = threading.Thread(target=self.play_midi, daemon=True)
        thread.start()
        self.esc_listener = Listener(on_press=self.on_press)
        self.esc_listener.start()

    def on_press(self, key):
        if key == Key.esc:
            self.stop_playback()
            return False

    def stop_playback(self):
        self.is_playing = False
        self.status_label.config(text="สถานะ: หยุดการทำงาน", foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def play_midi(self):
        try:
            mid = mido.MidiFile(self.midi_path.get())
            delay = self.delay_val.get()
            for i in range(delay, 0, -1):
                if not self.is_playing: return
                self.status_label.config(text=f"กำลังจะเริ่มใน {i}...", foreground="orange")
                time.sleep(1)
            self.status_label.config(text="สถานะ: กำลังเล่น...", foreground="green")
            for msg in mid.play():
                if not self.is_playing: break
                if msg.type == 'note_on' and msg.velocity > 0:
                    note_num = msg.note + self.transpose_val.get()
                    key_char = DEFAULT_MAP.get(str(note_num))
                    if key_char: self.keyboard.press(key_char)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    note_num = msg.note + self.transpose_val.get()
                    key_char = DEFAULT_MAP.get(str(note_num))
                    if key_char: self.keyboard.release(key_char)
            self.stop_playback()
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")
            self.stop_playback()

if __name__ == "__main__":
    root = tk.Tk()
    app = HeartopiaApp(root)
    root.mainloop()

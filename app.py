import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import requests
import json
import threading
import math
import queue
import pyttsx3

class OmiCodeAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("O.M.I - AI Coding Assistant")
        self.root.state('zoomed')
        self.root.configure(bg="#000000")

        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = "Omi-fine-llm"
        size = "6.9b"
        
        self.colors = {
            'bg_dark': '#0a0e1a',
            'bg_card': '#1a1a1a',
            'bg_card_hover': '#2a2a2a',
            'accent_red': "#00ff1a",
            'accent_gold': '#ffd700',
            'accent_glow': '#ffdd4b',
            'accent_red_dark': '#b3001b',
            'text_white': '#ffffff',
            'text_gray': '#a0a0a0',
            'success': '#00ff88',
            'processing': '#ffaa00'
        }
        
        self.font_ui = ("Segoe UI", 11)
        self.font_ui_bold = ("Segoe UI", 12, "bold")
        self.font_ui_title = ("Segoe UI", 16, "bold")
        self.font_code = ("Cascadia Code", 11)
        self.font_omi = ("Impact", 48, "bold")

        self.current_mode = "general"
        self.mode_instruction = ""
        self.pulse_state = 0.0
        self.processing_animation_state = 0
        self.active_tool_button = None
        self.is_processing = False
        self.is_speaking = False
        
        self.output_queue = queue.Queue()

        self.setup_styles()
        self.setup_ui()
        self.start_animations()
        
        self.general_mode()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
            background=self.colors['bg_card'],
            foreground=self.colors['text_white'],
            fieldbackground=self.colors['bg_dark'],
            borderwidth=0,
            font=self.font_ui)

        style.configure('TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', background=self.colors['bg_card'])
        
        style.configure('TLabel',
            background=self.colors['bg_dark'],
            foreground=self.colors['text_white'])
        
        style.configure('Card.TLabel', background=self.colors['bg_card'])
        style.configure('Header.TLabel',
            background=self.colors['accent_red'],
            foreground=self.colors['bg_dark'],
            font=self.font_ui_title,
            padding=(20, 10))

        style.configure('Title.TLabel',
            background=self.colors['bg_dark'],
            foreground=self.colors['accent_gold'],
            font=self.font_omi)
        
        style.configure('Subtitle.TLabel',
            background=self.colors['bg_dark'],
            foreground=self.colors['text_gray'],
            font=self.font_ui)

        style.configure('TButton',
            background=self.colors['bg_card'],
            foreground=self.colors['text_gray'],
            font=self.font_ui_bold,
            padding=(15, 12),
            relief=tk.FLAT,
            borderwidth=0)
        
        style.map('TButton',
            background=[('active', self.colors['bg_dark']), ('pressed', self.colors['bg_dark'])],
            foreground=[('active', self.colors['text_white']), ('pressed', self.colors['text_white'])])

        style.configure('Execute.TButton',
            background=self.colors['accent_red'],
            foreground=self.colors['bg_dark'],
            font=("Segoe UI", 14, "bold"),
            padding=(20, 15))
        
        style.map('Execute.TButton',
            background=[('active', self.colors['accent_red_dark']), ('pressed', self.colors['accent_red_dark']),
                        ('disabled', self.colors['bg_card'])],
            foreground=[('disabled', self.colors['text_gray'])])

        style.configure('Tool.TButton',
            font=self.font_ui_bold,
            background=self.colors['bg_dark'],
            foreground=self.colors['text_white'],
            anchor=tk.W,
            padding=(15, 10))
        
        style.map('Tool.TButton',
            background=[('active', self.colors['bg_card']), ('pressed', 'bg_card')],
            foreground=[('active', self.colors['accent_gold']), ('pressed', self.colors['accent_gold'])])

        style.configure('ActiveTool.TButton',
            background=self.colors['bg_card'],
            foreground=self.colors['accent_gold'],
            relief=tk.SOLID,
            bordercolor=self.colors['accent_gold'],
            borderwidth=1)

        style.configure('TPanedwindow', background=self.colors['bg_dark'])
        style.configure('TScrollbar',
            background=self.colors['bg_dark'],
            troughcolor=self.colors['bg_card'],
            bordercolor=self.colors['bg_dark'],
            arrowcolor=self.colors['accent_gold'])
        
        style.map('TScrollbar',
            background=[('active', self.colors['accent_gold']), ('pressed', self.colors['accent_gold'])])

    def setup_ui(self):
        main_container = ttk.Frame(self.root, style='TFrame')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        header = ttk.Frame(main_container, style='TFrame', height=120)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        self.reactor_canvas = tk.Canvas(header, width=100, height=100, bg=self.colors['bg_dark'], highlightthickness=0)
        self.reactor_canvas.pack(side=tk.LEFT, padx=30, pady=10)
        
        self.reactor_circles = [
            self.reactor_canvas.create_oval(0, 0, 0, 0, outline=self.colors['accent_gold'], width=2)
            for _ in range(5)
        ]
        self.reactor_core = self.reactor_canvas.create_oval(0, 0, 0, 0, fill=self.colors['accent_gold'], outline=self.colors['accent_glow'], width=2)

        title_frame = ttk.Frame(header, style='TFrame')
        title_frame.pack(side=tk.LEFT, padx=20, expand=True, fill=tk.BOTH)
        
        self.title_label = ttk.Label(title_frame, text="O.M.I", style='Title.TLabel')
        self.title_label.pack(anchor=tk.W)
        
        ttk.Label(title_frame, text="Om's Multifaceted Intelligence | AI Coding Assistant", style='Subtitle.TLabel').pack(anchor=tk.W)

        status_panel = ttk.Frame(header, style='Card.TFrame')
        status_panel.pack(side=tk.RIGHT, padx=30, pady=20, fill=tk.Y)
        
        ttk.Label(status_panel, text="SYSTEM STATUS", font=self.font_ui, foreground=self.colors['text_gray'], style='Card.TLabel').pack(padx=15, pady=(10, 5))
        self.status_indicator = ttk.Label(status_panel, text="● ONLINE", font=self.font_ui_bold, foreground=self.colors['success'], style='Card.TLabel')
        self.status_indicator.pack(padx=15, pady=(0, 10))
        
        content_frame = ttk.Frame(main_container, style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        left_panel = ttk.Frame(content_frame, width=350, style='Card.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)

        ttk.Label(left_panel, text="⚡ AI CODING TOOLS", style='Header.TLabel', anchor=tk.CENTER).pack(fill=tk.X, pady=(0, 10))
        
        tools_scroll_frame = ttk.Frame(left_panel, style='Card.TFrame')
        tools_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tools_canvas = tk.Canvas(tools_scroll_frame, bg=self.colors['bg_card'], highlightthickness=0)
        tools_scroll = ttk.Scrollbar(tools_scroll_frame, orient="vertical", command=self.tools_canvas.yview)
        self.tools_inner_frame = ttk.Frame(self.tools_canvas, style='Card.TFrame')

        self.tools_canvas.create_window((0, 0), window=self.tools_inner_frame, anchor="nw")
        self.tools_canvas.configure(yscrollcommand=tools_scroll.set)

        self.tools_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tools_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tools_inner_frame.bind("<Configure>", lambda e: self.tools_canvas.configure(scrollregion=self.tools_canvas.bbox("all")))
        
        tools_scroll_frame.bind("<Enter>", lambda e: tools_scroll_frame.bind_all("<MouseWheel>", self._on_mousewheel))
        tools_scroll_frame.bind("<Leave>", lambda e: tools_scroll_frame.unbind_all("<MouseWheel>"))
        
        self.tools = [
            ("🎯 GENERAL MODE", self.general_mode, "General coding assistance", self.colors['accent_red']),
            ("🔍 ANALYZE", self.analyze_mode, "Deep code analysis", self.colors['accent_gold']),
            ("🐛 DEBUG", self.debug_mode, "Find and fix bugs", self.colors['accent_red_dark']),
            ("⚠️ ERROR FINDER", self.error_finder_mode, "Identify all errors", "#ff6b6b"),
            ("✨ CLEAN CODE", self.clean_mode, "Format & optimize", "#51cf66"),
            ("🔄 CONVERT", self.convert_mode, "Language converter", "#748ffc"),
            ("📝 DOCUMENT", self.document_mode, "Generate docs", "#ffd43b"),
            ("🚀 OPTIMIZE", self.optimize_mode, "Performance boost", "#ff8787"),
            ("💡 EXPLAIN", self.explain_mode, "Code explanation", "#9775fa")
        ]
        
        self.tool_buttons = []
        for tool_name, command, desc, color in self.tools:
            self.create_tool_button(tool_name, command, desc, color)

        right_panel = ttk.PanedWindow(content_frame, orient=tk.VERTICAL)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        input_section = ttk.Frame(right_panel, style='Card.TFrame')
        input_section.pack(fill=tk.BOTH, expand=True)
        
        self.input_mode_label = ttk.Label(input_section, text="▶ INPUT YOUR CODE", style='Header.TLabel')
        self.input_mode_label.pack(fill=tk.X, pady=(0, 10))

        input_text_frame = ttk.Frame(input_section, style='TFrame', relief=tk.FLAT, borderwidth=0)
        input_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.input_text = scrolledtext.ScrolledText(
            input_text_frame, wrap=tk.WORD, font=self.font_code,
            bg="#0d1117", fg="#58a6ff", insertbackground=self.colors['accent_gold'],
            relief=tk.FLAT, borderwidth=0, padx=15, pady=15,
            selectbackground=self.colors['accent_gold'], selectforeground=self.colors['bg_dark'],
            insertwidth=3
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        right_panel.add(input_section, weight=40)

        control_frame = ttk.Frame(right_panel, style='TFrame')
        control_frame.pack(fill=tk.X)
        
        buttons_container = ttk.Frame(control_frame, style='TFrame')
        buttons_container.pack(pady=10)

        self.execute_btn = ttk.Button(
            buttons_container, text="⚡ EXECUTE", style='Execute.TButton',
            command=self.execute_command
        )
        self.execute_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(buttons_container, text="🗑 CLEAR", style='TButton', command=self.clear_all).pack(side=tk.LEFT, padx=8)
        ttk.Button(buttons_container, text="📋 COPY", style='TButton', command=self.copy_response).pack(side=tk.LEFT, padx=8)
        
        self.speak_btn = ttk.Button(buttons_container, text="🔊 SPEAK", style='TButton', command=self.speak_response)
        self.speak_btn.pack(side=tk.LEFT, padx=8)

        right_panel.add(control_frame, weight=1)

        output_section = ttk.Frame(right_panel, style='Card.TFrame')
        output_section.pack(fill=tk.BOTH, expand=True)
        
        output_header = ttk.Frame(output_section, style='Card.TFrame')
        output_header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_header, text="▶ O.M.I RESPONSE", style='Header.TLabel').pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.processing_label = ttk.Label(output_header, text="", font=self.font_ui_bold, foreground=self.colors['processing'], style='Card.TLabel')
        self.processing_label.pack(side=tk.RIGHT, padx=20)
        
        output_text_frame = ttk.Frame(output_section, style='TFrame')
        output_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            output_text_frame, wrap=tk.WORD, font=self.font_code,
            bg="#0d1117", fg="#7ee787", relief=tk.FLAT, borderwidth=0,
            padx=15, pady=15, state=tk.DISABLED,
            selectbackground=self.colors['success'], selectforeground=self.colors['bg_dark']
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        right_panel.add(output_section, weight=60)

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.tools_canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:
            self.tools_canvas.yview_scroll(-1, "units")

    def create_tool_button(self, tool_name, command, desc, color):
        card = ttk.Frame(self.tools_inner_frame, style='Card.TFrame')
        card.pack(fill=tk.X, pady=8, padx=5)
        
        accent = tk.Frame(card, bg=color, width=5)
        accent.pack(side=tk.LEFT, fill=tk.Y)
        
        btn_content = ttk.Frame(card, style='Card.TFrame')
        btn_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn = ttk.Button(
            btn_content,
            text=tool_name,
            style='Tool.TButton'
        )
        btn.configure(command=lambda c=command, b=btn: [c(), self.set_active_tool(b)])
        btn.pack(fill=tk.X, padx=(5, 0))
        
        desc_label = ttk.Label(
            btn_content,
            text=desc,
            font=self.font_ui,
            foreground=self.colors['text_gray'],
            style='Card.TLabel',
            anchor=tk.W,
            padding=(15, 0, 0, 5)
        )
        desc_label.pack(fill=tk.X, padx=(5, 0))

        def on_enter(e, widgets):
            for w in widgets:
                w.configure(background=self.colors['bg_card_hover'])
                
        def on_leave(e, widgets):
            for w in widgets:
                w.configure(background=self.colors['bg_card'])

        card_widgets = [card, btn_content, desc_label]
        
        card.bind("<Enter>", lambda e, w=card_widgets: on_enter(e, w))
        card.bind("<Leave>", lambda e, w=card_widgets: on_leave(e, w))
        btn_content.bind("<Enter>", lambda e, w=card_widgets: on_enter(e, w))
        btn_content.bind("<Leave>", lambda e, w=card_widgets: on_leave(e, w))
        desc_label.bind("<Enter>", lambda e, w=card_widgets: on_enter(e, w))
        desc_label.bind("<Leave>", lambda e, w=card_widgets: on_leave(e, w))

        self.tool_buttons.append(btn)


    def set_active_tool(self, button_to_activate):
        if self.active_tool_button:
            self.active_tool_button.configure(style='Tool.TButton')
            
        self.active_tool_button = button_to_activate
        self.active_tool_button.configure(style='ActiveTool.TButton')

    def start_animations(self):
        self.animate_reactor()
        self.animate_title_glow()

    def animate_reactor(self):
        self.pulse_state = (self.pulse_state + 0.05) % (2 * math.pi)
        
        core_scale = 0.8 + 0.2 * abs(math.sin(self.pulse_state * 2))
        core_radius = 15 * core_scale
        self.reactor_canvas.coords(self.reactor_core, 50 - core_radius, 50 - core_radius, 50 + core_radius, 50 + core_radius)
        
        for i, circle in enumerate(self.reactor_circles):
            ring_pulse = 0.95 + 0.05 * abs(math.sin(self.pulse_state + (i * math.pi / 5)))
            radius = (i + 1) * 8 * ring_pulse
            self.reactor_canvas.coords(circle, 50 - radius, 50 - radius, 50 + radius, 50 + radius)
            
        self.root.after(30, self.animate_reactor)

    def animate_title_glow(self):
        g = int(215 + 40 * abs(math.sin(self.pulse_state * 2)))
        r = 255
        b = int(100 + 50 * abs(math.sin(self.pulse_state * 2)))
        color = f'#{r:02x}{g:02x}{b:02x}'
        self.title_label.configure(foreground=color)
        self.root.after(30, self.animate_title_glow)

    def animate_processing(self):
        if not self.is_processing:
            self.processing_label.config(text="")
            return
            
        dots = "." * (self.processing_animation_state % 4)
        self.processing_label.config(text=f"⚙ PROCESSING{dots}")
        self.processing_animation_state += 1
        self.root.after(500, self.animate_processing)

    def update_status(self, message, color):
        self.status_indicator.config(text=f"● {message}", foreground=color)

    def set_mode(self, mode, instruction, label_text):
        self.current_mode = mode
        self.mode_instruction = instruction
        self.input_mode_label.config(text=label_text)
        self.update_status(f"MODE: {mode.upper()}", self.colors['accent_gold'])

    def general_mode(self):
        self.set_mode("general", "", "▶ INPUT YOUR CODE OR QUESTION")
        self.set_active_tool(self.tool_buttons[0])

    def analyze_mode(self):
        self.set_mode("analyze", "Analyze the following code comprehensively:\n\n", "▶ INPUT CODE FOR ANALYSIS")

    def debug_mode(self):
        self.set_mode("debug", "Debug this code and fix all issues:\n\n", "▶ INPUT CODE TO DEBUG")

    def error_finder_mode(self):
        self.set_mode("error", "Find all errors in this code:\n\n", "▶ INPUT CODE FOR ERROR DETECTION")

    def clean_mode(self):
        self.set_mode("clean", "Clean and format this code:\n\n", "▶ INPUT CODE TO CLEAN")

    def convert_mode(self):
        target_lang = simpledialog.askstring("Language Converter", "Target programming language:", parent=self.root)
        if target_lang:
            self.set_mode("convert", f"Convert this code to {target_lang}:\n\n", f"▶ CONVERTING TO {target_lang.upper()}")
        else:
            active_mode_name_start = self.current_mode.upper()
            for i, tool in enumerate(self.tools):
                tool_name_simple = tool[0].split(" ")[-1]
                if tool_name_simple == active_mode_name_start or (tool_name_simple == "MODE" and active_mode_name_start == "GENERAL"):
                    self.set_active_tool(self.tool_buttons[i])
                    break

    def document_mode(self):
        self.set_mode("document", "Generate documentation for this code:\n\n", "▶ INPUT CODE TO DOCUMENT")

    def optimize_mode(self):
        self.set_mode("optimize", "Optimize this code:\n\n", "▶ INPUT CODE TO OPTIMIZE")

    def explain_mode(self):
        self.set_mode("explain", "Explain this code in detail:\n\n", "▶ INPUT CODE TO EXPLAIN")

    def execute_command(self):
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("Input Required", "Sir, I need code or an instruction to proceed.")
            return
        
        prompt = f"{self.mode_instruction}{user_input}"
        
        self.execute_btn.config(state=tk.DISABLED)
        self.speak_btn.config(state=tk.DISABLED)
        self.update_status("PROCESSING", self.colors['processing'])
        self.is_processing = True
        self.animate_processing()
        
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
        
        thread = threading.Thread(target=self.call_omi_api, args=(prompt,))
        thread.daemon = True
        thread.start()
        
        self.process_output_queue()

    def process_output_queue(self):
        try:
            while True:
                token = self.output_queue.get_nowait()
                
                if token == "__DONE__":
                    self.is_processing = False
                    self.processing_label.config(text="✓ COMPLETE")
                    self.update_status("READY", self.colors['success'])
                    self.execute_btn.config(state=tk.NORMAL)
                    self.speak_btn.config(state=tk.NORMAL)
                    return
                elif token.startswith("__ERROR__"):
                    self.is_processing = False
                    self.show_error(token.replace("__ERROR__", ""))
                    return
                
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, token)
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)

        except queue.Empty:
            if self.is_processing:
                self.root.after(50, self.process_output_queue)

    def call_omi_api(self, prompt):
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True
            }
            
            response = requests.post(self.api_url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        token = json_response.get("response", "")
                        self.output_queue.put(token)
                        
                        if json_response.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.ConnectionError:
            self.output_queue.put("__ERROR__Sir, my connection to the local model failed. Please ensure Ollama is running on localhost:11434.")
        except requests.exceptions.RequestException as e:
            self.output_queue.put(f"__ERROR__API Error: {str(e)}")
        except Exception as e:
            self.output_queue.put(f"__ERROR__System Error: {str(e)}")
        finally:
            self.output_queue.put("__DONE__")

    def show_error(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, f"\n\n⚠️ SYSTEM ERROR: {message}\n")
        self.output_text.config(state=tk.DISABLED)
        
        self.update_status("ERROR", self.colors['accent_red'])
        self.processing_label.config(text="✗ FAILED")
        self.execute_btn.config(state=tk.NORMAL)
        self.speak_btn.config(state=tk.NORMAL)
        messagebox.showerror("O.M.I Error", message)

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.processing_label.config(text="")
        self.update_status("READY", self.colors['success'])
        self.general_mode()

    def copy_response(self):
        response = self.output_text.get("1.0", tk.END).strip()
        if response:
            self.root.clipboard_clear()
            self.root.clipboard_append(response)
            self.update_status("COPIED", self.colors['accent_gold'])
            messagebox.showinfo("Success", "Copied to clipboard, Sir.")
        else:
            messagebox.showwarning("Empty", "No response to copy, Sir.")

    def speak_response(self):
        if self.is_speaking:
            messagebox.showwarning("In Progress", "Speech is already in progress, Sir.")
            return
        
        response_text = self.output_text.get("1.0", tk.END).strip()
        
        if not response_text:
            messagebox.showwarning("Empty", "No response to speak, Sir.")
            return

        self.is_speaking = True
        self.speak_btn.config(state=tk.DISABLED)
        self.update_status("SPEAKING", self.colors['accent_gold'])
        
        thread = threading.Thread(target=self._run_tts, args=(response_text,))
        thread.daemon = True
        thread.start()

    def _run_tts(self, text):
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"TTS Error: {e}")
            self.output_queue.put(f"__ERROR__TTS failed: {e}")
        finally:
            self.root.after(0, self.on_speech_end)

    def on_speech_end(self):
        self.is_speaking = False
        self.speak_btn.config(state=tk.NORMAL)
        if not self.is_processing:
            self.update_status("READY", self.colors['success'])

if __name__ == "__main__":
    root = tk.Tk()
    app = OmiCodeAssistant(root)
    root.mainloop()


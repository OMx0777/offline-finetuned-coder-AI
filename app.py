import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading

class DeepSeekCodingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("OM's Offline coding Assistant JARVIS")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")
        
        # Ollama API endpoint
        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = "Malicus7862/deepseekcoder-6.7b-jarvis-gguf"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(
            main_frame, 
            text="🤖 OM's Offline coding Assistant JARVIS",
            font=("Segoe UI", 16, "bold"),
            bg="#1e1e1e",
            fg="#00d9ff"
        )
        title.pack(pady=(0, 10))
        
        # Top section - Input area
        input_frame = tk.LabelFrame(
            main_frame,
            text="Your Question / Code Request",
            font=("Segoe UI", 11, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief=tk.GROOVE,
            bd=2
        )
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Middle section - Control buttons
        control_frame = tk.Frame(main_frame, bg="#1e1e1e")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Generate button
        self.generate_btn = tk.Button(
            control_frame,
            text="🚀 Generate Code",
            font=("Segoe UI", 11, "bold"),
            bg="#0078d4",
            fg="#ffffff",
            activebackground="#005a9e",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.generate_code
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = tk.Button(
            control_frame,
            text="🗑️ Clear All",
            font=("Segoe UI", 11),
            bg="#3c3c3c",
            fg="#ffffff",
            activebackground="#2d2d2d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.clear_all
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Copy button
        copy_btn = tk.Button(
            control_frame,
            text="📋 Copy Response",
            font=("Segoe UI", 11),
            bg="#3c3c3c",
            fg="#ffffff",
            activebackground="#2d2d2d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.copy_response
        )
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="Ready",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Bottom section - Output area
        output_frame = tk.LabelFrame(
            main_frame,
            text="DeepSeek Response",
            font=("Segoe UI", 11, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief=tk.GROOVE,
            bd=2
        )
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def update_status(self, message, color="#00ff00"):
        self.status_label.config(text=message, fg=color)
        
    def generate_code(self):
        prompt = self.input_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("Input Required", "Please enter a question or code request!")
            return
        
        # Disable button during generation
        self.generate_btn.config(state=tk.DISABLED)
        self.update_status("Generating...", "#ffaa00")
        
        # Clear previous output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self.call_ollama_api, args=(prompt,))
        thread.daemon = True
        thread.start()
        
    def call_ollama_api(self, prompt):
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True
            }
            
            response = requests.post(self.api_url, json=payload, stream=True)
            
            if response.status_code == 200:
                full_response = ""
                
                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line)
                            token = json_response.get("response", "")
                            full_response += token
                            
                            # Update UI in main thread
                            self.root.after(0, self.append_output, token)
                            
                            if json_response.get("done", False):
                                self.root.after(0, self.update_status, "Complete!", "#00ff00")
                                self.root.after(0, self.generate_btn.config, {"state": tk.NORMAL})
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                self.root.after(0, self.show_error, error_msg)
                
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama. Make sure it's running on localhost:11434"
            self.root.after(0, self.show_error, error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self.show_error, error_msg)
            
    def append_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def show_error(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message)
        self.output_text.config(state=tk.DISABLED)
        self.update_status("Error occurred", "#ff0000")
        self.generate_btn.config(state=tk.NORMAL)
        messagebox.showerror("Error", message)
        
    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.update_status("Ready", "#00ff00")
        
    def copy_response(self):
        response = self.output_text.get("1.0", tk.END).strip()
        if response:
            self.root.clipboard_clear()
            self.root.clipboard_append(response)
            self.update_status("Copied to clipboard!", "#00d9ff")
            messagebox.showinfo("Success", "Response copied to clipboard!")
        else:
            messagebox.showwarning("Nothing to Copy", "No response to copy!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekCodingTool(root)
    root.mainloop()
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from pathlib import Path
import openai
from datetime import datetime
import pygame
import unicodedata
import locale

class TextToSpeechGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Text-to-Speech Converter")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        # Set UTF-8 encoding for better Vietnamese support
        try:
            # Try to set locale to the user's default with UTF-8 encoding
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Track the current audio file
        self.current_audio_file = None
        
        # Available voices
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Available models
        self.available_models = ["tts-1", "tts-1-hd"]
        
        # Available languages (with focus on Vietnamese)
        self.available_languages = [
            ("Auto-detect", ""),
            ("Vietnamese", "vi"),
            ("English", "en"),
            ("French", "fr"),
            ("German", "de"),
            ("Spanish", "es"),
            ("Chinese", "zh"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("Thai", "th")
        ]
        
        # Create output directory
        self.output_dir = Path("tts_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create GUI elements
        self.create_widgets()
        
        # Configure style for better Unicode/Vietnamese display
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial Unicode MS', 10))
        self.style.configure('TLabel', font=('Arial Unicode MS', 10))
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API Key section
        api_frame = ttk.LabelFrame(main_frame, text="OpenAI API Key", padding="10")
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_cb = ttk.Checkbutton(api_frame, text="Show Key", variable=self.show_key_var, 
                                         command=self.toggle_api_key_visibility)
        self.show_key_cb.grid(row=0, column=2, padx=5)
        
        # Text input section
        text_frame = ttk.LabelFrame(main_frame, text="Text Input", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_input = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=80, height=10)
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons for text operations
        text_buttons_frame = ttk.Frame(text_frame)
        text_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(text_buttons_frame, text="Load Text File", command=self.load_text_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(text_buttons_frame, text="Clear Text", command=self.clear_text).pack(side=tk.LEFT, padx=5)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="TTS Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Voice selection
        ttk.Label(options_frame, text="Voice:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.voice_var = tk.StringVar(value="nova")
        voice_combo = ttk.Combobox(options_frame, textvariable=self.voice_var, values=self.available_voices, width=15)
        voice_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        voice_combo.state(['readonly'])
        
        # Model selection
        ttk.Label(options_frame, text="Model:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value="tts-1")
        model_combo = ttk.Combobox(options_frame, textvariable=self.model_var, values=self.available_models, width=15)
        model_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        model_combo.state(['readonly'])
        
        # Language selection
        ttk.Label(options_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.language_var = tk.StringVar(value="")
        self.language_display_var = tk.StringVar(value="Auto-detect")
        
        # Create language dropdown with display names
        language_combo = ttk.Combobox(options_frame, textvariable=self.language_display_var, width=15)
        language_combo['values'] = [lang[0] for lang in self.available_languages]
        language_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        language_combo.state(['readonly'])
        
        # Bind language selection to update the actual language code
        language_combo.bind('<<ComboboxSelected>>', self.update_language_code)
        
        # Output file
        ttk.Label(options_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_file_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.output_file_var, width=40).grid(row=2, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(options_frame, text="Browse", command=self.browse_output_file).grid(row=2, column=3, padx=5, pady=5)
        
        # Vietnamese text encoding
        self.normalize_text_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Normalize Vietnamese text (NFC)", 
                       variable=self.normalize_text_var).grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.convert_button = ttk.Button(action_frame, text="Convert to Speech", command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.play_button = ttk.Button(action_frame, text="Play Audio", command=self.play_audio, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(action_frame, text="Stop Audio", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def toggle_api_key_visibility(self):
        """Toggle showing/hiding the API key"""
        if self.show_key_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")
    
    def load_text_file(self):
        """Load text from a file into the text input field"""
        file_path = filedialog.askopenfilename(
            title="Select Text File", 
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                encodings = ['utf-8', 'utf-16', 'cp1258']  # Try multiple encodings for Vietnamese support
                text = None
                
                # Try different encodings
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            text = file.read()
                            break
                    except UnicodeDecodeError:
                        continue
                
                if text is None:
                    raise UnicodeDecodeError("None of the encodings worked")
                
                # Normalize text for Vietnamese if selected
                if self.normalize_text_var.get():
                    text = unicodedata.normalize('NFC', text)
                    
                self.text_input.delete(1.0, tk.END)
                self.text_input.insert(tk.END, text)
                self.status_var.set(f"Loaded text from: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    def update_language_code(self, event):
        """Update the language code based on the selected display name"""
        selected_display = self.language_display_var.get()
        
        # Find the corresponding language code
        for lang_name, lang_code in self.available_languages:
            if lang_name == selected_display:
                self.language_var.set(lang_code)
                break
    
    def clear_text(self):
        """Clear the text input field"""
        self.text_input.delete(1.0, tk.END)
        self.status_var.set("Text cleared")
    
    def browse_output_file(self):
        """Browse for output file location"""
        file_path = filedialog.asksaveasfilename(
            title="Save Audio As",
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            initialdir=self.output_dir
        )
        
        if file_path:
            self.output_file_var.set(file_path)
    
    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        # Get text from input field
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to convert")
            return
        
        # Get API key
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your OpenAI API key")
            return
        
        # Disable buttons during conversion
        self.convert_button.configure(state=tk.DISABLED)
        self.status_var.set("Converting text to speech...")
        
        # Start conversion in a separate thread
        threading.Thread(target=self.convert_text_to_speech, daemon=True).start()
    
    def convert_text_to_speech(self):
        """Convert text to speech using OpenAI API"""
        try:
            # Configure API
            openai.api_key = self.api_key_var.get().strip()
            
            # Get input parameters
            text = self.text_input.get(1.0, tk.END).strip()
            voice = self.voice_var.get()
            model = self.model_var.get()
            language_code = self.language_var.get()
            output_file = self.output_file_var.get()
            
            # Normalize Vietnamese text if needed
            if self.normalize_text_var.get():
                text = unicodedata.normalize('NFC', text)
            
            # Generate default output file if not specified
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                lang_suffix = f"_{language_code}" if language_code else ""
                output_file = str(self.output_dir / f"speech_{voice}{lang_suffix}_{timestamp}.mp3")
                self.root.after(0, lambda: self.output_file_var.set(output_file))
            
            # Prepare speech parameters
            speech_params = {
                "model": model,
                "voice": voice,
                "input": text,
                "response_format": "mp3"
            }
            
            # Show status update about language if specified
            if language_code:
                selected_language = next((name for name, code in self.available_languages if code == language_code), "Unknown")
                self.root.after(0, lambda: self.status_var.set(f"Converting text in {selected_language}..."))
            
            # Make API request
            response = openai.audio.speech.create(**speech_params)
            
            # Save the audio file
            response.stream_to_file(output_file)
            
            # Update status and enable buttons
            self.current_audio_file = output_file
            self.root.after(0, self.update_ui_after_conversion)
            
        except Exception as e:
            # Show error message
            self.root.after(0, lambda: messagebox.showerror("Error", f"Conversion failed: {e}"))
            self.root.after(0, lambda: self.status_var.set("Conversion failed"))
            self.root.after(0, lambda: self.convert_button.configure(state=tk.NORMAL))
    
    def update_ui_after_conversion(self):
        """Update UI after successful conversion"""
        self.status_var.set(f"Audio saved to: {self.current_audio_file}")
        self.convert_button.configure(state=tk.NORMAL)
        self.play_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.NORMAL)
        messagebox.showinfo("Success", f"Text converted to speech successfully!\nSaved to: {self.current_audio_file}")
    
    def play_audio(self):
        """Play the generated audio file"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                # Stop any currently playing audio
                pygame.mixer.music.stop()
                
                # Load and play the new audio
                pygame.mixer.music.load(self.current_audio_file)
                pygame.mixer.music.play()
                
                self.status_var.set(f"Playing: {self.current_audio_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play audio: {e}")
        else:
            messagebox.showwarning("Warning", "No audio file available. Convert text to speech first.")
    
    def stop_audio(self):
        """Stop playing the audio"""
        pygame.mixer.music.stop()
        self.status_var.set("Audio playback stopped")

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = TextToSpeechGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import os
import threading
import sys
import webbrowser
import time
import srt
import subprocess
import shutil
import requests
from pathlib import Path

# Import from existing translation module
from gemini_srt_translate import translate_text, translate_srt
from faster_whisper_extract_srt import extract_subtitles_with_whisper
import google.generativeai as genai

class SRTTranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SRT Translator & Subtitle Extractor")
        self.root.geometry("1000x1100")
        self.root.minsize(800, 800)
        
        # Set high DPI awareness for crisp display
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Configure styles
        self.setup_styles()
        
        # Translation Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.api_key = tk.StringVar()
        self.target_lang = tk.StringVar(value="Chinese")
        self.proxy_enabled = tk.BooleanVar(value=True)
        self.proxy_url = tk.StringVar(value="http://127.0.0.1:7890")
        self.model_name = tk.StringVar(value="gemini-2.5-flash")
        
        # Whisper Variables
        self.video_file = tk.StringVar()
        self.whisper_output = tk.StringVar()
        self.local_model_path = tk.StringVar(value="")
        self.whisper_device = tk.StringVar(value="auto")
        self.selected_model = tk.StringVar(value="Select a model...")
        
        # Merge Variables
        self.merge_video_file = tk.StringVar()
        self.merge_srt_file = tk.StringVar()
        self.merge_output_file = tk.StringVar()
        
        # Font settings for merge
        self.font_size = tk.StringVar(value="16")
        self.font_color = tk.StringVar(value="ffffff")  # Default white
        self.font_outline_color = tk.StringVar(value="000000")  # Default black
        self.font_outline_width = tk.StringVar(value="1")
        self.font_name = tk.StringVar(value="Arial")
        self.font_bold = tk.BooleanVar(value=False)
        self.font_italic = tk.BooleanVar(value=False)
        
        # Position settings for merge
        self.subtitle_position = tk.StringVar(value="bottom")
        self.margin_vertical = tk.StringVar(value="25")
        self.margin_horizontal = tk.StringVar(value="20")
        
        # Advanced settings for merge
        self.video_codec = tk.StringVar(value="libx264")
        self.audio_codec = tk.StringVar(value="aac")
        self.video_quality = tk.StringVar(value="23")
        self.subtitle_encoding = tk.StringVar(value="utf-8")
        
        # Control flags
        self.stop_extraction = False
        self.stop_translation = False
        self.stop_download = False
        self.is_merging = False
        self.merge_process = None
        
        self.setup_styles()
        self.setup_additional_styles()
        
        self.setup_ui()
        
    def setup_styles(self):
        """Configure ttk styles for better appearance"""
        style = ttk.Style()
        
        # Use modern theme
        try:
            style.theme_use('vista')  # Modern Windows theme
        except:
            style.theme_use('clam')   # Fallback theme
        
        # Configure button styles
        style.configure('Action.TButton', 
                       padding=(25, 18),
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Stop.TButton',
                       padding=(25, 18),
                       font=('Segoe UI', 16))
        
        # Configure small button styles for Browse, Save As, Help buttons
        style.configure('Small.TButton',
                       padding=(15, 10),
                       font=('Segoe UI', 14))
        
        # Configure checkbox style
        style.configure('Large.TCheckbutton',
                       font=('Segoe UI', 16))
        
        # Configure combobox style - need special handling for dropdown
        style.configure('TCombobox',
                       font=('Segoe UI', 16),
                       fieldbackground='white')
        
        # Configure combobox dropdown - this is the key part
        style.map('TCombobox', 
                  fieldbackground=[('readonly', 'white')],
                  selectbackground=[('readonly', '#0078d4')])
        
        # Configure the dropdown listbox font
        self.root.option_add('*TCombobox*Listbox.font', ('Segoe UI', 16))
        
    def setup_combobox_font(self, combo, font_size=16):
        """Configure combobox with large font for both display and dropdown"""
        combo.configure(font=('Segoe UI', font_size))
        
    def disable_combobox_mousewheel(self, combo, target_canvas=None):
        """Disable combobox internal mouse wheel and redirect to page scrolling"""
        def _on_combobox_mousewheel(event):
            # Block combobox's internal scroll behavior and let page scroll instead
            if target_canvas and isinstance(target_canvas, tk.Canvas):
                # Scroll the specified canvas instead of the combobox
                target_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                # Find the parent canvas to scroll the page
                parent = event.widget
                while parent and not isinstance(parent, tk.Canvas):
                    parent = parent.master
                
                if parent and isinstance(parent, tk.Canvas):
                    # Scroll the canvas instead of the combobox
                    parent.yview_scroll(int(-1*(event.delta/120)), "units")
            
            return "break"  # Stop the event from reaching combobox
        
        # Permanently bind mouse wheel to redirect to page scrolling
        combo.bind("<MouseWheel>", _on_combobox_mousewheel)
        combo.bind("<Button-4>", _on_combobox_mousewheel)  # Linux mouse wheel up
        combo.bind("<Button-5>", _on_combobox_mousewheel)  # Linux mouse wheel down
        
    def setup_additional_styles(self):
        """Setup additional styles for enhanced appearance"""
        style = ttk.Style()
        
        # Configure frame styles - cleaner look
        style.configure('Card.TFrame',
                       relief='flat',
                       borderwidth=0,
                       padding=35)
        
        # Configure label styles with better contrast
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       foreground='#1a1a1a')
        
        style.configure('Section.TLabel',
                       font=('Segoe UI', 16, 'bold'),
                       foreground='#2d3748')
        
        style.configure('Info.TLabel',
                       font=('Segoe UI', 14),
                       foreground='#718096')
        
        # Configure notebook style
        style.configure('TNotebook.Tab',
                       padding=[35, 20],
                       font=('Segoe UI', 16, 'bold'))
        
        # Configure LabelFrame style
        style.configure('TLabelframe',
                       relief='flat',
                       borderwidth=1,
                       lightcolor='#e2e8f0',
                       darkcolor='#e2e8f0')
        
        style.configure('TLabelframe.Label',
                       font=('Segoe UI', 15, 'bold'),
                       foreground='#4a5568')
        
    def setup_ui(self):
        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Create notebook for tabs with improved styling
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True, pady=(0, 10))
        
        # Translation tab
        translate_frame = ttk.Frame(notebook)
        notebook.add(translate_frame, text="📝 Translation")
        self.setup_translate_tab(translate_frame)
        
        # Whisper extraction tab
        whisper_frame = ttk.Frame(notebook)
        notebook.add(whisper_frame, text="🎤 Extraction")
        self.setup_whisper_tab(whisper_frame)
        
        # Video merge tab
        merge_frame = ttk.Frame(notebook)
        notebook.add(merge_frame, text="🎬 Video Merge")
        self.setup_merge_tab(merge_frame)
        
        # Add status bar
        self.setup_status_bar(main_container)
        
    def bind_mousewheel(self, canvas):
        """Bind mouse wheel events to canvas for scrolling"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        # Bind mouse wheel when entering canvas area
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
    def setup_status_bar(self, parent):
        """Add a status bar at the bottom"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Separator(status_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 8))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Info.TLabel')
        status_label.pack(side=tk.LEFT)
        
        # Version info with cleaner design
        version_label = ttk.Label(status_frame, text="Powered by Gemini & Whisper", style='Info.TLabel')
        version_label.pack(side=tk.RIGHT)
        
    def setup_translate_tab(self, parent):
        # Main scrollable frame
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrollable frame to expand
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make scrollable_frame fill canvas width
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Also bind canvas resize to update scrollable frame width
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        # Bind mouse wheel
        self.bind_mousewheel(canvas)
        
        # Main container with cleaner layout - fill entire width
        main_frame = ttk.Frame(scrollable_frame, style='Card.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title - cleaner design
        title_label = ttk.Label(main_frame, text="SRT Translation", style='Title.TLabel')
        title_label.pack(fill=tk.X, pady=(0, 40))
        
        # API Configuration Section - full width
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="15")
        api_frame.pack(fill=tk.X, pady=(0, 20))
        api_frame.columnconfigure(1, weight=1)  # Make column 1 expandable
        api_frame.columnconfigure(2, weight=0)  # Keep column 2 fixed for buttons
        
        ttk.Label(api_frame, text="API Key:", style='Section.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        key_entry = ttk.Entry(api_frame, textvariable=self.api_key, show="*", font=('Consolas', 18))
        key_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 0))
        
        ttk.Label(api_frame, text="Model:", style='Section.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_name)
        model_combo['values'] = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        model_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 0))
        self.setup_combobox_font(model_combo, 18)
        self.disable_combobox_mousewheel(model_combo, canvas)
        
        # Proxy settings
        ttk.Label(api_frame, text="Proxy:", style='Section.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        proxy_frame = ttk.Frame(api_frame)
        proxy_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(15, 0))
        proxy_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(proxy_frame, text="Use Proxy", variable=self.proxy_enabled, style='Large.TCheckbutton').grid(row=0, column=0, sticky=tk.W)
        proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_url, font=('Consolas', 18))
        proxy_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(15, 0))
        
        # File Configuration Section - full width
        file_frame = ttk.LabelFrame(main_frame, text="Files & Language", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        file_frame.columnconfigure(1, weight=1)  # Make column 1 expandable
        
        # Input file
        ttk.Label(file_frame, text="Input SRT:", style='Section.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        input_entry = ttk.Entry(file_frame, textvariable=self.input_file, font=('Consolas', 18))
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(file_frame, text="Browse", command=self.browse_input_file, style='Small.TButton').grid(row=0, column=2, pady=(0, 10))
        
        # Output file
        ttk.Label(file_frame, text="Output SRT:", style='Section.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        output_entry = ttk.Entry(file_frame, textvariable=self.output_file, font=('Consolas', 18))
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(file_frame, text="Save As", command=self.browse_output_file, style='Small.TButton').grid(row=1, column=2, pady=(0, 10))
        
        # Target language
        ttk.Label(file_frame, text="Target Language:", style='Section.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        lang_combo = ttk.Combobox(file_frame, textvariable=self.target_lang)
        lang_combo['values'] = ["Chinese", "English", "Japanese", "Korean", "Spanish", "French", "German", "Italian", "Portuguese", "Russian"]
        lang_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(15, 0))
        self.setup_combobox_font(lang_combo, 18)
        self.disable_combobox_mousewheel(lang_combo, canvas)
        
        # Action buttons - cleaner design
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=25)
        
        self.translate_btn = ttk.Button(button_frame, text="🚀 Start Translation", 
                                      command=self.start_translation, style='Action.TButton')
        self.translate_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_translate_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                           command=self.stop_translation_process, 
                                           state="disabled", style='Stop.TButton')
        self.stop_translate_btn.pack(side=tk.LEFT)
        
        # Progress section - full width
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready to translate", style='Info.TLabel')
        self.status_label.pack(fill=tk.X)
        
        # Log output with cleaner styling - full width
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="15")
        log_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, 
                                                 font=('Consolas', 16), wrap=tk.WORD,
                                                 bg='#f8f9fa', relief='flat', borderwidth=1)
        self.log_text.pack(fill='both', expand=True)
        
        def _on_translate_log_mousewheel(event):
            self.log_text.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break" 
        
        def _bind_translate_log_mousewheel(event):
            self.log_text.bind_all("<MouseWheel>", _on_translate_log_mousewheel)
        
        def _unbind_translate_log_mousewheel(event):
            def canvas_mousewheel(e):
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            self.log_text.bind_all("<MouseWheel>", canvas_mousewheel)
        
        self.log_text.bind('<Enter>', _bind_translate_log_mousewheel)
        self.log_text.bind('<Leave>', _unbind_translate_log_mousewheel)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_whisper_tab(self, parent):
        # Main scrollable frame
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrollable frame to expand
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make scrollable_frame fill canvas width
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Also bind canvas resize to update scrollable frame width
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        # Bind mouse wheel
        self.bind_mousewheel(canvas)
        
        # Main container - fill entire width
        whisper_main = ttk.Frame(scrollable_frame, style='Card.TFrame')
        whisper_main.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(whisper_main, text="Subtitle Extraction", style='Title.TLabel')
        title_label.pack(fill=tk.X, pady=(0, 40))
        
        # Input/Output Section - full width
        io_frame = ttk.LabelFrame(whisper_main, text="Files", padding="15")
        io_frame.pack(fill=tk.X, pady=(0, 20))
        io_frame.columnconfigure(1, weight=1)  # Make column 1 expandable
        
        # Video input
        ttk.Label(io_frame, text="Video File:", style='Section.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        video_entry = ttk.Entry(io_frame, textvariable=self.video_file, font=('Consolas', 18))
        video_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(io_frame, text="Browse", command=self.browse_video_file, style='Small.TButton').grid(row=0, column=2, pady=(0, 10))
        
        # Output SRT
        ttk.Label(io_frame, text="Output SRT:", style='Section.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        whisper_output_entry = ttk.Entry(io_frame, textvariable=self.whisper_output, font=('Consolas', 18))
        whisper_output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(io_frame, text="Save As", command=self.browse_whisper_output, style='Small.TButton').grid(row=1, column=2, pady=(0, 10))
        
        # Model Configuration Section - full width
        model_frame = ttk.LabelFrame(whisper_main, text="Configuration", padding="15")
        model_frame.pack(fill=tk.X, pady=(0, 20))
        
        # First row: Device and Model Selection
        config_row1 = ttk.Frame(model_frame)
        config_row1.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(config_row1, text="Device:", style='Section.TLabel').pack(side=tk.LEFT)
        device_combo = ttk.Combobox(config_row1, textvariable=self.whisper_device)
        device_combo['values'] = ["cpu", "cuda", "auto"]
        device_combo.pack(side=tk.LEFT, padx=(12, 30))
        self.setup_combobox_font(device_combo, 18)
        self.disable_combobox_mousewheel(device_combo, canvas)
        
        ttk.Label(config_row1, text="Model:", style='Section.TLabel').pack(side=tk.LEFT)
        model_combo = ttk.Combobox(config_row1, textvariable=self.selected_model, state="readonly")
        model_combo['values'] = [
            "Select a model...",
            "tiny", "tiny.en", 
            "base", "base.en",
            "small", "small.en",
            "medium", "medium.en",
            "large-v1", "large-v2", "large-v3"
        ]
        model_combo.pack(side=tk.LEFT, padx=(12, 0))
        self.setup_combobox_font(model_combo, 18)
        self.disable_combobox_mousewheel(model_combo, canvas)
        model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)
        
        # Local Model Path
        ttk.Label(model_frame, text="Local Model Path:", style='Section.TLabel').pack(anchor=tk.W, pady=(12, 8))
        model_path_frame = ttk.Frame(model_frame)
        model_path_frame.pack(fill=tk.X, pady=(0, 8))
        
        model_path_entry = ttk.Entry(model_path_frame, textvariable=self.local_model_path, font=('Consolas', 18))
        model_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(model_path_frame, text="Browse", command=self.browse_local_model, style='Small.TButton').pack(side=tk.LEFT, padx=(8, 6))
        ttk.Button(model_path_frame, text="Help", command=self.show_model_help, style='Small.TButton').pack(side=tk.LEFT)
        
        ttk.Label(model_frame, text="Leave empty to download automatically", style='Info.TLabel').pack(anchor=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(whisper_main)
        button_frame.pack(fill=tk.X, pady=25)
        
        self.extract_btn = ttk.Button(button_frame, text="🚀 Extract Subtitles", 
                                    command=self.start_extraction, style='Action.TButton')
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_extract_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                         command=self.stop_extraction_process, 
                                         state="disabled", style='Stop.TButton')
        self.stop_extract_btn.pack(side=tk.LEFT)
        
        # Progress section - full width
        progress_frame = ttk.LabelFrame(whisper_main, text="Progress", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.whisper_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.whisper_progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.whisper_status_label = ttk.Label(progress_frame, text="Ready to extract", style='Info.TLabel')
        self.whisper_status_label.pack(fill=tk.X)
        
        # Log output - full width，增加高度并优化滚动优先级
        log_frame = ttk.LabelFrame(whisper_main, text="Log", padding="15")
        log_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.whisper_log = scrolledtext.ScrolledText(log_frame, height=12, 
                                                   font=('Consolas', 16), wrap=tk.WORD,
                                                   bg='#f8f9fa', relief='flat', borderwidth=1)
        self.whisper_log.pack(fill='both', expand=True)
        
        def _on_log_mousewheel(event):
            self.whisper_log.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break" 
        
        def _bind_log_mousewheel(event):
            self.whisper_log.bind_all("<MouseWheel>", _on_log_mousewheel)
        
        def _unbind_log_mousewheel(event):
            def canvas_mousewheel(e):
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            self.whisper_log.bind_all("<MouseWheel>", canvas_mousewheel)
        
        self.whisper_log.bind('<Enter>', _bind_log_mousewheel)
        self.whisper_log.bind('<Leave>', _unbind_log_mousewheel)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_merge_tab(self, parent):
        """Setup the video merge tab"""
        # Main scrollable frame
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrollable frame to expand
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        # Bind mouse wheel
        self.bind_mousewheel(canvas)
        
        # Main container
        merge_main = ttk.Frame(scrollable_frame, style='Card.TFrame')
        merge_main.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(merge_main, text="Video Subtitle Merge", style='Title.TLabel')
        title_label.pack(fill=tk.X, pady=(0, 30))
        
        # Files Section
        files_section = ttk.LabelFrame(merge_main, text="Input Files", padding="15")
        files_section.pack(fill=tk.X, pady=(0, 20))
        files_section.columnconfigure(1, weight=1)
        
        # Video file
        ttk.Label(files_section, text="Video File:", style='Section.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        merge_video_entry = ttk.Entry(files_section, textvariable=self.merge_video_file, font=('Consolas', 16))
        merge_video_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(files_section, text="Browse", command=self.browse_merge_video_file, style='Small.TButton').grid(row=0, column=2, pady=(0, 10))
        
        # SRT file
        ttk.Label(files_section, text="Subtitle File:", style='Section.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        merge_srt_entry = ttk.Entry(files_section, textvariable=self.merge_srt_file, font=('Consolas', 16))
        merge_srt_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(files_section, text="Browse", command=self.browse_merge_srt_file, style='Small.TButton').grid(row=1, column=2, pady=(0, 10))
        
        # Output file
        ttk.Label(files_section, text="Output File:", style='Section.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        merge_output_entry = ttk.Entry(files_section, textvariable=self.merge_output_file, font=('Consolas', 16))
        merge_output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 10), padx=(15, 10))
        ttk.Button(files_section, text="Save As", command=self.browse_merge_output_file, style='Small.TButton').grid(row=2, column=2, pady=(0, 10))
        
        # Font Settings Section
        font_section = ttk.LabelFrame(merge_main, text="Font Settings", padding="15")
        font_section.pack(fill=tk.X, pady=(0, 20))
        
        # Font basic settings row
        font_row1 = ttk.Frame(font_section)
        font_row1.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(font_row1, text="Font:", style='Section.TLabel').pack(side=tk.LEFT)
        font_combo = ttk.Combobox(font_row1, textvariable=self.font_name, width=15)
        font_combo['values'] = ["Arial", "Times New Roman", "Verdana", "Georgia", "Courier New", 
                               "Trebuchet MS", "Comic Sans MS", "Impact", "Lucida Console"]
        font_combo.pack(side=tk.LEFT, padx=(10, 20))
        self.setup_combobox_font(font_combo, 16)
        self.disable_combobox_mousewheel(font_combo, canvas)
        
        ttk.Label(font_row1, text="Size:", style='Section.TLabel').pack(side=tk.LEFT)
        size_spin = ttk.Spinbox(font_row1, textvariable=self.font_size, from_=8, to=100, width=8, 
                               font=('Consolas', 16))
        size_spin.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Checkbutton(font_row1, text="Bold", variable=self.font_bold, style='Large.TCheckbutton').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(font_row1, text="Italic", variable=self.font_italic, style='Large.TCheckbutton').pack(side=tk.LEFT)
        
        # Color settings row
        color_row = ttk.Frame(font_section)
        color_row.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(color_row, text="Font Color:", style='Section.TLabel').pack(side=tk.LEFT)
        self.font_color_btn = ttk.Button(color_row, text="■", command=self.choose_merge_font_color, width=5)
        self.font_color_btn.pack(side=tk.LEFT, padx=(10, 10))
        self.font_color_label = ttk.Label(color_row, text=f"#{self.font_color.get()}", font=('Consolas', 16))
        self.font_color_label.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(color_row, text="Outline Color:", style='Section.TLabel').pack(side=tk.LEFT)
        self.outline_color_btn = ttk.Button(color_row, text="■", command=self.choose_merge_outline_color, width=5)
        self.outline_color_btn.pack(side=tk.LEFT, padx=(10, 10))
        self.outline_color_label = ttk.Label(color_row, text=f"#{self.font_outline_color.get()}", font=('Consolas', 16))
        self.outline_color_label.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(color_row, text="Outline Width:", style='Section.TLabel').pack(side=tk.LEFT)
        outline_spin = ttk.Spinbox(color_row, textvariable=self.font_outline_width, from_=0, to=10, width=8, font=('Consolas', 16))
        outline_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Position settings row
        position_row = ttk.Frame(font_section)
        position_row.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(position_row, text="Position:", style='Section.TLabel').pack(side=tk.LEFT)
        pos_combo = ttk.Combobox(position_row, textvariable=self.subtitle_position, width=12)
        pos_combo['values'] = ["bottom", "top", "center"]
        pos_combo.pack(side=tk.LEFT, padx=(10, 20))
        self.setup_combobox_font(pos_combo, 16)
        self.disable_combobox_mousewheel(pos_combo, canvas)
        
        ttk.Label(position_row, text="V-Margin:", style='Section.TLabel').pack(side=tk.LEFT)
        v_margin_spin = ttk.Spinbox(position_row, textvariable=self.margin_vertical, from_=0, to=200, width=8, font=('Consolas', 16))
        v_margin_spin.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(position_row, text="H-Margin:", style='Section.TLabel').pack(side=tk.LEFT)
        h_margin_spin = ttk.Spinbox(position_row, textvariable=self.margin_horizontal, from_=0, to=200, width=8, font=('Consolas', 16))
        h_margin_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Font Preview Section
        preview_section = ttk.LabelFrame(font_section, text="Font Preview", padding="10")
        preview_section.pack(fill=tk.X, pady=(12, 0))
        
        # Preview controls row
        preview_controls = ttk.Frame(preview_section)
        preview_controls.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(preview_controls, text="Preview Text:", style='Section.TLabel').pack(side=tk.LEFT)
        self.preview_text = tk.StringVar(value="Sample subtitle text 字幕预览")
        preview_entry = ttk.Entry(preview_controls, textvariable=self.preview_text, font=('Consolas', 14), width=25)
        preview_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        ttk.Button(preview_controls, text="🔄 Update Preview", command=self.update_font_preview, style='Small.TButton').pack(side=tk.LEFT)
        
        # Preview display area
        self.font_preview_canvas = tk.Canvas(
            preview_section, 
            bg='white',
            height=80, 
            highlightthickness=0
        )
        self.font_preview_canvas.pack(fill=tk.X, expand=True, pady=(8, 0))
        
        # Bind changes to auto-update preview
        self.font_name.trace_add('write', lambda *args: self.update_font_preview())
        self.font_size.trace_add('write', lambda *args: self.update_font_preview())
        self.font_bold.trace_add('write', lambda *args: self.update_font_preview())
        self.font_italic.trace_add('write', lambda *args: self.update_font_preview())
        self.font_color.trace_add('write', lambda *args: self.update_font_preview())
        self.preview_text.trace_add('write', lambda *args: self.update_font_preview())
        self.font_outline_color.trace_add('write', lambda *args: self.update_font_preview())
        self.font_outline_width.trace_add('write', lambda *args: self.update_font_preview())
        
        # Advanced Settings Section
        advanced_section = ttk.LabelFrame(merge_main, text="Advanced Settings", padding="15")
        advanced_section.pack(fill=tk.X, pady=(0, 20))
        
        # Codec settings row
        codec_row = ttk.Frame(advanced_section)
        codec_row.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(codec_row, text="Video Codec:", style='Section.TLabel').pack(side=tk.LEFT)
        video_codec_combo = ttk.Combobox(codec_row, textvariable=self.video_codec, width=12)
        video_codec_combo['values'] = ["libx264", "libx265", "libvpx-vp9", "copy"]
        video_codec_combo.pack(side=tk.LEFT, padx=(10, 20))
        self.setup_combobox_font(video_codec_combo, 16)
        self.disable_combobox_mousewheel(video_codec_combo, canvas)
        
        ttk.Label(codec_row, text="Audio Codec:", style='Section.TLabel').pack(side=tk.LEFT)
        audio_codec_combo = ttk.Combobox(codec_row, textvariable=self.audio_codec, width=12)
        audio_codec_combo['values'] = ["aac", "mp3", "copy"]
        audio_codec_combo.pack(side=tk.LEFT, padx=(10, 20))
        self.setup_combobox_font(audio_codec_combo, 16)
        self.disable_combobox_mousewheel(audio_codec_combo, canvas)
        
        ttk.Label(codec_row, text="Quality (CRF):", style='Section.TLabel').pack(side=tk.LEFT)
        quality_spin = ttk.Spinbox(codec_row, textvariable=self.video_quality, from_=0, to=51, width=8, font=('Consolas', 16))
        quality_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Encoding settings row
        encoding_row = ttk.Frame(advanced_section)
        encoding_row.pack(fill=tk.X)
        
        ttk.Label(encoding_row, text="Subtitle Encoding:", style='Section.TLabel').pack(side=tk.LEFT)
        encoding_combo = ttk.Combobox(encoding_row, textvariable=self.subtitle_encoding, width=12)
        encoding_combo['values'] = ["utf-8", "gbk", "gb2312", "big5"]
        encoding_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.setup_combobox_font(encoding_combo, 16)
        self.disable_combobox_mousewheel(encoding_combo, canvas)
        
        # Action buttons
        button_frame = ttk.Frame(merge_main)
        button_frame.pack(fill=tk.X, pady=25)
        
        self.merge_btn = ttk.Button(button_frame, text="🚀 Start Merge", 
                                   command=self.start_merge, style='Action.TButton')
        self.merge_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_merge_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                        command=self.stop_merge, 
                                        state="disabled", style='Stop.TButton')
        self.stop_merge_btn.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(merge_main, text="Progress", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.merge_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.merge_progress.pack(fill=tk.X, pady=(0, 10))
        
        # self.progress_label = ttk.Label(progress_frame, text="Ready to merge", 
        #                         style='Info.TLabel', anchor='w', justify=tk.LEFT,
        #                         font=('Consolas', 16)) 
        self.progress_label = ttk.Label(
            progress_frame, 
            text="Ready to merge", 
            style='Info.TLabel', 
            anchor='w',
            justify=tk.LEFT, 
            font=('Consolas', 14)
        )
        self.progress_label.pack(fill=tk.X, expand=True)
        
        def configure_progress_label_wrap(event):
            width = event.width
            self.progress_label.config(wraplength=max(width - 20, 1))
        progress_frame.bind('<Configure>', configure_progress_label_wrap)
        
        # Log section
        log_frame = ttk.LabelFrame(merge_main, text="Processing Log", padding="15")
        log_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.merge_log = scrolledtext.ScrolledText(log_frame, height=12, 
                                                  font=('Consolas', 16), wrap=tk.WORD,
                                                  bg='#f8f9fa', relief='flat', borderwidth=1)
        self.merge_log.pack(fill='both', expand=True)
        
        def _on_merge_log_mousewheel(event):
            self.merge_log.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        def _bind_merge_log_mousewheel(event):
            self.merge_log.bind_all("<MouseWheel>", _on_merge_log_mousewheel)
        
        def _unbind_merge_log_mousewheel(event):
            def canvas_mousewheel(e):
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            self.merge_log.bind_all("<MouseWheel>", canvas_mousewheel)
        
        self.merge_log.bind('<Enter>', _bind_merge_log_mousewheel)
        self.merge_log.bind('<Leave>', _unbind_merge_log_mousewheel)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def browse_input_file(self):
        filename = filedialog.askopenfilename(
            title="Select Input SRT File",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            self.status_var.set(f"Input file selected: {os.path.basename(filename)}")
            # Auto-set output filename
            if not self.output_file.get():
                base_name = os.path.splitext(filename)[0]
                self.output_file.set(f"{base_name}_translated.srt")
                
    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save Translated SRT File",
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            self.status_var.set(f"Output file set: {os.path.basename(filename)}")
            
    def browse_video_file(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"), ("All files", "*.*")]
        )
        if filename:
            self.video_file.set(filename)
            self.status_var.set(f"Video file selected: {os.path.basename(filename)}")
            # Auto-set output filename
            if not self.whisper_output.get():
                base_name = os.path.splitext(filename)[0]
                self.whisper_output.set(f"{base_name}.srt")
                
    def browse_whisper_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save Subtitle File",
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.whisper_output.set(filename)
            self.status_var.set(f"Subtitle output set: {os.path.basename(filename)}")
            
    def browse_local_model(self):
        """Browse for local Whisper model directory"""
        directory = filedialog.askdirectory(
            title="Select Local Whisper Model Directory"
        )
        if directory:
            self.local_model_path.set(directory)
            
    def stop_extraction_process(self):
        """Stop the extraction process"""
        self.stop_extraction = True
        self.whisper_log_message("Stopping extraction...")
        self.stop_extract_btn.config(state="disabled")
        
    def stop_translation_process(self):
        """Stop the translation process"""
        self.stop_translation = True
        self.log("Stopping translation...")
        self.stop_translate_btn.config(state="disabled")
            
    def handle_no_local_model(self):
        """Handle case when no local model is found"""
        result = messagebox.askyesno(
            "No Local Model Found",
            "Local Whisper model not found. Would you like to:\n\n"
            "• Yes: Open Hugging Face to download model\n"
            "• No: Cancel extraction",
            icon="question"
        )
        
        if result is True:  # Yes - Open website
            webbrowser.open("https://huggingface.co/collections/Systran/faster-whisper-6867ecec0e757ee14896e2d3")
            return "download"
        else:  # Cancel
            return "cancel"
    
    def on_model_selected(self, event):
        """Handle model selection from dropdown"""
        selected_model = self.selected_model.get()
        if selected_model != "Select a model...":
            result = messagebox.askyesno(
                "Download Model",
                f"Do you want to download the '{selected_model}' model?\n\n"
                f"The model will be downloaded to:\n{os.path.join(os.getcwd(), 'Models', selected_model)}\n\n"
                "This may take several minutes depending on model size.",
                icon="question"
            )
            
            if result:
                self.download_model(selected_model)
            else:
                # Reset selection if user cancels
                self.selected_model.set("Select a model...")
    
    def download_model(self, model_name):
        """Download the selected Whisper model"""
        self.stop_download = False
        self.whisper_log_message(f"Starting download of {model_name} model...")
        
        # Disable buttons during download
        self.extract_btn.config(state="disabled")
        
        # Run download in separate thread
        threading.Thread(target=self._download_model_thread, args=(model_name,), daemon=True).start()
    
    def _download_model_thread(self, model_name):
        """Download model in separate thread"""
        try:
            # Create Models directory if it doesn't exist
            models_dir = os.path.join(os.getcwd(), "Models")
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
                self.whisper_log_message(f"Created Models directory: {models_dir}")
            
            model_path = os.path.join(models_dir, model_name)
            
            # Check if model already exists
            if os.path.exists(model_path) and os.listdir(model_path):
                self.whisper_log_message(f"Model {model_name} already exists at {model_path}")
                self.local_model_path.set(model_path)
                self.whisper_log_message("✅ Model path set successfully!")
                return
            
            self.whisper_log_message(f"Downloading {model_name} from Hugging Face...")
            self.whisper_log_message("This may take a few minutes depending on your internet connection...")
            
            # Use huggingface_hub to download the model
            try:
                from huggingface_hub import snapshot_download
                from tqdm import tqdm
                import sys
                
                # Map model names to repository names
                model_repos = {
                    "tiny": "Systran/faster-whisper-tiny",
                    "tiny.en": "Systran/faster-whisper-tiny.en", 
                    "base": "Systran/faster-whisper-base",
                    "base.en": "Systran/faster-whisper-base.en",
                    "small": "Systran/faster-whisper-small",
                    "small.en": "Systran/faster-whisper-small.en",
                    "medium": "Systran/faster-whisper-medium",
                    "medium.en": "Systran/faster-whisper-medium.en",
                    "large-v1": "Systran/faster-whisper-large-v1",
                    "large-v2": "Systran/faster-whisper-large-v2",
                    "large-v3": "Systran/faster-whisper-large-v3"
                }
                
                repo_id = model_repos.get(model_name)
                if not repo_id:
                    raise ValueError(f"Unknown model: {model_name}")
                
                # Create a custom progress callback
                def progress_callback(progress_info):
                    if hasattr(progress_info, 'desc') and hasattr(progress_info, 'n') and hasattr(progress_info, 'total'):
                        if progress_info.total and progress_info.total > 0:
                            percent = int((progress_info.n / progress_info.total) * 100)
                            # Format file size
                            def format_bytes(bytes_val):
                                if bytes_val < 1024:
                                    return f"{bytes_val}B"
                                elif bytes_val < 1024**2:
                                    return f"{bytes_val/1024:.1f}kB"
                                elif bytes_val < 1024**3:
                                    return f"{bytes_val/(1024**2):.1f}MB"
                                else:
                                    return f"{bytes_val/(1024**3):.2f}GB"
                            
                            current_size = format_bytes(progress_info.n)
                            total_size = format_bytes(progress_info.total)
                            
                            # Calculate download speed
                            elapsed = getattr(progress_info, 'elapsed', 0)
                            if elapsed > 0:
                                speed = progress_info.n / elapsed
                                speed_str = f"{format_bytes(speed)}/s"
                            else:
                                speed_str = "calculating..."
                            
                            status_msg = f"{progress_info.desc}: {percent}% | {current_size}/{total_size} [{speed_str}]"
                            self.whisper_log_message(status_msg)
                
                # Redirect stdout to capture tqdm progress
                class ProgressCapture:
                    def __init__(self, log_func):
                        self.log_func = log_func
                        self.buffer = ""
                        self.last_update = 0
                        import time
                        self.start_time = time.time()
                    
                    def write(self, text):
                        self.buffer += text
                        # Process complete lines
                        while '\r' in self.buffer or '\n' in self.buffer:
                            if '\r' in self.buffer:
                                line, self.buffer = self.buffer.split('\r', 1)
                            else:
                                line, self.buffer = self.buffer.split('\n', 1)
                            
                            if line.strip():
                                # Filter and format progress messages
                                if any(keyword in line for keyword in ['%|', 'MB/s', 'kB/s', 'GB/s', 'Fetching', 'files:', 'model.bin:', 'tokenizer.json:', 'config.json:']):
                                    # Clean up the progress line
                                    clean_line = line.strip()
                                    # Remove ANSI escape codes
                                    import re
                                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                                    # Remove excessive whitespace
                                    clean_line = re.sub(r'\s+', ' ', clean_line)
                                    
                                    if clean_line:
                                        # Throttle updates to avoid log spam
                                        import time
                                        current_time = time.time()
                                        if current_time - self.last_update > 1.0:  # Update every second
                                            self.log_func(f"📥 {clean_line}")
                                            self.last_update = current_time
                    
                    def flush(self):
                        pass
                
                # Create progress capture
                progress_capture = ProgressCapture(self.whisper_log_message)
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                
                try:
                    # Redirect stdout and stderr to capture progress
                    sys.stdout = progress_capture
                    sys.stderr = progress_capture
                    
                    # Download the model
                    downloaded_path = snapshot_download(
                        repo_id=repo_id,
                        local_dir=model_path,
                        local_dir_use_symlinks=False,
                        tqdm_class=tqdm  # Use tqdm for progress display
                    )
                finally:
                    # Restore stdout and stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                
                self.whisper_log_message(f"✅ Model {model_name} downloaded successfully!")
                self.whisper_log_message(f"Model saved to: {model_path}")
                
                # Set the local model path
                self.local_model_path.set(model_path)
                self.whisper_log_message("Model path updated automatically.")
                
                messagebox.showinfo(
                    "Download Complete", 
                    f"Model '{model_name}' has been downloaded successfully!\n\nPath: {model_path}"
                )
                
            except ImportError as ie:
                # Check if it's missing huggingface_hub or tqdm
                if "huggingface_hub" in str(ie):
                    # Fallback: Install huggingface_hub if not available
                    self.whisper_log_message("Installing huggingface_hub...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
                    self.whisper_log_message("huggingface_hub installed. Please try downloading again.")
                    messagebox.showinfo("Installation", "Required dependency installed. Please try downloading the model again.")
                elif "tqdm" in str(ie):
                    # Install tqdm for progress display
                    self.whisper_log_message("Installing tqdm for progress display...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
                    self.whisper_log_message("tqdm installed. Please try downloading again.")
                    messagebox.showinfo("Installation", "Progress display library installed. Please try downloading the model again.")
                else:
                    # Try without progress display
                    self.whisper_log_message("Progress display not available, downloading without detailed progress...")
                    from huggingface_hub import snapshot_download
                    downloaded_path = snapshot_download(
                        repo_id=repo_id,
                        local_dir=model_path,
                        local_dir_use_symlinks=False
                    )
                
        except Exception as e:
            error_msg = f"Error downloading model {model_name}: {str(e)}"
            self.whisper_log_message(f"❌ {error_msg}")
            messagebox.showerror("Download Error", error_msg)
        finally:
            # Re-enable buttons
            self.extract_btn.config(state="normal")
            self.stop_download = False
            
    def show_model_help(self):
        """Show help information about local models"""
        help_text = """Local Whisper Model Help:

Two ways to get models:

1. Automatic Download (Recommended):
   - Use the "Model" dropdown to select a model
   - Click on a model name to download it automatically
   - Models will be saved to the "Models" folder
   - Path will be set automatically after download

2. Manual Download:
   - Download from: https://huggingface.co/collections/Systran/faster-whisper-6867ecec0e757ee14896e2d3
   - Extract to a folder and browse to select it
   
Available models:
- tiny/tiny.en: ~39MB, fastest but least accurate
- base/base.en: ~74MB, good balance of speed/accuracy  
- small/small.en: ~244MB, better accuracy
- medium/medium.en: ~769MB, high accuracy
- large-v1/v2/v3: ~1550MB, best accuracy but slowest

English-specific models (*.en) are optimized for English only."""

        # Create help window
        help_window = tk.Toplevel(self.root)
        help_window.title("Local Model Help")
        help_window.geometry("700x500")
        help_window.resizable(True, True)
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10, font=('Segoe UI', 18))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        # Add download button
        btn_frame = ttk.Frame(help_window)
        btn_frame.pack(pady=10)
        ttk.Button(
            btn_frame, 
            text="Open Hugging Face", 
            command=lambda: webbrowser.open("https://huggingface.co/collections/Systran/faster-whisper-6867ecec0e757ee14896e2d3"),
            style='Small.TButton'
        ).pack()
        
    def log(self, message):
        """Add message to log area"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.status_var.set(message)
        self.root.update()
        
    def whisper_log_message(self, message):
        """Add message to whisper log area"""
        self.whisper_log.insert(tk.END, f"{message}\n")
        self.whisper_log.see(tk.END)
        self.status_var.set(message)
        self.root.update()
        
    def translate_srt_file(self):
        """Use existing translate_srt function with progress tracking"""
        try:
            self.log("Reading SRT file...")
            # Read SRT file to calculate total batches
            with open(self.input_file.get(), "r", encoding="utf-8") as f:
                srt_content = f.read()
            
            import srt
            subtitles = list(srt.parse(srt_content))
            batch_size = 10
            total_batches = len(subtitles) // batch_size + (1 if len(subtitles) % batch_size else 0)
            
            self.log(f"Found {len(subtitles)} subtitles, processing in {total_batches} batches")
            
            # Set progress bar maximum
            self.progress.config(maximum=total_batches)
            self.progress['value'] = 0
            
            # Use custom translation logic to track progress
            success = self.translate_with_progress(subtitles, batch_size, total_batches)
            
            if success and not self.stop_translation:
                self.log("✅ Translation completed successfully!")
                self.status_var.set("Translation completed successfully!")
                messagebox.showinfo("Success", "Translation completed!")
            elif self.stop_translation:
                self.log("⚠️ Translation stopped by user.")
                self.status_var.set("Translation stopped by user")
                messagebox.showinfo("Stopped", "Translation stopped by user.")
            
        except Exception as e:
            error_msg = f"Error during translation: {e}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
        finally:
            self.translate_btn.config(state="normal")
            self.stop_translate_btn.config(state="disabled")
            self.progress['value'] = 0
            self.stop_translation = False
            
    def translate_with_progress(self, subtitles, batch_size, total_batches):
        """Custom translation with progress tracking"""
        import srt
        import time
                
        translated_subs = []
        
        for i in range(0, len(subtitles), batch_size):
            # Check if user requested stop
            if self.stop_translation:
                self.log("Translation stopped by user request.")
                return False
                
            current_batch = i // batch_size + 1
            self.log(f"Translating batch {current_batch} of {total_batches}...")
            
            batch = subtitles[i:i+batch_size]
            batch_text = "\n".join(sub.content for sub in batch)
            
            # Log original text (first few lines for preview)
            preview_lines = batch_text.split('\n')[:3]
            self.log(f"Original text preview: {' | '.join(preview_lines)}")
            
            try:
                translated = translate_text(batch_text, self.target_lang.get())
                
                # Log translated text preview
                translated_preview = translated.strip().split('\n')[:3]
                self.log(f"Translated preview: {' | '.join(translated_preview)}")
                
            except Exception as e:
                self.log(f"API error in batch {current_batch}: {e}")
                # Continue with original text if translation fails
                translated = batch_text
            
            translated_lines = translated.strip().split("\n")
            for j, sub in enumerate(batch):
                if j < len(translated_lines):
                    sub.content = translated_lines[j]
                translated_subs.append(sub)
            
            # Update progress bar
            self.progress['value'] = current_batch
            self.root.update()
            
            self.log(f"Batch {current_batch} completed.")
            time.sleep(2)  # Avoid API rate limiting
        
        if not self.stop_translation:
            # Save translated file
            with open(self.output_file.get(), "w", encoding="utf-8") as f:
                f.write(srt.compose(translated_subs))
            self.log(f"File saved to: {self.output_file.get()}")
            return True
        else:
            self.log("Translation stopped.")
            return False
            
    def extract_subtitles(self):
        """Extract subtitles using Whisper"""
        try:
            self.whisper_log_message("Starting subtitle extraction...")
            self.whisper_progress.start() 
            local_path = self.local_model_path.get().strip()
            if not local_path or not os.path.exists(local_path):
                self.whisper_log_message(f"Local model path not found: {local_path}")
                action = self.handle_no_local_model()
                
                if action == "cancel":
                    self.whisper_log_message("Extraction cancelled by user.")
                    return
                else:
                    self.whisper_log_message("Please download the model and restart extraction.")
                    return

            # Check for stop request before starting
            if self.stop_extraction:
                self.whisper_log_message("Extraction stopped before starting.")
                return
            
            output_file = extract_subtitles_with_whisper(
                video_path=self.video_file.get(),
                output_path=self.whisper_output.get(),
                local_model_path=local_path,
                device=self.whisper_device.get(),
                log_callback=self.whisper_log_message,
                stop_callback=lambda: self.stop_extraction
            )
            
            if not self.stop_extraction:
                self.whisper_progress['value'] = 100
                self.whisper_log_message(f"✅ Extraction completed! Saved to: {output_file}")
                self.status_var.set("Subtitle extraction completed!")
                messagebox.showinfo("Success", "Subtitle extraction completed!")
            else:
                self.whisper_log_message("⚠️ Extraction stopped by user.")
                self.status_var.set("Extraction stopped by user")
                messagebox.showinfo("Stopped", "Subtitle extraction stopped by user.")
            
        except Exception as e:
            error_msg = f"Error during extraction: {e}"
            self.whisper_log_message(error_msg)
            messagebox.showerror("Error", error_msg)
        finally:
            self.extract_btn.config(state="normal")
            self.stop_extract_btn.config(state="disabled")
            self.whisper_progress.stop()
            self.stop_extraction = False 
            
    def start_extraction(self):
        """Start subtitle extraction (run in new thread)"""
        # Validate input
        if not self.video_file.get() or not os.path.exists(self.video_file.get()):
            messagebox.showerror("Error", "Please select a valid video file")
            return
            
        if not self.whisper_output.get():
            messagebox.showerror("Error", "Please set output file path")
            return
            
        # Reset stop flag and disable/enable buttons
        self.stop_extraction = False
        self.extract_btn.config(state="disabled")
        self.stop_extract_btn.config(state="normal")
        self.whisper_log_message("Starting extraction...")
        
        # Run extraction in new thread
        threading.Thread(target=self.extract_subtitles, daemon=True).start()
            
    def start_translation(self):
        """Start translation (run in new thread)"""
        # Validate input
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter Google API Key")
            return
            
        if not self.model_name.get():
            messagebox.showerror("Error", "Please select or enter a Gemini model")
            return
            
        if not self.input_file.get() or not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Please select a valid input SRT file")
            return
            
        if not self.output_file.get():
            messagebox.showerror("Error", "Please set output file path")
            return
            
        # Set proxy
        if self.proxy_enabled.get():
            os.environ["HTTP_PROXY"] = self.proxy_url.get()
            os.environ["HTTPS_PROXY"] = self.proxy_url.get()
            self.log(f"Proxy enabled: {self.proxy_url.get()}")
        else:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            self.log("No proxy used")
            
        # Configure Gemini API (update the global configuration)
        try:
            genai.configure(api_key=self.api_key.get())
            # Update the global model in the imported module
            import gemini_srt_translate
            gemini_srt_translate.model = genai.GenerativeModel(self.model_name.get())
            self.log(f"API configuration successful with model: {self.model_name.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"API configuration failed: {e}")
            return
            
        # Disable button, start progress bar
        self.stop_translation = False
        self.translate_btn.config(state="disabled")
        self.stop_translate_btn.config(state="normal")
        self.progress['value'] = 0
        self.log("Starting translation...")
        
        # Run translation in new thread
        threading.Thread(target=self.translate_srt_file, daemon=True).start()
    
    # Merge tab methods
    def browse_merge_video_file(self):
        """Browse for merge video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"), ("All files", "*.*")]
        )
        if filename:
            self.merge_video_file.set(filename)
            self.status_var.set(f"Video selected: {os.path.basename(filename)}")
            # Auto-set output filename
            if not self.merge_output_file.get():
                base_name = os.path.splitext(filename)[0]
                self.merge_output_file.set(f"{base_name}_with_subtitles.mp4")
    
    def browse_merge_srt_file(self):
        """Browse for merge SRT file"""
        filename = filedialog.askopenfilename(
            title="Select SRT File",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.merge_srt_file.set(filename)
            self.status_var.set(f"Subtitle selected: {os.path.basename(filename)}")
    
    def browse_merge_output_file(self):
        """Browse for merge output file"""
        filename = filedialog.asksaveasfilename(
            title="Save Output Video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.merge_output_file.set(filename)
            self.status_var.set(f"Output set: {os.path.basename(filename)}")
    
    def choose_merge_font_color(self):
        """Choose font color for merge"""
        color = colorchooser.askcolor(title="Choose Font Color")
        if color[1]:  # color[1] is hex color like '#ffffff'
            hex_color = color[1].lstrip('#')  # Remove # to get 'ffffff'
            self.font_color.set(hex_color)
            self.font_color_label.config(text=color[1])  # Show with # for display
    
    def choose_merge_outline_color(self):
        """Choose outline color for merge"""
        color = colorchooser.askcolor(title="Choose Outline Color")
        if color[1]:  # color[1] is hex color like '#000000'
            hex_color = color[1].lstrip('#')  # Remove # to get '000000'
            self.font_outline_color.set(hex_color)
            self.outline_color_label.config(text=color[1])  # Show with # for display
    
    def update_font_preview(self):
        """在 Canvas 上更新字体预览，包括描边效果"""
        try:
            # 1. 获取所有需要的设置
            font_name = self.font_name.get() or 'Arial'
            font_size = int(self.font_size.get() or 15)
            is_bold = self.font_bold.get()
            is_italic = self.font_italic.get()
            preview_text = self.preview_text.get() or 'Sample subtitle text 字幕预览'
            
            # 获取主颜色和描边颜色，并确保它们是 Tkinter 可用的格式 (e.g., '#ffffff')
            font_color_hex = f"#{self.font_color.get() or 'ffffff'}"
            outline_color_hex = f"#{self.font_outline_color.get() or '000000'}"
            
            # 获取描边宽度
            outline_width = int(self.font_outline_width.get() or 0)

            # 2. 准备字体
            weight = 'bold' if is_bold else 'normal'
            slant = 'italic' if is_italic else 'roman'
            preview_font = (font_name, font_size, weight, slant)

            # 3. 在 Canvas 上绘制
            canvas = self.font_preview_canvas
            # 清空上一次的绘制内容
            canvas.delete("all")
            
            # 获取 Canvas 的中心点坐标
            # 我们需要等待 Canvas 实际显示出来才能获取准确宽高，但这里可以先获取配置值
            canvas.update_idletasks() # 确保获取最新的尺寸信息
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            center_x, center_y = width / 2, height / 2

            # 4. 绘制描边 (如果宽度大于0)
            if outline_width > 0:
                # 在8个方向上绘制描边文字，形成一个较粗的轮廓
                for dx in [-outline_width, 0, outline_width]:
                    for dy in [-outline_width, 0, outline_width]:
                        if dx == 0 and dy == 0:
                            continue # 跳过中心点
                        canvas.create_text(
                            center_x + dx, center_y + dy,
                            text=preview_text,
                            font=preview_font,
                            fill=outline_color_hex, # 使用描边颜色
                            anchor=tk.CENTER
                        )

            # 5. 最后在顶部绘制主颜色的文字
            canvas.create_text(
                center_x, center_y,
                text=preview_text,
                font=preview_font,
                fill=font_color_hex, # 使用主体颜色
                anchor=tk.CENTER
            )
            
        except Exception as e:
            # 在预览出错时，可以打印错误信息帮助调试
            # print(f"Error updating font preview: {e}")
            pass
    
    def merge_log_message(self, message):
        """Add message to merge log"""
        self.merge_log.insert(tk.END, f"{message}\n")
        self.merge_log.see(tk.END)
        
        # Only update status bar for non-error messages
        if not any(keyword in message.lower() for keyword in ['error', 'failed', 'unable', 'invalid', 'cannot']):
            # Update status bar only for progress or success messages
            if any(keyword in message.lower() for keyword in ['starting', 'completed', 'processing', 'merge']):
                self.status_var.set("Processing video merge...")
        
        self.root.update()
    
    def build_ffmpeg_command(self):
        """Build FFmpeg command for merging"""
        if not self.merge_video_file.get() or not self.merge_srt_file.get() or not self.merge_output_file.get():
            raise ValueError("Please select all required files")
        
        # Normalize file paths to handle Windows paths and special characters
        video_path = os.path.normpath(self.merge_video_file.get())
        srt_path = os.path.normpath(self.merge_srt_file.get())
        output_path = os.path.normpath(self.merge_output_file.get())
        
        # Convert Windows paths to forward slashes for FFmpeg
        if os.name == 'nt':  # Windows
            video_path = video_path.replace('\\', '/')
            srt_path = srt_path.replace('\\', '/')
            srt_path = srt_path.replace(':', '\\:')
            output_path = output_path.replace('\\', '/')
        
        # Build subtitle filter
        font_style = []
        
        # Font family and size
        font_style.append(f"FontName={self.font_name.get()}")
        font_style.append(f"FontSize={self.font_size.get()}")
        
        # Colors (convert hex to ASS BGR format)
        if self.font_color.get():
            font_color_hex = self.font_color.get().lstrip('#')
            if len(font_color_hex) == 6:  # Valid hex color
                # Convert RGB to BGR for ASS format
                r = font_color_hex[0:2]
                g = font_color_hex[2:4] 
                b = font_color_hex[4:6]
                bgr_color = f"{b}{g}{r}"  # Convert to BGR
                font_style.append(f"PrimaryColour=&H{bgr_color}")
        
        if self.font_outline_color.get():
            outline_color_hex = self.font_outline_color.get().lstrip('#')
            if len(outline_color_hex) == 6:  # Valid hex color
                # Convert RGB to BGR for ASS format
                r = outline_color_hex[0:2]
                g = outline_color_hex[2:4]
                b = outline_color_hex[4:6]
                bgr_color = f"{b}{g}{r}"  # Convert to BGR
                font_style.append(f"OutlineColour=&H{bgr_color}")
        
        font_style.append(f"Outline={self.font_outline_width.get()}")
        
        # Bold and Italic
        if self.font_bold.get():
            font_style.append("Bold=1")
        if self.font_italic.get():
            font_style.append("Italic=1")
        
        # Position
        if self.subtitle_position.get() == "top":
            font_style.append(f"MarginV={self.margin_vertical.get()}")
            font_style.append("Alignment=8")  # Top center
        elif self.subtitle_position.get() == "center":
            font_style.append("Alignment=5")  # Middle center
        else:  # bottom
            font_style.append(f"MarginV={self.margin_vertical.get()}")
            font_style.append("Alignment=2")  # Bottom center
        
        font_style.append(f"MarginL={self.margin_horizontal.get()}")
        font_style.append(f"MarginR={self.margin_horizontal.get()}")
        
        style_string = ",".join(font_style)
        
        # Build FFmpeg command with proper escaping
        # For Windows paths with colons, use single quotes to wrap the entire path
        subtitles_filter = f"subtitles='{srt_path}':force_style='{style_string}'"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", subtitles_filter,
            "-c:v", self.video_codec.get(),
            "-c:a", self.audio_codec.get()
        ]
        
        # Add CRF if using x264 or x265
        if self.video_codec.get() in ["libx264", "libx265"]:
            cmd.extend(["-crf", self.video_quality.get()])
        
        cmd.append(output_path)
        
        return cmd
    
    def start_merge(self):
        """Start video merging process"""
        try:
            # Validate inputs
            cmd = self.build_ffmpeg_command()
            
            # Check if FFmpeg is available
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                messagebox.showerror("Error", 
                    "FFmpeg not found. Please install FFmpeg and add it to your PATH.\n\n"
                    "Download from: https://ffmpeg.org/download.html")
                return
            
            self.is_merging = True
            self.merge_btn.config(state="disabled")
            self.stop_merge_btn.config(state="normal")
            self.merge_progress.start()
            self.status_var.set("Starting video merge...")
            self.merge_log_message("Starting video processing...")
            self.merge_log_message(f"Command: {' '.join(cmd)}")
            
            # Run FFmpeg in separate thread
            threading.Thread(target=self._merge_video_thread, args=(cmd,), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error starting merge: {str(e)}")
    
    def update_progress_label(self, progress_text):
        if hasattr(self, 'progress_label'):
            self.progress_label.config(text=progress_text)
    
    def _merge_video_thread(self, cmd):
        try:
            self.root.after(0, self.update_progress_label, "Starting FFmpeg process...")

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.merge_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                startupinfo=startupinfo
            )

            for line in iter(self.merge_process.stderr.readline, ''):
                if not self.is_merging:
                    break 

                line = line.strip()
                if not line:
                    continue

                if line.startswith("frame=") and "time=" in line and "speed=" in line:
                    self.root.after(0, self.update_progress_label, f"⏳ {line}")
                else:
                    self.root.after(0, self.merge_log_message, line)

            self.merge_process.wait()
            
            if self.is_merging: 
                if self.merge_process.returncode == 0:
                    self.root.after(0, self.update_progress_label, "✅ Process completed successfully!")
                    self.root.after(0, self.merge_log_message, "✅ Video merge completed successfully!")
                    self.status_var.set("Merge completed successfully!")
                    messagebox.showinfo("Success", f"Video saved to:\n{self.merge_output_file.get()}")
                else:
                    err_msg = f"❌ Process failed! (Return Code: {self.merge_process.returncode})"
                    self.root.after(0, self.update_progress_label, err_msg)
                    self.root.after(0, self.merge_log_message, f"❌ Merge failed with return code {self.merge_process.returncode}")
                    self.status_var.set("Merge failed. Check log for details.")
                    messagebox.showerror("Error", "Merge failed. Check the log for details.")

        except Exception as e:
            self.root.after(0, self.update_progress_label, "❌ An unexpected error occurred.")
            self.root.after(0, self.merge_log_message, f"❌ Error during merge: {str(e)}")
            self.status_var.set("Merge error occurred. Check log for details.")
            messagebox.showerror("Error", f"Merge error: {str(e)}")
        finally:
            def final_ui_reset():
                self.is_merging = False
                self.merge_btn.config(state="normal")
                self.stop_merge_btn.config(state="disabled")
                self.merge_progress.stop()
                self.merge_process = None
            
            self.root.after(0, final_ui_reset)
    
    def stop_merge(self):
        """Stop video merge process"""
        self.is_merging = False
        if self.merge_process and self.merge_process.poll() is None:
            self.merge_process.terminate()
            self.merge_log_message("Merge stopped by user")
            self.merge_btn.config(state="normal")
            self.stop_merge_btn.config(state="disabled")
            self.merge_progress.stop()
        
        
def main():
    root = tk.Tk()
    app = SRTTranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
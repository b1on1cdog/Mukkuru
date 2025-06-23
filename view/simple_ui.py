# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Uses tktinter to produce ui, used when webview is not available '''
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import threading
import queue
root = tk.Tk()
root.withdraw() #We do not want 2 windows

gui_task_queue = queue.Queue()
def run_gui_loop():
    ''' execute pending tasks '''
    def poll_queue():
        while not gui_task_queue.empty():
            try:
                task = gui_task_queue.get_nowait()
                task()
            except queue.Empty as e:
                print("GUI Task Error:", e)
        root.after(50, poll_queue)

    poll_queue()
    root.mainloop()

def create_progress_bar(pb_title):
    ''' produces a progress bar with a message  '''
    #if threading.current_thread() is not threading.main_thread():
    #    gui_task_queue.put(lambda: create_progress_bar(pb_title))
    #    return
    pw = tk.Toplevel(root)
    pw.title(pb_title)
    pw.geometry("400x120")

    label = tk.Label(pw, text="Starting....")
    label.pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(pw, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", expand=True, padx=20, pady=20)

    def update_progress(val, text = None):
        '''Update the progress bar'''
        #progress_var.set(val)
        #progress_bar.update_idletasks()
        pw.after(0, lambda: progress_var.set(val))
        if text:
            label.config(text=text)
        if val == 100:
            pw.after(0, pw.destroy())
        #gui_task_queue.put(lambda: progress_var.set(val))

    # Return the updater and the mainloop so caller can control
    return update_progress, root.mainloop

def open_filepicker(title, filetypes):
    ''' Literally what the function says '''
    if threading.current_thread() is not threading.main_thread():
        gui_task_queue.put(lambda: open_filepicker(title, filetypes))
        return
    root.withdraw()
    filepath = filedialog.askopenfilename(
    title=title,
    filetypes=[filetypes]
)
    if filepath == '':
        return None
    return filepath

def show_messagebox(title, message, kind, options = None):
    ''' Display a message box '''
    if threading.current_thread() is not threading.main_thread():
        gui_task_queue.put(lambda: show_messagebox(title, message, kind, options))
        return
    if kind == "Warning":
        messagebox.showwarning(title, message)
    elif kind == "Error":
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)
    if options:
        return

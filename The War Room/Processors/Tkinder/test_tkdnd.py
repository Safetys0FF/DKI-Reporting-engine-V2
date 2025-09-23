from tkinterdnd2 import TkinterDnD, DND_FILES
import tkinter as tk

def drop(event):
    dropped = event.data
    text_box.insert(tk.END, f"\nDropped: {dropped}")

root = TkinterDnD.Tk()
root.title("TKDnD Test")
root.geometry("400x300")

text_box = tk.Text(root, width=50, height=15)
text_box.pack(padx=10, pady=10)
text_box.drop_target_register(DND_FILES)
text_box.dnd_bind('<<Drop>>', drop)

root.mainloop()


import tkinter as tk
from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    
    # Iniciar con 4 bloques por defecto
    for _ in range(4):
        app.add_block()
        
    root.geometry(\"1000x750\")
    root.mainloop()

if __name__ == \"__main__\":
    main()

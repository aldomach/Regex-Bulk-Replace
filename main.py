import tkinter as tk
from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    
    # Iniciar con geometry antes de agregar bloques para evitar parpadeo
    root.geometry("1000x800")
    
    # Iniciar con 4 bloques por defecto
    for _ in range(4):
        app.add_block()
    root.mainloop()

if __name__ == "__main__":
    main()

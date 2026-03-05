import customtkinter
from app import SpotiFollowApp

if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("green")

    app = SpotiFollowApp()
    app.mainloop()

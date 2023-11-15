import os

from kivy.config import Config

x = os.environ.get('x', 50)
y = os.environ.get('y', 50)
Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', x)
Config.set('graphics', 'top', y)
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', True)

from kivy.core.window import Window

from .app import DurakFloatApp

DurakFloatApp().run()

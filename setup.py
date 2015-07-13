from distutils.core import setup
setup(name='tortp',
      version='0.5',
      py_modules=['tortp'],
      requires=['stem'],
      scripts=['tortp-gtk', 'tortp'],
      data_files=[('share/applications/', ['tortp.desktop']),
                  ('share/pixmaps/', ['anonymous.ico'])]
      )

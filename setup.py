from distutils.core import setup
setup(name='tortp',
        version='0.4',
        py_modules=['tortp'],
        requires=['stem'],
	scripts=['tortp-gtk'],
	data_files=[('share/applications/', ['tortp.desktop'])]
    )

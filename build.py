#!/usr/bin/env python3 -B
# -*- coding: utf-8 -*-

import os
import subprocess

path = os.path.dirname( os.path.realpath( __file__ ) )
os.chdir( os.path.join( path, 'src' ) )

spec = 'main.spec'
subprocess.run( [ 'pyinstaller', spec, '--distpath', os.path.join( path, 'dist' ), '--workpath', os.path.join( path, 'build' ) ], cwd = os.getcwd() )

try:
	os.remove( os.path.join( path, 'dist', '.'.join( spec.split( '.' )[ :-1 ] ) ) )
except:
	pass

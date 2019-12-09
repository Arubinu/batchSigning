# -*- mode: python -*-

import os
import sys
import platform

directory = '..'
rcpath = './resources'
binpath = os.path.join( rcpath, 'bin' )

ext = ''
icon = ''
syst = ''
pathex = []
bundle = True	# Create .app bundle
app_name = 'batchSigning'

p = platform.system()
name = sys.argv[ 1 ][ :-5 ]

if p.find( 'Windows' ) >= 0:
	ext = '.exe'
	icon = 'ico'
	syst = 'windows'
	pathex.append( 'C:\\Users\\' + os.getenv( 'USERNAME' ) + '\\AppData\\Local\\Programs\\Python\\Python37\\Lib\\site-packages\\PyQt5' )
	pathex.append( 'C:\\Users\\' + os.getenv( 'USERNAME' ) + '\\AppData\\Local\\Programs\\Python\\Python37\\Lib\\site-packages\\PyQt5\\Qt\\bin' )
	pathex.append( 'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64' )
elif p.find( 'Darwin' ) >= 0:
	ext = '.app'
	icon = 'icns'
	syst = 'darwin'
	pathex.append( '/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/PyQt5' )
elif p.find( 'Linux' ) >= 0:
	icon = 'png'
	syst = 'linux'
	pathex.append( '/home/' + os.getenv( 'USER' ) + '/.local/lib/python3.7/site-packages/PyQt5' )
else:
	raise ( Exception( 'Unsupported System' ) )
	sys.exit( 1 )

block_cipher = None
binpath = os.path.join( binpath, syst )

a = Analysis(
	[ name + '.py' ],
	pathex					= pathex,
	binaries				= [],
	datas					= [
		( os.path.join( 'style.qss' ),							'.' ),
		( os.path.join( rcpath, 'Status_Unavailable_2x.png' ),	rcpath ),
		( os.path.join( rcpath, 'Status_Unavailable_2xa.png' ),	rcpath ),
		( os.path.join( rcpath, 'Status_Partially_2x.png' ),	rcpath ),
		( os.path.join( rcpath, 'Status_Partially_2xa.png' ),	rcpath ),
		( os.path.join( rcpath, 'Status_None_2x.png' ),			rcpath ),
		( os.path.join( rcpath, 'checkbox_checked.png' ),		rcpath ),
		( os.path.join( rcpath, 'checkbox_unchecked.png' ),		rcpath ),
		( os.path.join( rcpath, 'icon.png' ),					rcpath ),
		( os.path.join( rcpath, 'logo.png' ),					rcpath ),
		( os.path.join( rcpath, 'signature.png' ),				rcpath ),
		( os.path.join( rcpath, 'gallery.png' ),				rcpath ),
		( os.path.join( rcpath, 'target.png' ),					rcpath ),
		( os.path.join( rcpath, 'apply.png' ),					rcpath ),
		( os.path.join( rcpath, 'gravity_center.png' ),			rcpath ),
		( os.path.join( rcpath, 'gravity_northwest.png' ),		rcpath ),
		( os.path.join( rcpath, 'gravity_north.png' ),			rcpath ),
		( os.path.join( rcpath, 'gravity_northeast.png' ),		rcpath ),
		( os.path.join( rcpath, 'gravity_east.png' ),			rcpath ),
		( os.path.join( rcpath, 'gravity_southeast.png' ),		rcpath ),
		( os.path.join( rcpath, 'gravity_south.png' ),			rcpath ),
		( os.path.join( rcpath, 'gravity_southwest.png' ),		rcpath ),
		( os.path.join( rcpath, 'gravity_west.png' ),			rcpath )

	],
	hiddenimports			= [ 'engineio.async_eventlet' ],
	hookspath				= [],
	runtime_hooks			= [],
	excludes				= [ 'jinja2.asyncsupport', 'jinja2.asyncfilters' ],
	win_no_prefer_redirects	= False,
	win_private_assemblies	= False,
	cipher					= block_cipher
)

a.datas += Tree( binpath, prefix = binpath, excludes = [ 'Thumbs.db', '.DS_Store' ], typecode = 'DATA' )

pyz = PYZ(
	a.pure,
	a.zipped_data,
	cipher					= block_cipher
)

if syst != 'darwin':
	name = app_name

exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	name					= name,
	debug					= False,
	strip					= False,
	upx						= False,
	console					= False,
	icon					= os.path.join( rcpath, 'icon.' + icon )
)

# MacOS Bundle (.app) don't open console
if bundle:
	app = BUNDLE(
		exe,
		name				= app_name + ext,
		icon				= os.path.join( rcpath, 'icon.' + icon ),
		bundle_identifier	= None,
		info_plist			= {
			'LSBackgroundOnly':			'True',
			'NSHighResolutionCapable':	'True'
		}
	)

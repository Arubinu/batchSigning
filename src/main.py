#!/usr/bin/env python3
# -*- coding: utf-8 -*-

DIVIDE = [ 'png', 'tiff' ]
EXTENSIONS = [ 'png', 'jpeg', 'tiff', 'webp' ]

# built-in
import os
import sys
import math
import threading
import subprocess

# since PIP
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog

# more
try:
	import win32api
	def longpath( path ):
		return ( win32api.GetLongPathName( path ) )
except:
	def longpath( path ):
		return ( path )

# platform
os_name = sys.platform
os_name = ( 'windows' if os_name.startswith( 'win' ) else os_name )
os_name = ( 'linux' if os_name.startswith( 'linux' ) else os_name )

# fix subprocess poped window
startupinfo = None
if sys.platform == 'win32':
	startupinfo = subprocess.STARTUPINFO()
	startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def exec_path( relative_path = '' ):
	if getattr( sys, 'frozen', False ) and getattr( sys, '_MEIPASS', False ):
		tmp = os.path.dirname( sys.executable )
	else:
		tmp = os.path.dirname( os.path.realpath( __file__ ) )

	return ( os.path.join( tmp, relative_path ) )

def resource_path( relative_path = '' ):
	if getattr( sys, '_MEIPASS', False ):
		tmp = sys._MEIPASS
	else:
		tmp = os.path.dirname( os.path.realpath( __file__ ) )

	return ( os.path.join( tmp, relative_path ) )

def resource( *args, **kwargs ):
	global os_name

	path = os.path.join( *args )
	if 'root' not in kwargs or not kwargs[ 'root' ]:
		path = os.path.join( 'resources', path )
	if 'bin' in kwargs and kwargs[ 'bin' ] and os_name == 'windows':
		path += '.exe'

	return ( resource_path( path ) )

def getfilesize( file ):
	filesize = str( os.path.getsize( file ) )

	lencut = 0
	lensize = len( filesize )
	if ( lensize > 12 ):
		lencut = 12
	elif ( lensize > 9 ):
		lencut = 9
	elif ( lensize > 6 ):
		lencut = 6
	elif ( lensize > 3 ):
		lencut = 3

	lensuffix = { 0: '', 3: 'K', 6: 'M', 9: 'G', 12: 'T' }
	if lencut:
		filesize = filesize[ 0:-( lencut ) ] + '.' + filesize[ -( lencut ):-( lencut - 1 ) ]
	filesize += ' ' + lensuffix[ lencut ] + 'o'

	return ( filesize )

def process( files, watermark, target, quality = 100, gravity = ( 0, 0 ), position = ( 0, 0 ), size = ( 0, 0 ), stopevent = None, sigprogress = None, sigfinished = None ):
	global DIVIDE, os_name, startupinfo

	composite = resource( 'bin', os_name, 'composite', bin = True )

	g = ''
	gravities = [ [ 'North', 'South' ], [ 'West', 'East' ] ]
	if gravity[ 0 ] or gravity[ 1 ]:
		if gravity[ 0 ]:
			g += ( gravities[ 0 ][ 1 if gravity[ 0 ] > 0 else 0 ] )
		if gravity[ 1 ]:
			g += ( gravities[ 1 ][ 1 if gravity[ 1 ] > 0 else 0 ] )
	else:
		g = 'Center'

	geometry = '%s%d' % ( ( '+' if position[ 0 ] >= 0 else '' ), position[ 0 ] )
	geometry += '%s%d' % ( ( '+' if position[ 1 ] >= 0 else '' ), position[ 1 ] )
	if size[ 0 ] and size[ 1 ]:
		geometry = '%dx%d%s' % ( size[ 0 ], size[ 1 ], geometry )

	resume = [ [], [] ]
	total = len( files )
	for index, file in enumerate( files ):
		if stopevent and stopevent.is_set():
			return
		if sigprogress:
			sigprogress( index, total, file, None, None, None )

		q = quality
		if file.split( '.' )[ -1 ].lower() in DIVIDE:
			q = round( q / 10 )
		q = str( 100 if q <= 0 or q > 100 else q )

		t = os.path.join( target, os.path.basename( file ) )

		cmd = [ composite, '-gravity', g, '-geometry', geometry, '-quality', q, watermark, file, t ]
		error = False
		output = False
		try:
			output = subprocess.check_output( cmd, stderr = subprocess.STDOUT, env = os.environ, startupinfo = startupinfo )
			resume[ 0 ].append( file )
		except subprocess.CalledProcessError as e:
			error = True
			output = e.output
			resume[ 1 ].append( file )

		output = str( output, 'utf-8' )
		if sigprogress:
			sigprogress( index, total, file, cmd, error, output )

	if sigfinished:
		sigfinished( *resume )

class Image( QtWidgets.QLabel ): # QtWidgets.QPushButton
	def __init__( self, name = None, width = 0, height = 0, callback = None, parent = None ):
		super( Image, self ).__init__( parent )

		pixmap = None
		if name:
			self.setObjectName( name )
			pixmap = QtGui.QPixmap( resource( '%s.png' % name ) )

		mode = 'height'
		if width and height:
			self.setFixedSize( width, height )
		elif width:
			mode = 'width'
			self.setFixedWidth( width )
		elif height:
			self.setFixedHeight( height )
		else:
			mode = None

		if pixmap and not pixmap.isNull():
			if mode:
				size = ( width if mode == 'width' else height )
				pixmap = getattr( pixmap, ( 'scaledTo%s' % mode.capitalize() ) )( size, QtCore.Qt.SmoothTransformation )

			self.setPixmap( pixmap )

		self.callback = callback

	def mousePressEvent( self, event ):
		if self.callback:
			self.callback( self, event )

class Gravity( QtWidgets.QLabel ):
	def __init__( self, prefix, extension, parent = None ):
		super( Gravity, self ).__init__( parent )

		self.prefix = prefix
		self.extension = extension

		self.gravity = 'center'
		self.relative = ( 0, 0 )
		self.reload()

	def reload( self ):
		pixmap = QtGui.QPixmap( resource( '%s%s.%s' % ( self.prefix, self.gravity, self.extension ) ) )
		self.setPixmap( pixmap.scaledToHeight( 115, QtCore.Qt.SmoothTransformation ) )

	def mousePressEvent( self, event ):
		x = math.floor( event.x() / ( self.width() / 3 ) )
		y = math.floor( event.y() / ( self.height() / 3 ) )
		if x == 1 and y == 1:
			self.gravity = 'center'
		elif x == 1:
			self.gravity = ( 'north' if y < 1 else 'south' )
		elif y == 1:
			self.gravity = ( 'west' if x < 1 else 'east' )
		else:
			self.gravity = ( 'north' if y < 1 else 'south' )
			self.gravity += ( 'west' if x < 1 else 'east' )

		self.relative = ( y - 1, x - 1 )
		self.reload()

class Window( QtWidgets.QMainWindow ):
	sigfinished = QtCore.pyqtSignal( list, list )
	sigprogress = QtCore.pyqtSignal( int, int, str, object, object, object )

	def __init__( self, parent = None ):
		super( Window, self ).__init__( parent )

		self.drag = 0
		self.step = 0
		self.paths = [ '', '', '' ]
		self.steps = [ [], [], [], [] ]
		self.started = False
		self.waiting = False
		self.settings = {}
		self.sigfinished.connect( self.finished )
		self.sigprogress.connect( self.progress )
		self.stopthread = threading.Event()

	def setup( self ):
		global EXTENSIONS

		icon = QtGui.QIcon()
		icon.addPixmap( QtGui.QPixmap( resource( 'icon.png' ) ), QtGui.QIcon.Normal, QtGui.QIcon.Off )
		self.setWindowIcon( icon )
		self.setWindowTitle( 'batchSigning' )
		self.setWindowFlags( QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowMaximizeButtonHint )
		self.setAttribute( QtCore.Qt.WA_TranslucentBackground, True )
		self.setFixedSize( 800, 480 )
		self.setObjectName( 'window' )

		self.centralWidget = QtWidgets.QWidget( self )
		self.centralWidget.setObjectName( 'centralWidget' )
		self.setCentralWidget( self.centralWidget )
		layout = QtWidgets.QVBoxLayout( self.centralWidget )
		layout.setAlignment( QtCore.Qt.AlignBottom )
		layout.setContentsMargins( 0, 0, 0, 0 )

		self.defaultPage = QtWidgets.QWidget()
		self.defaultPage.setObjectName( 'defaultPage' )
		layout = QtWidgets.QVBoxLayout( self.defaultPage )
		layout.setAlignment( QtCore.Qt.AlignBottom )
		layout.setContentsMargins( 0, 0, 0, 0 )
		self.central( self.defaultPage )

		### Logo
		wlogo = QtWidgets.QWidget( self )
		wlogo.setObjectName( 'wlogo' )
		wlogo.setGeometry( QtCore.QRect( 0, 0, 800, 50 ) )

		llayout = QtWidgets.QVBoxLayout( wlogo )
		llayout.setAlignment( QtCore.Qt.AlignCenter )

		logo = QtWidgets.QLabel()
		logo.setFixedSize( 140, 25 )
		logo.setAlignment( QtCore.Qt.AlignCenter )
		logo.setObjectName( 'logo' )
		llayout.addWidget( logo )

		### Controls
		wcontrols = QtWidgets.QWidget( self )
		wcontrols.setObjectName( 'wcontrols' )
		wcontrols.setGeometry( QtCore.QRect( 8, 0, 76, 38 ) ) # 60x18
		wlogo.stackUnder( wcontrols )

		clayout = QtWidgets.QHBoxLayout( wcontrols )
		clayout.setAlignment( QtCore.Qt.AlignLeft )
		clayout.setContentsMargins( 0, 0, 0, 0 )
		clayout.setSpacing( 0 )

		cross = Image( 'cross', 20, 20, lambda item, event: self.close() )
		clayout.addWidget( cross )

		minimize = Image( 'minimize', 20, 20, lambda item, event: self.showMinimized() )
		clayout.addWidget( minimize )

		maximize = Image( 'maximize', 20, 20 )
		clayout.addWidget( maximize )

		### Icons
		icons = QtWidgets.QWidget()
		icons.setObjectName( 'icons' )
		ilayout = QtWidgets.QHBoxLayout( icons )
		ilayout.setAlignment( QtCore.Qt.AlignCenter )
		ilayout.setSpacing( 38 )
		layout.addWidget( icons )

		## Icon
		isignature = Image( 'signature', 42, 42 )
		isignature.setProperty( 'cssClass', 'icon' )
		isignature.setObjectName( 'isignature' )
		ilayout.addWidget( isignature )
		self.steps[ 0 ].append( isignature )

		## Separator
		separator = QtWidgets.QWidget()
		separator.setProperty( 'cssClass', 'separator' )
		ilayout.addWidget( separator )
		self.steps[ 1 ].append( separator )

		## Icon
		igallery = Image( 'gallery', 42, 42 )
		igallery.setProperty( 'cssClass', 'icon' )
		ilayout.addWidget( igallery )
		self.steps[ 1 ].append( igallery )

		## Separator
		separator = QtWidgets.QWidget()
		separator.setProperty( 'cssClass', 'separator' )
		ilayout.addWidget( separator )
		self.steps[ 2 ].append( separator )

		## Icon
		itarget = Image( 'target', 42, 42 )
		itarget.setProperty( 'cssClass', 'icon' )
		ilayout.addWidget( itarget )
		self.steps[ 2 ].append( itarget )

		## Separator
		separator = QtWidgets.QWidget()
		separator.setProperty( 'cssClass', 'separator' )
		ilayout.addWidget( separator )
		self.steps[ 3 ].append( separator )

		## Icon
		iapply = Image( 'apply', 42, 42 )
		iapply.setProperty( 'cssClass', 'icon' )
		ilayout.addWidget( iapply )
		self.steps[ 3 ].append( iapply )

		### Buttons
		buttons = QtWidgets.QWidget()
		buttons.setObjectName( 'buttons' )
		blayout = QtWidgets.QHBoxLayout( buttons )
		blayout.setAlignment( QtCore.Qt.AlignCenter )
		blayout.setSpacing( 42 )
		layout.addWidget( buttons )

		## Button
		vbwidget = QtWidgets.QWidget()
		vbwidget.setProperty( 'cssClass', 'vbwidget' )
		vlayout = QtWidgets.QVBoxLayout( vbwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vbwidget )
		self.steps[ 0 ].append( vbwidget )

		bsignature = QtWidgets.QPushButton( 'Select Signature' )
		bsignature.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		bsignature.setProperty( 'cssClass', 'button' )
		bsignature.setObjectName( 'bsignature' )
		bsignature.clicked.connect( lambda: self.define( 0 ) )
		vlayout.addWidget( bsignature )
		self.steps[ 0 ].append( bsignature )

		nsignature = QtWidgets.QLabel( ', '.join( EXTENSIONS ) )
		nsignature.setAlignment( QtCore.Qt.AlignHCenter )
		nsignature.setProperty( 'cssClass', 'note' )
		nsignature.setObjectName( 'nsignature' )
		vlayout.addWidget( nsignature )
		self.steps[ 0 ].append( nsignature )

		## Change
		vcwidget = QtWidgets.QWidget()
		vcwidget.setProperty( 'cssClass', 'vcwidget' )
		vlayout = QtWidgets.QVBoxLayout( vcwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vcwidget )
		self.steps[ 0 ].append( vcwidget )

		psignature = QtWidgets.QLabel()
		psignature.setAlignment( QtCore.Qt.AlignHCenter )
		psignature.setProperty( 'cssClass', 'path' )
		psignature.setObjectName( 'psignature' )
		vlayout.addWidget( psignature )
		self.steps[ 0 ].append( psignature )

		csignature = QtWidgets.QPushButton( 'Change' )
		csignature.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		csignature.setProperty( 'cssClass', 'change' )
		csignature.setObjectName( 'csignature' )
		csignature.clicked.connect( lambda: self.define( 0 ) )
		vlayout.addWidget( csignature )

		dsignature = QtWidgets.QLabel()
		dsignature.setAlignment( QtCore.Qt.AlignHCenter )
		dsignature.setProperty( 'cssClass', 'details' )
		dsignature.setObjectName( 'dsignature' )
		vlayout.addWidget( dsignature )
		self.steps[ 0 ].append( dsignature )

		## Button
		vbwidget = QtWidgets.QWidget()
		vbwidget.setProperty( 'cssClass', 'vbwidget' )
		vlayout = QtWidgets.QVBoxLayout( vbwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vbwidget )
		self.steps[ 1 ].append( vbwidget )

		bgallery = QtWidgets.QPushButton( 'Select Gallery' )
		bgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		bgallery.setProperty( 'cssClass', 'button' )
		bgallery.setObjectName( 'bgallery' )
		bgallery.clicked.connect( lambda: self.define( 1 ) )
		vlayout.addWidget( bgallery )
		self.steps[ 1 ].append( bgallery )

		ngallery = QtWidgets.QLabel( 'contains: %s' % ', '.join( EXTENSIONS ) )
		ngallery.setAlignment( QtCore.Qt.AlignHCenter )
		ngallery.setProperty( 'cssClass', 'note' )
		ngallery.setObjectName( 'ngallery' )
		vlayout.addWidget( ngallery )
		self.steps[ 1 ].append( ngallery )

		## Change
		vcwidget = QtWidgets.QWidget()
		vcwidget.setProperty( 'cssClass', 'vcwidget' )
		vlayout = QtWidgets.QVBoxLayout( vcwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vcwidget )
		self.steps[ 1 ].append( vcwidget )

		pgallery = QtWidgets.QLabel()
		pgallery.setAlignment( QtCore.Qt.AlignHCenter )
		pgallery.setProperty( 'cssClass', 'path' )
		pgallery.setObjectName( 'pgallery' )
		vlayout.addWidget( pgallery )
		self.steps[ 1 ].append( pgallery )

		cgallery = QtWidgets.QPushButton( 'Change' )
		cgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		cgallery.setProperty( 'cssClass', 'change' )
		cgallery.setObjectName( 'cgallery' )
		cgallery.clicked.connect( lambda: self.define( 1 ) )
		vlayout.addWidget( cgallery )

		dgallery = QtWidgets.QLabel()
		dgallery.setAlignment( QtCore.Qt.AlignHCenter )
		dgallery.setProperty( 'cssClass', 'details' )
		dgallery.setObjectName( 'dgallery' )
		vlayout.addWidget( dgallery )
		self.steps[ 1 ].append( dgallery )

		## Button
		vbwidget = QtWidgets.QWidget()
		vbwidget.setProperty( 'cssClass', 'vbwidget' )
		vlayout = QtWidgets.QVBoxLayout( vbwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vbwidget )
		self.steps[ 2 ].append( vbwidget )

		btarget = QtWidgets.QPushButton( 'Select Target' )
		btarget.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		btarget.setProperty( 'cssClass', 'button' )
		btarget.setObjectName( 'btarget' )
		btarget.clicked.connect( lambda: self.define( 2 ) )
		vlayout.addWidget( btarget )
		self.steps[ 2 ].append( btarget )

		## Change
		vcwidget = QtWidgets.QWidget()
		vcwidget.setProperty( 'cssClass', 'vcwidget' )
		vlayout = QtWidgets.QVBoxLayout( vcwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vcwidget )
		self.steps[ 2 ].append( vcwidget )

		pgallery = QtWidgets.QLabel()
		pgallery.setAlignment( QtCore.Qt.AlignHCenter )
		pgallery.setProperty( 'cssClass', 'path' )
		pgallery.setObjectName( 'pgallery' )
		vlayout.addWidget( pgallery )
		self.steps[ 2 ].append( pgallery )

		cgallery = QtWidgets.QPushButton( 'Change' )
		cgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		cgallery.setProperty( 'cssClass', 'change' )
		cgallery.setObjectName( 'cgallery' )
		cgallery.clicked.connect( lambda: self.define( 2 ) )
		vlayout.addWidget( cgallery )

		## Button
		vbwidget = QtWidgets.QWidget()
		vbwidget.setProperty( 'cssClass', 'vbwidget' )
		vlayout = QtWidgets.QVBoxLayout( vbwidget )
		vlayout.setAlignment( QtCore.Qt.AlignTop )
		vlayout.setContentsMargins( 0, 0, 0, 0 )
		vlayout.setSpacing( 18 )
		blayout.addWidget( vbwidget )

		bapply = QtWidgets.QPushButton( 'Apply' )
		bapply.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		bapply.setProperty( 'cssClass', 'button' )
		bapply.setObjectName( 'bapply' )
		bapply.clicked.connect( lambda: self.update( 4 ) )
		vlayout.addWidget( bapply )
		self.steps[ 3 ].append( bapply )

		### Settings
		labelsize = 90
		spinboxsize = 115
		checkboxsize = 19

		settings = QtWidgets.QWidget()
		settings.setObjectName( 'settings' )
		slayout = QtWidgets.QGridLayout( settings )
		slayout.setAlignment( QtCore.Qt.AlignTop )
		slayout.setContentsMargins( 15, 15, 15, 10 )
		slayout.setSpacing( 20 )
		layout.addWidget( settings )

		slayout.setColumnMinimumWidth( 2, checkboxsize + 15 )
		slayout.setColumnMinimumWidth( 3, labelsize )
		slayout.setColumnMinimumWidth( 4, spinboxsize )
		slayout.setColumnMinimumWidth( 5, labelsize )
		slayout.setColumnMinimumWidth( 6, spinboxsize )

		## Gravity
		lgravity = QtWidgets.QLabel( 'Gravity:' )
		lgravity.setAlignment( QtCore.Qt.AlignLeft )
		lgravity.setObjectName( 'lgravity' )
		slayout.addWidget( lgravity, 0, 0 )

		gravity = Gravity( 'gravity_', 'png' )
		gravity.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		gravity.setAlignment( QtCore.Qt.AlignCenter )
		gravity.setObjectName( 'gravity' )
		slayout.addWidget( gravity, 0, 1, 3, 1 )
		self.settings[ 'gravity' ] = gravity

		## Quality
		lquality = QtWidgets.QLabel( 'Quality:' )
		lquality.setAlignment( QtCore.Qt.AlignLeft )
		lquality.setObjectName( 'lquality' )
		slayout.addWidget( lquality, 0, 3 )

		squality = QtWidgets.QSpinBox()
		squality.setToolTip( '0 to 100% (for lossless rendering)' )
		squality.setProperty( 'cssClass', 'spinbox' )
		squality.setRange( 1, 100 )
		squality.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		slayout.addWidget( squality, 0, 6 )
		self.settings[ 'quality' ] = squality

		## Position
		lpositionx = QtWidgets.QLabel( 'Position X:' )
		lpositionx.setAlignment( QtCore.Qt.AlignLeft )
		lpositionx.setObjectName( 'lpositionx' )
		slayout.addWidget( lpositionx, 1, 3 )

		spositionx = QtWidgets.QSpinBox()
		spositionx.setToolTip( 'Expresses itself in pixel' )
		spositionx.setProperty( 'cssClass', 'spinbox' )
		spositionx.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		spositionx.setRange( -10000, 10000 )
		slayout.addWidget( spositionx, 1, 4 )
		self.settings[ 'x' ] = spositionx

		lpositiony = QtWidgets.QLabel( 'Position Y:' )
		lpositiony.setAlignment( QtCore.Qt.AlignLeft )
		lpositiony.setObjectName( 'lpositiony' )
		slayout.addWidget( lpositiony, 1, 5 )

		spositiony = QtWidgets.QSpinBox()
		spositiony.setToolTip( 'Expresses itself in pixel' )
		spositiony.setProperty( 'cssClass', 'spinbox' )
		spositiony.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		spositiony.setRange( -10000, 10000 )
		slayout.addWidget( spositiony, 1, 6 )
		self.settings[ 'y' ] = spositiony

		## Size
		more = QtWidgets.QWidget()
		more.setContentsMargins( 0, 0, 0, 0 )
		more.setObjectName( 'more' )
		mlayout = QtWidgets.QGridLayout( more )
		mlayout.setAlignment( QtCore.Qt.AlignRight )
		mlayout.setContentsMargins( 0, 0, 0, 0 )
		mlayout.setSpacing( 20 )
		slayout.addWidget( more, 2, 2, 1, 5 )

		mlayout.setColumnMinimumWidth( 0, checkboxsize )
		mlayout.setColumnMinimumWidth( 1, labelsize )
		mlayout.setColumnMinimumWidth( 2, spinboxsize )
		mlayout.setColumnMinimumWidth( 3, labelsize )
		mlayout.setColumnMinimumWidth( 4, spinboxsize )

		# CheckBox
		csize = QtWidgets.QCheckBox()
		csize.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		csize.stateChanged.connect( self.change )
		mlayout.addWidget( csize, 0, 0 )
		self.settings[ 'resize' ] = csize

		# Width
		lwidth = QtWidgets.QLabel( 'Width:' )
		lwidth.setAlignment( QtCore.Qt.AlignLeft )
		lwidth.setObjectName( 'lwidth' )
		mlayout.addWidget( lwidth, 0, 1 )

		swidth = QtWidgets.QSpinBox()
		swidth.setToolTip( 'Expresses itself in pixel' )
		swidth.setProperty( 'cssClass', 'spinbox' )
		swidth.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		swidth.setRange( 1, 10000 )
		mlayout.addWidget( swidth, 0, 2 )
		self.settings[ 'width' ] = swidth

		# Height
		lheight = QtWidgets.QLabel( 'Height:' )
		lheight.setAlignment( QtCore.Qt.AlignLeft )
		lheight.setObjectName( 'lheight' )
		mlayout.addWidget( lheight, 0, 3 )

		sheight = QtWidgets.QSpinBox()
		sheight.setToolTip( 'Expresses itself in pixel' )
		sheight.setProperty( 'cssClass', 'spinbox' )
		sheight.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		sheight.setRange( 1, 10000 )
		mlayout.addWidget( sheight, 0, 4 )
		self.settings[ 'height' ] = sheight

		### Process
		self.processPage = QtWidgets.QWidget( self )
		self.processPage.setObjectName( 'processPage' )

		layout = QtWidgets.QGridLayout( self.processPage )
		layout.setAlignment( QtCore.Qt.AlignBottom )
		layout.setContentsMargins( 30, 0, 30, 30 )
		layout.setSpacing( 20 )
		layout.setVerticalSpacing( 38 )

		## Progressbar
		progressbar = QtWidgets.QProgressBar()
		progressbar.setObjectName( 'progressbar' )
		layout.addWidget( progressbar, 0, 0, 1, 2 )

		## Preview
		preview = QtWidgets.QLabel()
		preview.setAlignment( QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter )
		preview.setObjectName( 'preview' )
		preview.setFixedHeight( 320 )
		layout.addWidget( preview, 1, 0 )

		## Infos
		infos = QtWidgets.QWidget()
		infos.setContentsMargins( 0, 0, 0, 0 )
		infos.setObjectName( 'infos' )
		ilayout = QtWidgets.QVBoxLayout( infos )
		ilayout.setAlignment( QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight )
		ilayout.setContentsMargins( 0, 0, 0, 0 )
		ilayout.setSpacing( 20 )
		layout.addWidget( infos, 1, 1 )

		infos.setFixedWidth( 200 )

		# Filename
		filename = QtWidgets.QLabel()
		filename.setAlignment( QtCore.Qt.AlignRight )
		filename.setObjectName( 'filename' )
		ilayout.addWidget( filename )

		# Filesize
		filesize = QtWidgets.QLabel()
		filesize.setAlignment( QtCore.Qt.AlignRight )
		filesize.setObjectName( 'filesize' )
		ilayout.addWidget( filesize )

		# States
		states = QtWidgets.QLabel()
		states.setAlignment( QtCore.Qt.AlignCenter )
		states.setTextFormat( QtCore.Qt.RichText )
		states.setObjectName( 'states' )
		ilayout.addWidget( states )

		# Cancel
		self.cancel = QtWidgets.QPushButton( 'Cancel' )
		self.cancel.setSizePolicy( QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed )
		self.cancel.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		self.cancel.setProperty( 'cssClass', 'button' )
		self.cancel.setObjectName( 'cancel' )
		self.cancel.clicked.connect( lambda: self.stopprocess( True ) )
		ilayout.addWidget( self.cancel )

		# Close
		self.close = QtWidgets.QPushButton( 'Close' )
		self.close.setSizePolicy( QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed )
		self.close.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		self.close.setProperty( 'cssClass', 'button' )
		self.close.setObjectName( 'close' )
		self.close.hide()
		self.close.clicked.connect( lambda: self.stopprocess( True ) )
		ilayout.addWidget( self.close )

		self.infos = {
			'progressbar':	progressbar,
			'preview':	preview,
			'filename':	filename,
			'filesize':	filesize,
			'states':	states
		}

		### Header on top
		self.defaultPage.stackUnder( wlogo )
		self.processPage.stackUnder( wlogo )

		### Values
		squality.setValue( 100 )
		csize.setChecked( False )
		swidth.setValue( 100 )
		sheight.setValue( 100 )

		self.change()
		self.update()

	def central( self, widget ):
		layout = self.centralWidget.layout()

		if layout.count():
			layout.takeAt( 0 ).widget().hide()

		layout.addWidget( widget )
		widget.show()

	def change( self, *args ):
		self.settings[ 'width' ].setEnabled( bool( self.settings[ 'resize' ].checkState() ) )
		self.settings[ 'height' ].setEnabled( bool( self.settings[ 'resize' ].checkState() ) )

	def file( self, title, path = None, types = None ):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog

		path = ( path or os.getenv( 'HOME', '' ) )
		file, _ = QFileDialog.getOpenFileName( None, title, path, types, options = options )
		return ( file )

	def folder( self, title, path = None ):
		options = QFileDialog.Options()
		options |= QFileDialog.ShowDirsOnly
		options |= QFileDialog.DontUseNativeDialog

		path = ( path or os.getenv( 'HOME', '' ) )
		folder = QFileDialog.getExistingDirectory( None, title, path, options = options )
		return ( folder )

	def progress( self, index, total, file = '', cmd = None, error = None, output = None ):
		if total:
			self.infos[ 'progressbar' ].setRange( 0, total )
			self.infos[ 'progressbar' ].setValue( index )

		if error is None:
			length = max( 3, len( str( total ) ) )
			template = '<pre>[ <span style="font-size: %dpx;"><span style="color: rgb( 231, 76, 60 );">%s</span> %s / %s</span> ]</pre>'

			fontsize = 10
			fontsizes = [ 17, 17, 17, 14, 12 ]
			if length <= len( fontsizes ):
				fontsize = fontsizes[ length - 1 ]

			text = template % (
				fontsize,
				str( self.errors ).ljust( length, ' ' ),
				str( index + 1 ).rjust( length, '0' ),
				str( total ).rjust( length, '0' )
			)

			self.infos[ 'states' ].setText( text )

			if file:
				self.infos[ 'filename' ].setText( os.path.basename( file ) )
				self.infos[ 'filesize' ].setText( getfilesize( file ) )

				pixmap = QtGui.QPixmap( file )
				if pixmap and not pixmap.isNull():
					width = self.infos[ 'preview' ].width()
					height = self.infos[ 'preview' ].height()

					pixmap = pixmap.scaled( width, height, ( QtCore.Qt.KeepAspectRatio | QtCore.Qt.SmoothTransformation ) )
					self.infos[ 'preview' ].setPixmap( pixmap )
		else:
			self.infos[ 'progressbar' ].setValue( index + 1 )
			# create resume file
			#print( 'cmd:', cmd )
			if error:
				self.errors += 1
				#print( 'output:', output )
				pass
			pass

	def finished( self, success, errors ):
		self.stopprocess()

	def define( self, step ):
		if step >= 0 and step < len( self.steps ):
			title = ''
			path = None
			details = None
			for item in self.steps[ step ]:
				property = item.property( 'cssClass' )
				if property == 'button':
					title = item.text()
				elif property == 'path':
					path = item
				elif property == 'details':
					details = item

			if title:
				selected = getattr( self, ( 'folder' if step else 'file' ) )( title )
				if selected:
					if step == 2 and selected == self.paths[ step - 1 ]:
						return

					self.paths[ step ] = selected
					if path:
						path.setToolTip( longpath( selected ) )
						path.setText( os.path.basename( selected ) )

					self.update( step + 1 )

	def update( self, step = None ):
		global EXTENSIONS

		if step is not None and step > self.step:
			self.step = step

		if self.step > 3:
			exts = []
			for ext in EXTENSIONS:
				exts.append( ext )
				if ext == 'jpeg':
					exts.append( 'jpg' )

			files = []
			gallery = self.paths[ 1 ]
			for file in os.listdir( gallery ):
				file = os.path.join( gallery, file )
				ext = file.split( '.' )[ -1 ].lower()
				if os.path.isfile( file ) and ext in exts:
					files.append( file )

			quality = self.settings[ 'quality' ].value()
			gravity = self.settings[ 'gravity' ].relative
			position = ( self.settings[ 'x' ].value(), self.settings[ 'y' ].value() )
			size = ( 0, 0 )
			if bool( self.settings[ 'resize' ].checkState() ):
				size = ( self.settings[ 'width' ].value(), self.settings[ 'height' ].value() )

			args = ( files, self.paths[ 0 ], self.paths[ 2 ] )
			kwargs = {
				'quality':		quality,
				'gravity':		gravity,
				'position':		position,
				'size':			size,
				'stopevent':	self.stopthread,
				'sigprogress':	self.sigprogress.emit,
				'sigfinished':	self.sigfinished.emit
			}

			self.errors = 0
			self.startprocess()

			self.thread = threading.Thread( target = process, args = args, kwargs = kwargs, daemon = True )
			self.thread.start()
			return

		for index, items in enumerate( self.steps ):
			for item in self.steps[ index ]:
				item.setEnabled( self.step >= index )

				property = item.property( 'cssClass' )
				bshow = ( self.step <= index )
				cshow = ( not bshow )

				if property == 'vbwidget':
					getattr( item, ( 'show' if bshow else 'hide' ) )()
				elif property == 'vcwidget':
					getattr( item, ( 'show' if cshow else 'hide' ) )()

				if property in [ 'vbwidget', 'vcwidget' ]:
					item.setFixedSize( 155, 120 )
				elif property == 'separator':
					item.setFixedSize( 80, 2 ) # 90, 2

	def startprocess( self ):
		if not self.started:
			self.started = True
			self.progress( 0, 0 )
			self.central( self.processPage )

	def stopprocess( self, user = False ):
		if self.started and not self.waiting:
			self.waiting = True
			if self.cancel.isVisible():
				self.cancel.hide()
				self.close.show()

				if not user:
					self.infos[ 'filename' ].setText( '' )
					self.infos[ 'filesize' ].setText( '' )
					self.infos[ 'preview' ].setPixmap( QtGui.QPixmap() )

				self.cancel.setText( 'Waiting ...' )
				if self.thread and self.thread.is_alive():
					self.stopthread.set()
					self.thread.join()
			else:
				self.central( self.defaultPage )
				self.close.hide()
				self.cancel.show()

				self.started = False
				self.stopthread.clear()
				self.cancel.setText( 'Cancel' )

			self.waiting = False

	def mouseMoveEvent( self, event ):
		if event.buttons() & QtCore.Qt.LeftButton and self.drag:
			self.move( event.globalPos() - self.drag )
			event.accept()

	def mousePressEvent( self, event ):
		self.drag = 0
		if event.button() == QtCore.Qt.LeftButton:
			drag = ( event.globalPos() - self.frameGeometry().topLeft() )
			if drag.y() < 42:
				self.drag = drag
				event.accept()

	def closeEvent( self, event ):
		if not self.started or not self.cancel.isVisible():
			event.accept()
		else:
			event.ignore()

def launch():
	os.chdir( resource_path() )
	app = QtWidgets.QApplication( [] )

	style = ''
	with open( resource( 'style.qss', root = True ), 'r', encoding = 'utf-8', errors = 'ignore' ) as f:
		app.setStyleSheet( f.read() )

	win = Window()
	win.setup()
	win.show()

	qtRectangle = win.frameGeometry()
	centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
	qtRectangle.moveCenter( centerPoint )
	win.move( qtRectangle.topLeft() )

	win.activateWindow()
	win.setFocus()
	win.raise_()

	sys.exit( app.exec_() )

if __name__ == '__main__':
	launch()

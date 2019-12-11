#!/usr/bin/env python3
# -*- coding: utf-8 -*-

DIVIDE = [ 'png', 'tiff' ]
EXTENSIONS = [ 'png', 'jpeg', 'tiff', 'webp' ]
CONTROLS_CONFIGS = {
	'default':	[ 'minimize', 'maximize', 'cross', 10, 26, 86, 38, -( 86 + 15 ) ],
	'darwin':	[ 'cross', 'minimize', 'maximize', 20, 0, 76, 38, 8 ]
}

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

def process( files, watermark, target, quality = 100, opacity = 100, gravity = ( 0, 0 ), position = ( 0, 0 ), size = ( 0, 0 ), stopevent = None, sigprogress = None, sigcanceled = None, sigfinished = None ):
	global DIVIDE, os_name, startupinfo

	composite = resource( 'bin', os_name, 'composite', bin = True )

	opacity = ( '%d%%' % opacity )

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

	resume = [ [], [], [] ]
	total = len( files )
	for index, file in enumerate( files ):
		if stopevent and stopevent.is_set():
			if sigcanceled and not len( resume[ 2 ] ):
				sigcanceled()

			resume[ 2 ].append( file )
			continue
		elif sigprogress:
			sigprogress( index, total, file, None, None, None )

		q = quality
		if file.split( '.' )[ -1 ].lower() in DIVIDE:
			q = round( q / 10 )
		q = str( 100 if q <= 0 or q > 100 else q )

		t = os.path.join( target, os.path.basename( file ) )

		cmd = [ composite, '-watermark', opacity, '-gravity', g, '-geometry', geometry, '-quality', q, watermark, file, t ]
		error = False
		output = False
		try:
			output = subprocess.check_output( cmd, stdin = subprocess.PIPE, stderr = subprocess.STDOUT, env = os.environ, startupinfo = startupinfo )
			resume[ 0 ].append( file )
		except subprocess.CalledProcessError as e:
			error = True
			output = e.output
			resume[ 1 ].append( file )

		output = str( output, 'utf-8' )
		if sigprogress:
			sigprogress( index, total, file, cmd, error, output )

	if sigfinished:
		sigfinished( ( stopevent and stopevent.is_set() ), *resume )

class Image( QtWidgets.QLabel ):
	def __init__( self, name, width, height, mouseover = False, callback = None, path = None, parent = None ):
		super( Image, self ).__init__( parent )

		self.mouseoveron = False

		self.name = name
		self.path = path
		self.callback = callback
		self.mouseover = mouseover

		self.setObjectName( name )
		self.setFixedSize( width, height )
		self.setMouseTracking( False )

	def enterEvent( self, event ):
		self.mouseoveron = True
		self.update()

	def leaveEvent( self, event ):
		self.mouseoveron = False
		self.update()

	def paintEvent( self, event ):
		name = self.name
		opacity = ( type( self.mouseover ) is not str )
		white = ( self.isEnabled() and ( not self.mouseover or ( self.mouseover and self.mouseoveron ) ) )
		if not opacity:
			name = ( self.mouseover if white else name )

		file = name
		if self.path:
			file = os.path.join( self.path, file )

		painter = QtGui.QPainter( self )
		painter.setRenderHints( ( QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform ), True )

		image = QtGui.QPixmap.fromImage( QtGui.QImage( resource( '%s.png' % file ) ) )
		if opacity:
			painter.setOpacity( 1 if white else .3 )

		center = QtCore.QPoint( ( self.width() / 2 ), ( self.height() / 2 ) )
		painter.translate( center )

		painter.scale( 1 * ( self.width() / image.width() ), 1 * ( self.width() / image.height() ) )
		painter.translate( -( image.width() / 2 ), -( image.height() / 2 ) )

		painter.drawPixmap( 0, 0, image.width(), image.height(), image )

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
		file = os.path.join( 'gravity', '%s%s.%s' % ( self.prefix, self.gravity, self.extension ) )
		pixmap = QtGui.QPixmap( resource( file ) )
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
	sigcanceled = QtCore.pyqtSignal()
	sigfinished = QtCore.pyqtSignal( bool, list, list, list )
	sigprogress = QtCore.pyqtSignal( int, int, str, object, object, object )

	def __init__( self, parent = None ):
		super( Window, self ).__init__( parent )

		self.drag = 0
		self.step = 0
		self.paths = [ '', '', '' ]
		self.steps = [ [], [], [], [] ]
		self.resume = ''
		self.started = False
		self.waiting = False
		self.settings = {}
		self.sigcanceled.connect( self.canceled )
		self.sigfinished.connect( self.finished )
		self.sigprogress.connect( self.progress )
		self.stopthread = threading.Event()

	def setup( self ):
		global EXTENSIONS, CONTROLS_CONFIGS

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

		### Logo
		top = QtWidgets.QWidget( self )
		top.setObjectName( 'wlogo' )
		top.setGeometry( QtCore.QRect( 0, 0, 800, 50 ) )
		self.centralWidget.stackUnder( top )

		llayout = QtWidgets.QVBoxLayout( top )
		llayout.setAlignment( QtCore.Qt.AlignCenter )

		self.logo = QtWidgets.QLabel()
		self.logo.setObjectName( 'logo' )
		self.logo.setFixedSize( 140, 25 )
		llayout.addWidget( self.logo )

		### Controls
		mode = 'default'
		if os_name in CONTROLS_CONFIGS.keys():
			mode = os_name

		suffix = ( '_' + mode )
		icon1, icon2, icon3, size, spacing, width, height, position = CONTROLS_CONFIGS[ mode ]
		if position < 0:
			position = ( self.width() + position )

		self.controls = QtWidgets.QWidget( self )
		self.controls.setObjectName( 'controls' )
		self.controls.setGeometry( QtCore.QRect( position, 0, width, height ) )
		self.controls.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

		clayout = QtWidgets.QHBoxLayout( self.controls )
		clayout.setAlignment( QtCore.Qt.AlignLeft )
		clayout.setContentsMargins( 0, 0, 0, 0 )
		clayout.setSpacing( spacing )

		for item in [ icon1, icon2, icon3 ]:
			event = None
			if item == 'cross':
				event = ( lambda icon, event: self.close() )
			elif item == 'minimize':
				event = ( lambda icon, event: self.showMinimized() )

			file = ( item + suffix )
			mouseover = ( ( file + '_hover' ) if bool( event ) else item )

			icon = Image( file, size, size, mouseover, event, 'controls' )
			icon.setEnabled( bool( event ) )
			clayout.addWidget( icon )

		### Icons
		icons = QtWidgets.QWidget()
		icons.setObjectName( 'icons' )
		ilayout = QtWidgets.QHBoxLayout( icons )
		ilayout.setAlignment( QtCore.Qt.AlignCenter )
		ilayout.setSpacing( 38 )
		layout.addWidget( icons )

		for index, item in enumerate( [ 'signature', 'gallery', 'target', 'apply' ] ):
			if index:
				separator = QtWidgets.QWidget()
				separator.setProperty( 'cssClass', 'separator' )
				ilayout.addWidget( separator )
				self.steps[ index ].append( separator )

			icon = Image( item, 42, 42 )
			icon.setProperty( 'cssClass', 'icon' )
			ilayout.addWidget( icon )
			self.steps[ index ].append( icon )

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
		bsignature.setObjectName( 'bsignature' )
		bsignature.setProperty( 'cssClass', 'button' )
		bsignature.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		bsignature.clicked.connect( lambda: self.define( 0 ) )
		vlayout.addWidget( bsignature )
		self.steps[ 0 ].append( bsignature )

		nsignature = QtWidgets.QLabel( ', '.join( EXTENSIONS ) )
		nsignature.setObjectName( 'nsignature' )
		nsignature.setProperty( 'cssClass', 'note' )
		nsignature.setAlignment( QtCore.Qt.AlignHCenter )
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
		psignature.setObjectName( 'psignature' )
		psignature.setProperty( 'cssClass', 'path' )
		psignature.setAlignment( QtCore.Qt.AlignHCenter )
		vlayout.addWidget( psignature )
		self.steps[ 0 ].append( psignature )

		csignature = QtWidgets.QPushButton( 'Change' )
		csignature.setObjectName( 'csignature' )
		csignature.setProperty( 'cssClass', 'change' )
		csignature.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		csignature.clicked.connect( lambda: self.define( 0 ) )
		vlayout.addWidget( csignature )

		dsignature = QtWidgets.QLabel()
		dsignature.setObjectName( 'dsignature' )
		dsignature.setProperty( 'cssClass', 'details' )
		dsignature.setAlignment( QtCore.Qt.AlignHCenter )
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
		bgallery.setObjectName( 'bgallery' )
		bgallery.setProperty( 'cssClass', 'button' )
		bgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		bgallery.clicked.connect( lambda: self.define( 1 ) )
		vlayout.addWidget( bgallery )
		self.steps[ 1 ].append( bgallery )

		ngallery = QtWidgets.QLabel( 'contains: %s' % ', '.join( EXTENSIONS ) )
		ngallery.setObjectName( 'ngallery' )
		ngallery.setProperty( 'cssClass', 'note' )
		ngallery.setAlignment( QtCore.Qt.AlignHCenter )
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
		pgallery.setObjectName( 'pgallery' )
		pgallery.setProperty( 'cssClass', 'path' )
		pgallery.setAlignment( QtCore.Qt.AlignHCenter )
		vlayout.addWidget( pgallery )
		self.steps[ 1 ].append( pgallery )

		cgallery = QtWidgets.QPushButton( 'Change' )
		cgallery.setObjectName( 'cgallery' )
		cgallery.setProperty( 'cssClass', 'change' )
		cgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		cgallery.clicked.connect( lambda: self.define( 1 ) )
		vlayout.addWidget( cgallery )

		dgallery = QtWidgets.QLabel()
		dgallery.setObjectName( 'dgallery' )
		dgallery.setProperty( 'cssClass', 'details' )
		dgallery.setAlignment( QtCore.Qt.AlignHCenter )
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
		btarget.setObjectName( 'btarget' )
		btarget.setProperty( 'cssClass', 'button' )
		btarget.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
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
		pgallery.setObjectName( 'pgallery' )
		pgallery.setProperty( 'cssClass', 'path' )
		pgallery.setAlignment( QtCore.Qt.AlignHCenter )
		vlayout.addWidget( pgallery )
		self.steps[ 2 ].append( pgallery )

		cgallery = QtWidgets.QPushButton( 'Change' )
		cgallery.setObjectName( 'cgallery' )
		cgallery.setProperty( 'cssClass', 'change' )
		cgallery.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
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
		bapply.setObjectName( 'bapply' )
		bapply.setProperty( 'cssClass', 'button' )
		bapply.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
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
		lgravity.setObjectName( 'lgravity' )
		lgravity.setAlignment( QtCore.Qt.AlignLeft )
		slayout.addWidget( lgravity, 0, 0 )

		gravity = Gravity( '', 'png' )
		gravity.setObjectName( 'gravity' )
		gravity.setAlignment( QtCore.Qt.AlignCenter )
		gravity.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		slayout.addWidget( gravity, 0, 1, 3, 1 )
		self.settings[ 'gravity' ] = gravity

		## Quality
		lquality = QtWidgets.QLabel( 'Quality:' )
		lquality.setObjectName( 'lquality' )
		lquality.setAlignment( QtCore.Qt.AlignLeft )
		slayout.addWidget( lquality, 0, 3 )

		squality = QtWidgets.QSpinBox()
		squality.setProperty( 'cssClass', 'spinbox' )
		squality.setToolTip( '0 to 100% (for lossless rendering)' )
		squality.setRange( 1, 100 )
		squality.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		slayout.addWidget( squality, 0, 4 )
		self.settings[ 'quality' ] = squality

		## Opacity
		lopacity = QtWidgets.QLabel( 'Opacity:' )
		lopacity.setObjectName( 'lopacity' )
		lopacity.setAlignment( QtCore.Qt.AlignLeft )
		slayout.addWidget( lopacity, 0, 5 )

		sopacity = QtWidgets.QSpinBox()
		sopacity.setProperty( 'cssClass', 'spinbox' )
		sopacity.setToolTip( '0 to 100% (for lossless rendering)' )
		sopacity.setRange( 1, 100 )
		sopacity.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		slayout.addWidget( sopacity, 0, 6 )
		self.settings[ 'opacity' ] = sopacity

		## Position
		lpositionx = QtWidgets.QLabel( 'Position X:' )
		lpositionx.setObjectName( 'lpositionx' )
		lpositionx.setAlignment( QtCore.Qt.AlignLeft )
		slayout.addWidget( lpositionx, 1, 3 )

		spositionx = QtWidgets.QSpinBox()
		spositionx.setProperty( 'cssClass', 'spinbox' )
		spositionx.setToolTip( 'Expresses itself in pixel' )
		spositionx.setRange( -10000, 10000 )
		spositionx.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		slayout.addWidget( spositionx, 1, 4 )
		self.settings[ 'x' ] = spositionx

		lpositiony = QtWidgets.QLabel( 'Position Y:' )
		lpositiony.setObjectName( 'lpositiony' )
		lpositiony.setAlignment( QtCore.Qt.AlignLeft )
		slayout.addWidget( lpositiony, 1, 5 )

		spositiony = QtWidgets.QSpinBox()
		spositiony.setProperty( 'cssClass', 'spinbox' )
		spositiony.setToolTip( 'Expresses itself in pixel' )
		spositiony.setRange( -10000, 10000 )
		spositiony.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		slayout.addWidget( spositiony, 1, 6 )
		self.settings[ 'y' ] = spositiony

		## Size
		more = QtWidgets.QWidget()
		more.setObjectName( 'more' )
		more.setContentsMargins( 0, 0, 0, 0 )
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
		lwidth.setObjectName( 'lwidth' )
		lwidth.setAlignment( QtCore.Qt.AlignLeft )
		mlayout.addWidget( lwidth, 0, 1 )

		swidth = QtWidgets.QSpinBox()
		swidth.setProperty( 'cssClass', 'spinbox' )
		swidth.setToolTip( 'Expresses itself in pixel' )
		swidth.setRange( 1, 10000 )
		swidth.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
		mlayout.addWidget( swidth, 0, 2 )
		self.settings[ 'width' ] = swidth

		# Height
		lheight = QtWidgets.QLabel( 'Height:' )
		lheight.setObjectName( 'lheight' )
		lheight.setAlignment( QtCore.Qt.AlignLeft )
		mlayout.addWidget( lheight, 0, 3 )

		sheight = QtWidgets.QSpinBox()
		sheight.setProperty( 'cssClass', 'spinbox' )
		sheight.setToolTip( 'Expresses itself in pixel' )
		sheight.setRange( 1, 10000 )
		sheight.setAttribute( QtCore.Qt.WA_MacShowFocusRect, 0 )
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
		scroll = QtWidgets.QScrollArea()
		scroll.setAlignment( QtCore.Qt.AlignCenter )
		scroll.setWidgetResizable( True )
		scroll.setFixedHeight( 320 )
		layout.addWidget( scroll, 1, 0 )

		preview = QtWidgets.QLabel()
		preview.setAlignment( QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter )
		preview.setTextFormat( QtCore.Qt.RichText )
		preview.setWordWrap( True )
		preview.setObjectName( 'preview' )
		scroll.setWidget( preview )

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
		self.bcancel = QtWidgets.QPushButton( 'Cancel' )
		self.bcancel.setSizePolicy( QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed )
		self.bcancel.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		self.bcancel.setProperty( 'cssClass', 'button' )
		self.bcancel.setObjectName( 'cancel' )
		self.bcancel.clicked.connect( lambda: self.stopprocess( True ) )
		ilayout.addWidget( self.bcancel )

		# Close
		self.bclose = QtWidgets.QPushButton( 'Close' )
		self.bclose.setSizePolicy( QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed )
		self.bclose.setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		self.bclose.setProperty( 'cssClass', 'button' )
		self.bclose.setObjectName( 'close' )
		self.bclose.hide()
		self.bclose.clicked.connect( lambda: self.stopprocess( True ) )
		ilayout.addWidget( self.bclose )

		self.infos = {
			'progressbar':	progressbar,
			'preview':	preview,
			'filename':	filename,
			'filesize':	filesize,
			'states':	states
		}

		### Header on top
		self.central( self.processPage )
		self.central( self.defaultPage )

		### Values
		squality.setValue( 100 )
		sopacity.setValue( 100 )
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

	def canceled( self ):
		self.bcancel.hide()
		self.bcancel.setText( 'Cancel' )
		self.bclose.show()

		self.infos[ 'filename' ].setText( '' )
		self.infos[ 'filesize' ].setText( '' )
		self.infos[ 'preview' ].setPixmap( QtGui.QPixmap() )
		self.infos[ 'preview' ].setAlignment( QtCore.Qt.AlignCenter )
		self.infos[ 'preview' ].setText( ( self.resume or '' ).replace( '\n', '<br>' ) )

		self.waiting = False

	def finished( self, user = False, success = None, errors = None, ignored = None ):
		resume = ''
		template = '<div align="left" style="margin: 10px 10px 0px; font-weight: bold; text-decoration: underline;">%s:</div><div align="center" style="margin: 0px 20px;">%s</div>'

		if len( ignored ):
			files = ''
			for index, file in enumerate( ignored ):
				files += '%s%s' % ( ( ', ' if index else '' ), os.path.basename( file ) )
			resume += template % ( 'Ignored files', files )

		if len( errors ):
			files = ''
			for index, file in enumerate( errors ):
				files += '%s%s' % ( ( ', ' if index else '' ), os.path.basename( file ) )
			resume += template % ( 'Errors encountered', files )

		self.resume = ( resume or 'Everything went smoothly !' )
		if not user:
			self.stopprocess( user = user )

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

			#print( 'cmd:', cmd )
			if error:
				self.errors += 1
				#print( 'output:', output )

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
			opacity = self.settings[ 'opacity' ].value()
			gravity = self.settings[ 'gravity' ].relative
			position = ( self.settings[ 'x' ].value(), self.settings[ 'y' ].value() )
			size = ( 0, 0 )
			if bool( self.settings[ 'resize' ].checkState() ):
				size = ( self.settings[ 'width' ].value(), self.settings[ 'height' ].value() )

			args = ( files, self.paths[ 0 ], self.paths[ 2 ] )
			kwargs = {
				'quality':		quality,
				'opacity':		opacity,
				'gravity':		gravity,
				'position':		position,
				'size':			size,
				'stopevent':	self.stopthread,
				#'sigcanceled':	self.sigcanceled.emit,
				'sigfinished':	self.sigfinished.emit,
				'sigprogress':	self.sigprogress.emit,
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
			if self.bcancel.isVisible():
				if self.thread and self.thread.is_alive():
					def wait( thread, callback ):
						thread.join()
						callback()

					self.stopthread.set()
					self.bcancel.setText( 'Waiting ...' )
					thread = threading.Thread( target = wait, args = ( self.thread, self.sigcanceled.emit ), daemon = True )
					thread.start()
					return
				else:
					self.canceled()
			else:
				self.central( self.defaultPage )
				self.bclose.hide()
				self.bcancel.show()

				self.started = False
				self.stopthread.clear()

				self.infos[ 'preview' ].setText( '' )
				self.infos[ 'preview' ].setAlignment( QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter )

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
		if not self.started or not self.bcancel.isVisible():
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

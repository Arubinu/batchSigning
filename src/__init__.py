import os
import sys

path = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ) )
sys.path.append( '.' )
os.chdir( path )

from main import launch

if __name__ == '__main__':
	launch()

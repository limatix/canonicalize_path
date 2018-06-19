all:
	python setup.py build

install:
	python setup.py install --prefix=/usr/local 
	python setup.py install_data --prefix=/usr/local 

clean:
	python setup.py clean
	rm -f *~ *.pyc *.swp */*~ */*.pyc */*.swp
	rm -rf build/
	rm -rf dist/
	rm -rf canonicalize_path.egg-info
	rm -rf canonicalize_path/__pycache__

commit: clean
	git add -A # hg addrem
	git commit -a # hg commit





import shutil
import os.path
from distutils.core import setup,Extension
from distutils.command.install_lib import install_lib
from distutils.command.install import install
import sys

config_files=["canonical_paths.conf","tag_index_paths.conf"]

class install_lib_save_prefix(install_lib):
    """Save a file install_prefix.txt with the install prefix"""
    def run(self):
        install_lib.run(self)
        
        #sys.stderr.write("\nprefix:" + str((self.distribution.command_obj["install"].prefix))+"\n\n\n")
        
        #sys.stderr.write("\ninstall_dir:" + self.install_dir+"\n\n\n")
        #sys.stderr.write("\npackages:" + str(self.distribution.command_obj["build_py"].packages)+"\n\n\n")

        for package in self.distribution.command_obj["build_py"].packages:
            install_dir=os.path.join(*([self.install_dir] + package.split('.')))
            fh=open(os.path.join(install_dir,"install_prefix.txt"),"w")
            fh.write(self.distribution.command_obj["install"].prefix)
            fh.close()
            pass
        pass
    pass


class install_config_files(install):
    """store config files in PREFIX/etc"""
    def run(self):
        install.run(self)
        
        #sys.stderr.write("\nprefix:" + str((self.distribution.command_obj["install"].prefix))+"\n\n\n")
        
        if self.prefix=="/usr": 
            config_dir='/etc/canonicalize_path'
            pass
        else:
            config_dir=os.path.join(self.prefix,"etc","canonicalize_path")
            pass

        if not os.path.exists(config_dir):
            os.mkdir(config_dir)
            pass

        for configfile in config_files:
            if os.path.exists(os.path.join(config_dir,configfile)):
                os.remove(os.path.join(config_dir,configfile))
                pass
            shutil.copyfile(configfile,os.path.join(config_dir,configfile))
            pass
            
        pass
    pass

setup(name="canonicalize_path",
      description="path canonicalization",
      author="Stephen D. Holland",
      # url="http://thermal.cnde.iastate.edu/dataguzzler",
      packages=["canonicalize_path"],
      cmdclass={"install_lib": install_lib_save_prefix,
                "install": install_config_files})


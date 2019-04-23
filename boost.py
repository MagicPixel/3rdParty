#!/usr/bin/python

import os, sys, subprocess

import platform

import os, sys, subprocess


def install(source_root, build_root, install_root, build_model, build_type):
	os.chdir(source_root)
	print("source_root :" + source_root)
	cmd = ""
	if platform.system() == "Windows":
		subprocess.call(["./bootstrap.bat"])
		cmd = "./bjam.exe"
	else:
		subprocess.call(["bash","./bootstrap.sh"])
		cmd = "./bjam"
	
	if build_model == "x86":
		model = 32
	else:
		model = 64
	
	build_type = build_type.lower()

	
	build_cmd = [
	cmd,
	"install", 
	"--prefix=%s" % install_root,
	"--stagedir=%s" % build_root, 
	"--address-model=%d" % model, 
	"link=shared" ,
	"runtime-link=shared",
	"threading=multi",
	"%s" % build_type,
	]
	subprocess.call(build_cmd)


if __name__ == "__main__":
	if len(sys.argv) == 6:
		install(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
	else:
		root = os.getcwd()
		source_root = root + "/sources/boost"
		build_root = root + "/projects/boost"
		install_root = root + "/" + platform.system()
		build_model = "x64"
		build_type = "release"
		install(source_root, build_root, install_root, build_model, build_type)
		print "Usage: python " + sys.argv[0] + " source_root build_root install_root buld_model build_type"

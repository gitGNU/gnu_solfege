#!/usr/bin/python3

import subprocess
import os

def fail(*msg):
    print(*msg)
    exit(-1)


ver = "3.23.2"
tar = "solfege-%s.tar.gz" % ver

def sign(name, version):
    r = subprocess.call(["gpg", "-b", "%s-%s.tar.gz" % (name, version)])
    if r != 0:
        fail("GPG signing of %s-%s failed" % (name, version))

def create_directive(name, version):
    directive = "%s-%s.tar.gz.directive" % (name, version)
    directive_template = "\n".join([
        "version: '1.2'",
        "directory: solfege",
        "filename: %s-%s.tar.gz",
        ""]) % (name, version)

    with open(directive, 'w') as f:
        f.write(directive_template)

    r = subprocess.call(["gpg", "--clearsign", directive])
    if r != 0:
        fail("GPG signing of template failed")

def make_upload_script(name, namebin, version):
    with open("upload.lftp", "w") as f:
        print("open ftp-upload.gnu.org", file=f)
        print("cd incoming/alpha", file=f)
        print("put %s-%s.tar.gz" % (name, version), file=f)
        print("put %s-%s.tar.gz.sig" % (name, version), file=f)
        print("put %s-%s.tar.gz.directive.asc" % (name, version), file=f)
        print("put %s-%s.tar.gz" % (namebin, version), file=f)
        print("put %s-%s.tar.gz.sig" % (namebin, version), file=f)
        print("put %s-%s.tar.gz.directive.asc" % (namebin, version), file=f)

sign("solfege", ver)
create_directive("solfege", ver)

sign("solfege-bin", ver)
create_directive("solfege-bin", ver)

make_upload_script("solfege", "solfege-bin", ver)

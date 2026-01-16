#!/usr/bin/env python3
# CurseForge modpack installer
# This program is an alternative to the Twitch client, written for Linux users,
# so that they can install Minecraft modpacks from CurseForge.
# This tool requires that the user download the pack zip from CurseForge. It
# will then generate a complete Minecraft install directory with all of the
# mods and overrides installed.

import os
import sys
import shutil
import argparse
import pathlib

import mod_download
from zipfile import ZipFile

# shutil.copytree doesn't accept dirs_exist_ok until 3.8 which is fairly modern (I think some LTS distros still use 3.6)
# fall back to distutils copy_tree (the old solution) if needed
if sys.version_info.minor >= 8:
    import shutil
    def copy_tree(src, dest):
        shutil.copytree(src, dest, dirs_exist_ok=True)
else:
    from distutils.dir_util import copy_tree

# Files/directories to always copy when updating a modpack
# otherwise, only files and directories that don't exist in the new install will be copied
update_always_copy = [
    'options.txt',
    'optionsof.txt', # optifine options (may or may not exist)
    'servers.dat',
    'servers.dat_old',
    'screenshots'
]

# try to create a directory and all of its parent directories if they do not exist (like mkdir -p)
def mkdirp(path):
    if type(path) != pathlib.Path:
        path = pathlib.Path(path) # convert to pathlib path if a string is provided
    try:
        path.mkdir(parents=True, exist_ok=True)
    except TypeError: # exist_ok not defined
        try:
            path.mkdir(parents=True)
        except FileExistsError:
            if not path.is_dir():
                raise # keep exception if a non-directory file exists here

def main(zipfile, mods_dir):
    # Extract pack
    packname = os.path.splitext(zipfile)[0]
    packname = os.path.basename(packname)
    packdata_dir = '.packs/' + packname
    if os.path.isdir(packdata_dir):
        print("[pack data already unzipped]")
    else:
        mkdirp('.packs/')
        print("Extracting %s" % zipfile)
        with ZipFile(zipfile, 'r') as zf:
            zf.extractall(packdata_dir)

    _, manual_downloads = mod_download.main(packdata_dir + '/manifest.json', mods_dir)
    if len(manual_downloads) > 0:
        while True:
            actual_manual_dls = [] # which ones aren't already downloaded
            for url, resp in manual_downloads:
                outfile = resp[3]
                if not os.path.exists(outfile):
                    actual_manual_dls.append((url, outfile))
            if len(actual_manual_dls) > 0:
                print("====MANUAL DOWNLOAD REQUIRED====")
                print("The following mods cannot be downloaded due to the new Project Distribution Toggle.")
                print("Please download them manually; the files will be retrieved from your downloads directly.")
                print("If there is a 404 error opening any of these links, try replacing 'legacy.curseforge.com' with 'www.curseforge.com'")
                for url, outfile in actual_manual_dls:
                    print("* %s (%s)" % (url, os.path.basename(outfile)))

                # TODO save user's configured downloads folder somewhere
                user_downloads_dir = os.environ['HOME'] + '/Downloads'
                print("Retrieving downloads from %s - if that isn't your browser's download location, enter" \
                        % user_downloads_dir)
                print("the correct location below. Otherwise, press Enter to continue.")
                req_downloads_dir = input()

                req_downloads_dir = os.path.expanduser(req_downloads_dir)
                if len(req_downloads_dir) > 0:
                    if not os.path.isdir(req_downloads_dir):
                        print("- input directory is not a directory; ignoring")
                    else:
                        user_downloads_dir = req_downloads_dir
                print("Finding files in %s..." % user_downloads_dir)
                
                for url, outfile in actual_manual_dls:
                    fname = os.path.basename(outfile)
                    fname_plus = fname.replace(' ', '+')
                    dl_path = user_downloads_dir + '/' + fname
                    dl_path_plus = user_downloads_dir + '/' + fname_plus
                    if os.path.exists(dl_path_plus):
                        print(dl_path_plus)
                        shutil.move(dl_path_plus, outfile)
                    elif os.path.exists(dl_path):
                        print(dl_path)
                        shutil.move(dl_path, outfile)
            else:
                break

    print(f"Successfully downloaded the mods to {mods_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('zipfile')
    parser.add_argument(
        '--modsdir', dest='modsdir', required=True,
        help="Where mods are downloaded"
    )
    args = parser.parse_args(sys.argv[1:])
    main(
        args.zipfile,
        args.modsdir
    )

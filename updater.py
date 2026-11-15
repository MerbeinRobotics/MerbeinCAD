"""GitHub Releases update discovery and package validation, stdlib only."""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse


def clean_repo(value):
    value=value.strip().rstrip('/')
    if value.startswith('https://github.com/'):
        value=value[len('https://github.com/'):]
    if value.endswith('.git'):value=value[:-4]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*',value):
        raise ValueError('Enter owner/repository, e.g. merbeinrobotics/MerbeinCAD, or https://github.com/owner/repository')
    return value


def compare_version(a,b):
    def parse(x):
        if not re.fullmatch(r'v?\d+(?:\.\d+){1,3}',x):raise ValueError('Unrecognised version')
        return tuple(map(int,x.lstrip('v').split('.')))
    left,right=parse(a),parse(b)
    n=max(len(left),len(right))
    return (left+(0,)*(n-len(left))>right+(0,)*(n-len(right)))-(left+(0,)*(n-len(left))<right+(0,)*(n-len(right)))


def latest_release(repo):
    repo=clean_repo(repo)
    req=Request('https://api.github.com/repos/'+repo+'/releases/latest',headers={'Accept':'application/vnd.github+json','User-Agent':'MerbeinCAD-Updater'})
    with urlopen(req,timeout=15) as response:
        return json.load(response)


def download_release(asset,target,repo,tag):
    url=asset.get('browser_download_url','')
    expected_prefix=f'https://github.com/{clean_repo(repo)}/releases/download/{tag}/'
    if not url.startswith(expected_prefix) or not url.endswith('/MerbeinCAD_Update.zip'):
        raise ValueError('GitHub release asset URL does not match this repository, version and expected filename.')
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix('.part')
    h=hashlib.sha256();total=0
    try:
        with urlopen(Request(url,headers={'User-Agent':'MerbeinCAD-Updater'}),timeout=45) as response,open(tmp,'wb') as output:
            while True:
                chunk=response.read(1024*128)
                if not chunk:break
                total+=len(chunk)
                if total>100*1024*1024:raise ValueError('Update exceeds 100 MB limit.')
                h.update(chunk);output.write(chunk)
        digest=asset.get('digest')
        if digest and digest.startswith('sha256:') and h.hexdigest().lower()!=digest[7:].lower():
            raise ValueError('Downloaded update SHA-256 does not match GitHub release metadata.')
        if total<100:raise ValueError('Downloaded archive is unexpectedly small.')
        tmp.replace(target)
    finally:
        if tmp.exists():tmp.unlink()
    return target


def unpack_release(source,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Pending update folder already exists: '+str(destination))
    with zipfile.ZipFile(source) as z:
        names=z.namelist()
        if not names or len(names)>300:raise ValueError('Invalid update archive')
        for entry in z.infolist():
            name=entry.filename.replace('\\','/')
            parts=Path(name).parts
            if name.startswith('/') or '..' in parts or ':' in name or not (name.startswith('Application/') or name in ('Install_Update.ps1','Update_MerbeinCAD.bat','README_FIRST.txt')):
                raise ValueError('Update archive contains an unexpected path: '+name)
            if entry.file_size>100*1024*1024:raise ValueError('Update file too large')
        if 'Application/app.py' not in names or 'Install_Update.ps1' not in names:
            raise ValueError('Update archive is missing required files.')
        destination.mkdir(parents=True)
        try:z.extractall(destination)
        except Exception:
            shutil.rmtree(destination,ignore_errors=True);raise
    return destination

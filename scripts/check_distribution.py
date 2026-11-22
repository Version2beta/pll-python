"""Complete non-writing build/install judge. No provisioning/network; do not change."""
import email
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['__init__.py', '_errors.py', '_values.py', '_follower_values.py',
           '_rate.py', '_span.py', '_pacer.py', '_follower.py', 'pllpace.py']
PINS = dict(line.strip().split('==') for line in (ROOT/'scripts/build-requirements.txt').read_text().splitlines())


def main():
    build_python = os.environ.get('PLL_BUILD_PYTHON')
    if not build_python or not Path(build_python).is_absolute():
        raise SystemExit('set PLL_BUILD_PYTHON to externally provisioned pinned venv interpreter')
    config = tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert config['build-system'] == {'requires':['setuptools==84.2.1','wheel==0.48.0'],
                                      'build-backend':'setuptools.build_meta'}
    project = config['project']
    assert project['name']=='pypll' and project['version']=='0.1.0'
    assert project['requires-python']=='>=3.11' and project['readme']=='README.md'
    assert project['license']=='MIT' and project['license-files']==['LICENSE']
    assert project['dependencies']==[]
    assert project['scripts'] == {'pllpace': 'pll.pllpace:main'}
    assert not any(project.get(k) for k in ('gui-scripts','entry-points','optional-dependencies','dynamic'))
    packages = config['tool']['setuptools']
    assert packages['packages']==['pll'] and packages['include-package-data'] is False
    assert not packages.get('py-modules')
    env = dict(os.environ, PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1',
               PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    def run(args, cwd, capture=False):
        return subprocess.check_output(args, cwd=cwd, env=env, text=True) if capture else subprocess.run(args, cwd=cwd, env=env, check=True)
    with tempfile.TemporaryDirectory(prefix='pll-distribution-') as tmp:
        tmp = Path(tmp)
        installed = json.loads(run([build_python,'-I','-c',
            'import importlib.metadata as m,json;print(json.dumps({n:m.version(n) for n in '+repr(list(PINS))+'}))'], tmp, True))
        if installed != PINS:
            raise AssertionError(('build prerequisite pins',installed,PINS))
        src = tmp/'source'
        (src/'pll').mkdir(parents=True)
        for n in ('README.md','LICENSE','pyproject.toml','MANIFEST.in'):
            shutil.copyfile(ROOT/n, src/n)
        for n in SOURCES:
            shutil.copyfile(ROOT/'pll'/n, src/'pll'/n)
        dist = tmp/'dist'
        run([build_python,'-I','-m','build','--no-isolation','--sdist','--wheel','--outdir',str(dist)],src)
        wheel = next(dist.glob('*.whl'))
        sdist = next(dist.glob('*.tar.gz'))
        with tarfile.open(sdist) as archive:
            members=archive.getnames()
            prefix=members[0].split('/')[0]
            allowed={'README.md','LICENSE','pyproject.toml','MANIFEST.in','PKG-INFO','setup.cfg'}
            for n in members:
                rel='/'.join(n.split('/')[1:])
                if not rel or rel in ('pll','pypll.egg-info'):
                    continue
                if rel not in allowed and rel not in {'pll/'+x for x in SOURCES} and not rel.startswith('pypll.egg-info/'):
                    raise AssertionError(('unexpected sdist member',rel))
            archive.extractall(tmp/'unpacked', filter='data')
        print('SDIST MANIFEST '+json.dumps(members))
        second = tmp/'sdist-wheel'
        run([build_python,'-I','-m','build','--no-isolation','--wheel','--outdir',str(second)],tmp/'unpacked'/prefix)
        wheels=[wheel,next(second.glob('*.whl'))]
        examples='\n'.join(re.findall(r'```python\n(.*?)```',(ROOT/'README.md').read_text(),re.S))
        for w in wheels:
            with zipfile.ZipFile(w) as archive:
                names=archive.namelist()
                assert {n for n in names if n.startswith('pll/')} == {'pll/'+n for n in SOURCES}, names
                assert all(n.startswith(('pll/','pypll-0.1.0.dist-info/')) for n in names),names
                metadata=email.message_from_bytes(archive.read('pypll-0.1.0.dist-info/METADATA'))
                assert metadata['Name']=='pypll' and metadata['Version']=='0.1.0'
                assert metadata['Requires-Python']=='>=3.11' and not metadata.get_all('Requires-Dist')
                assert metadata['License-Expression']=='MIT'
                assert archive.read('pypll-0.1.0.dist-info/entry_points.txt').decode().strip() == '[console_scripts]\npllpace = pll.pllpace:main'
                assert archive.read('pypll-0.1.0.dist-info/licenses/LICENSE')==(ROOT/'LICENSE').read_bytes()
                for n in SOURCES:
                    assert archive.read('pll/'+n)==(ROOT/'pll'/n).read_bytes()
            print('WHEEL MANIFEST '+json.dumps(names))
            for interpreter in ('python3.11','python3'):
                venv=tmp/(w.parent.name+'-'+interpreter)
                run([shutil.which(interpreter),'-I','-m','venv',str(venv)],tmp)
                py=str(venv/'bin/python')
                run([py,'-I','-m','pip','install','--no-index','--no-deps',str(w)],tmp)
                probe="import pll,sys,pathlib; assert pathlib.Path(pll.__file__).is_relative_to(sys.prefix); print(pll.__file__)\n"+examples
                run([py,'-I','-c',probe],tmp)
                probe_cli = "import pll.pllpace,sys,pathlib,importlib.metadata as m; assert pathlib.Path(pll.pllpace.__file__).is_relative_to(sys.prefix); ep=[e for e in m.distribution('pypll').entry_points if e.name=='pllpace']; assert len(ep)==1 and ep[0].load() is pll.pllpace.main; print(pll.pllpace.__file__)"
                run([py,'-I','-c',probe_cli],tmp)
                for command in ([str(venv/'bin/pllpace')], [py,'-I','-m','pll.pllpace']):
                    run(command+['--help'],tmp)
                    observed=run(command+['-seconds','.002','-bps','8','-unit-bytes','1'],tmp,True)
                    assert '1 offered units, 1 writer-accepted bytes' in observed, observed
        print('PASS DISTRIBUTION BUILDS AND INSTALLED EXAMPLES')


if __name__ == '__main__':
    main()

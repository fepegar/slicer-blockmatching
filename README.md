# Blockmatching
3D Slicer module as a GUI for `blockmatching`.

In a terminal, do:
```
mkdir ~/git
cd ~/git
git clone https://github.com/fepegar/blockmatching.git
mkdir ~/bin
ln -s $(which blockmatching) ~/bin
```


In `~/.slicerrc.py`:

```
import os

import qt
import slicer

moduleFactory = slicer.app.moduleManager().factoryManager()
 
dirs = ['~/slicer',
        '~/git/blockmatching']

dirs = [os.path.expanduser(d) for d in dirs]

for d in dirs:
    for fn in os.listdir(d):
        if not fn.endswith('.py'): continue
        if 'update' in fn: continue
        fp = os.path.join(d, fn)
        moduleFactory.registerModule(qt.QFileInfo(fp))
        moduleFactory.loadModules([os.path.splitext(fn)[0]])
```




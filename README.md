# Blockmatching
[3D Slicer](https://www.slicer.org/) module as a GUI for `blockmatching`.

In a terminal, run:
```
mkdir ~/git
cd ~/git
git clone https://github.com/fepegar/slicer-blockmatching.git
mkdir ~/bin
ln -s $(which blockmatching) ~/bin
```


In `~/.slicerrc.py`:

```
import os
import qt

moduleFactory = slicer.app.moduleManager().factoryManager()
 
dirs = ['~/git/slicer-blockmatching']

dirs = filter(os.path.isdir, [os.path.expanduser(d) for d in dirs])

for d in dirs:
    for fn in os.listdir(d):
        if not fn.endswith('.py'):
            continue
        fp = os.path.join(d, fn)
        moduleFactory.registerModule(qt.QFileInfo(fp))
        moduleFactory.loadModules([os.path.splitext(fn)[0]])
```




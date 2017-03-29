# Blockmatching
3D Slicer module as a GUI for blockmatching.

In `~/.slicerrc.py`:

```
moduleFactory = slicer.app.moduleManager().factoryManager()
 
dirs = ('/home/fernando/slicer',
        '/home/fernando/git/blockmatching')

for d in dirs:
    for fn in os.listdir(d):
        if not fn.endswith('.py'): continue
        if 'update' in fn: continue
        fp = os.path.join(d, fn)
        moduleFactory.registerModule(qt.QFileInfo(fp))
        moduleFactory.loadModules([os.path.splitext(fn)[0]])
```

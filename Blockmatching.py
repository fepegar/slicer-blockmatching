import os
import time
import shutil
import random
import string
import datetime
import subprocess

import numpy as np
import sitkUtils as su
import SimpleITK as sitk
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *


# BLOCKMATCHING_PATH = '/home/fernando/git/morpheme-privat/vt/build/bin/blockmatching'
BLOCKMATCHING_PATH = os.path.expanduser('~/bin/blockmatching')
QT_ALIGN_CENTER = 4
TRANSFORMATIONS = ['Rigid', 'Similitude', 'Affine', 'Vectorfield']


class Blockmatching(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Blockmatching"
        self.parent.categories = ["Registration"]
        self.parent.dependencies = []
        self.parent.contributors = ["Fernando Perez-Garcia (fepegar@gmail.com - Brain & Spine Institute - Paris)"]
        self.parent.helpText = """
        """
        self.parent.acknowledgementText = """
        """



class BlockmatchingWidget(ScriptedLoadableModuleWidget):

    def __init__(self, parent):

        ScriptedLoadableModuleWidget.__init__(self, parent)


    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = BlockmatchingLogic()
        self.makeGUI()
        self.onInputModified()
        self.onTransformationTypeChanged()


    def makeGUI(self):
        """
        Usage: blockmatching -reference|-ref %s -floating|-flo %s -result|-res %s
        [-initial-transformation|-init-trsf|-left-transformation|-left-trsf %s]
        [-initial-voxel-transformation|-init-voxel-trsf|-left-voxel-transformation|-left-voxel-trsf %s]
        [-initial-result-transformation|-init-res-trsf %s]
        [-initial-result-voxel-transformation|-init-res-voxel-trsf %s]
        [-result-transformation|-res-trsf %s]
        [-result-voxel-transformation|-res-voxel-trsf %s]
        [-normalisation|-norma|-rescale|-no-normalisation|-no-norma|-no-rescale]
        [-no-composition-with-initial] [-composition-with-initial]
        [-pyramid-lowest-level | -py-ll %d] [-pyramid-highest-level | -py-hl %d]
        [-pyramid-gaussian-filtering | -py-gf]
        [-block-size|-bl-size %d %d %d] [-block-spacing|-bl-space %d %d %d]
        [-block-border|-bl-border %d %d %d]
        [-floating-low-threshold | -flo-lt %d]
        [-floating-high-threshold | -flo-ht %d]
        [-floating-removed-fraction | -flo-rf %f]
        [-reference-low-threshold | -ref-lt %d]
        [-reference-high-threshold | -ref-ht %d]
        [-reference-removed-fraction | -ref-rf %f]
        [-floating-selection-fraction[-ll|-hl] | -flo-frac[-ll|-hl] %lf]
        [-search-neighborhood-half-size | -se-hsize %d %d %d]
        [-search-neighborhood-step | -se-step %d %d %d]
        [-similarity-measure | -similarity | -si [cc]]
        [-similarity-measure-threshold | -si-th %lf]
        [-transformation-type|-transformation|-trsf-type %s]
        [-elastic-regularization-sigma[-ll|-hl] | -elastic-sigma[-ll|-hl]  %lf %lf %lf]
        [-estimator-type|-estimator|-es-type wlts|lts|wls|ls]
        [-lts-cut|-lts-fraction %lf] [-lts-deviation %f] [-lts-iterations %d]
        [-fluid-sigma|-lts-sigma[-ll|-hl] %lf %lf %lf]
        [-vector-propagation-distance|-propagation-distance|-pdistance %f]
        [-vector-fading-distance|-fading-distance|-fdistance %f]
        [-max-iteration[-ll|-hl]|-max-iter[-ll|-hl] %d] [-corner-ending-condition|-rms]
        [-gaussian-filter-type|-filter-type deriche|fidrich|young-1995|young-2002|...
        ...|gabor-young-2002|convolution]
        [-default-filenames|-df] [-no-default-filenames|-ndf]
        [-command-line %s] [-logfile %s]
        [-vischeck] [-write_def]
        [-parallel|-no-parallel] [-max-chunks %d]
        [-parallelism-type|-parallel-type default|none|openmp|omp|pthread|thread]
        [-omp-scheduling|-omps default|static|dynamic-one|dynamic|guided]
        [-verbose|-v] [-no-verbose|-noverbose|-nv]
        [-debug|-D] [-no-debug|-nodebug]
        [-trace|-no-trace]
        [-print-parameters|-param]
        [-print-time|-time] [-no-time|-notime]

        """

        self.makeInputsButton()
        self.makeParametersButton()
        self.makeOutputsButton()

        self.applyButton = qt.QPushButton('Apply')
        self.applyButton.setDisabled(True)
        self.applyButton.clicked.connect(self.onApply)
        self.parent.layout().addWidget(self.applyButton)

        self.parent.layout().addStretch()


    def makeInputsButton(self):
        self.inputsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.inputsCollapsibleButton.text = 'Inputs'
        self.layout.addWidget(self.inputsCollapsibleButton)

        self.inputsLayout = qt.QFormLayout(self.inputsCollapsibleButton)


        # Reference
        self.referenceSelector = slicer.qMRMLNodeComboBox()
        self.referenceSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.referenceSelector.selectNodeUponCreation = False
        self.referenceSelector.addEnabled = False
        self.referenceSelector.removeEnabled = True
        self.referenceSelector.noneEnabled = False
        self.referenceSelector.showHidden = False
        self.referenceSelector.showChildNodeTypes = True
        self.referenceSelector.setMRMLScene(slicer.mrmlScene)
        self.referenceSelector.currentNodeChanged.connect(self.onInputModified)
        self.inputsLayout.addRow("Reference: ", self.referenceSelector)


        # Floating
        self.floatingSelector = slicer.qMRMLNodeComboBox()
        self.floatingSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.floatingSelector.selectNodeUponCreation = False
        self.floatingSelector.addEnabled = False
        self.floatingSelector.removeEnabled = True
        self.floatingSelector.noneEnabled = False
        self.floatingSelector.showHidden = True
        self.floatingSelector.showChildNodeTypes = True
        self.floatingSelector.setMRMLScene(slicer.mrmlScene)
        self.floatingSelector.currentNodeChanged.connect(self.onInputModified)
        self.inputsLayout.addRow("Floating: ", self.floatingSelector)


        # Initial transform
        self.initialTransformSelector = slicer.qMRMLNodeComboBox()
        self.initialTransformSelector.nodeTypes = ["vtkMRMLTransformNode"]
        self.initialTransformSelector.selectNodeUponCreation = True
        self.initialTransformSelector.addEnabled = False
        self.initialTransformSelector.removeEnabled = True
        self.initialTransformSelector.noneEnabled = True
        self.initialTransformSelector.showHidden = False
        self.initialTransformSelector.showChildNodeTypes = True
        self.initialTransformSelector.setMRMLScene(slicer.mrmlScene)
        self.initialTransformSelector.baseName = 'Initial transform'
        self.initialTransformSelector.currentNodeChanged.connect(self.onInputModified)
        self.inputsLayout.addRow("Initial transform: ", self.initialTransformSelector)


    def makeOutputsButton(self):
        self.outputsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.outputsCollapsibleButton.text = 'Outputs'
        self.layout.addWidget(self.outputsCollapsibleButton)

        self.outputsLayout = qt.QFormLayout(self.outputsCollapsibleButton)

        # Result transform
        self.resultTransformSelector = slicer.qMRMLNodeComboBox()
        self.resultTransformSelector.nodeTypes = ["vtkMRMLTransformNode"]
        self.resultTransformSelector.selectNodeUponCreation = True
        self.resultTransformSelector.addEnabled = True
        self.resultTransformSelector.removeEnabled = True
        self.resultTransformSelector.renameEnabled = True
        self.resultTransformSelector.noneEnabled = True
        self.resultTransformSelector.showHidden = False
        self.resultTransformSelector.showChildNodeTypes = True
        self.resultTransformSelector.setMRMLScene(slicer.mrmlScene)
        self.resultTransformSelector.currentNodeChanged.connect(self.onInputModified)
        self.outputsLayout.addRow("Result transform: ", self.resultTransformSelector)


        # Result volume
        self.resultVolumeSelector = slicer.qMRMLNodeComboBox()
        self.resultVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.resultVolumeSelector.selectNodeUponCreation = True
        self.resultVolumeSelector.addEnabled = True
        self.resultVolumeSelector.removeEnabled = True
        self.resultVolumeSelector.renameEnabled = True
        self.resultVolumeSelector.noneEnabled = True
        self.resultVolumeSelector.showHidden = False
        self.resultVolumeSelector.showChildNodeTypes = True
        self.resultVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.resultVolumeSelector.currentNodeChanged.connect(self.onInputModified)
        self.outputsLayout.addRow("Result volume: ", self.resultVolumeSelector)


    def makeParametersButton(self):
        self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.parametersCollapsibleButton.text = 'Parameters'
        self.layout.addWidget(self.parametersCollapsibleButton)
        self.parametersLayout = qt.QFormLayout(self.parametersCollapsibleButton)

        self.makeTransformationTypeWidgets()

        self.pyramidGroupBox = qt.QGroupBox()
        self.pyramidLayout = qt.QGridLayout(self.pyramidGroupBox)
        self.parametersLayout.addRow('Pyramid levels:', self.pyramidGroupBox)

        self.pyramidHighestSpinBox = qt.QSpinBox()
        self.pyramidHighestSpinBox.value = 3
        self.pyramidHighestSpinBox.valueChanged.connect(self.onPyramidLevelsChanged)
        self.pyramidHighestLabel = qt.QLabel()
        self.pyramidHighestLabel.setAlignment(QT_ALIGN_CENTER)
        self.pyramidLayout.addWidget(qt.QLabel('Highest:'), 0, 0)
        self.pyramidLayout.addWidget(self.pyramidHighestSpinBox, 0, 1)
        self.pyramidLayout.addWidget(self.pyramidHighestLabel, 0, 2)

        self.pyramidLowestSpinBox = qt.QSpinBox()
        self.pyramidLowestSpinBox.value = 2
        self.pyramidLowestSpinBox.valueChanged.connect(self.onPyramidLevelsChanged)
        self.pyramidLowestLabel = qt.QLabel()
        self.pyramidLowestLabel.setAlignment(QT_ALIGN_CENTER)
        self.pyramidLayout.addWidget(qt.QLabel('Lowest:'), 1, 0)
        self.pyramidLayout.addWidget(self.pyramidLowestSpinBox, 1, 1)
        self.pyramidLayout.addWidget(self.pyramidLowestLabel, 1, 2)

        self.pyramidGaussianFilteringCheckBox = qt.QCheckBox()
        self.pyramidLayout.addWidget(qt.QLabel('Gaussian filtering:'), 2, 0)
        self.pyramidLayout.addWidget(self.pyramidGaussianFilteringCheckBox, 2, 1)


    def makeTransformationTypeWidgets(self):
        self.trsfTypeGroupBox = qt.QGroupBox()
        self.parametersLayout.addRow('Transformation type:', self.trsfTypeGroupBox)
        trsfTypeLayout = qt.QHBoxLayout(self.trsfTypeGroupBox)

        self.trsfTypeRadioButtons = []
        for trsfType in TRANSFORMATIONS:
            radioButton = qt.QRadioButton(trsfType)
            radioButton.clicked.connect(self.onTransformationTypeChanged)
            self.trsfTypeRadioButtons.append(radioButton)
            trsfTypeLayout.addWidget(radioButton)

        self.trsfTypeRadioButtons[0].setChecked(True)


    def getSelectedTransformationType(self):
        for b in self.trsfTypeRadioButtons:
            if b.isChecked():
                trsfType = str(b.text).lower()
        return trsfType


    def getCommandLineList(self):
        self.tempDir = str(slicer.util.tempDirectory())

        self.refPath = self.logic.getNodeFilepath(self.referenceVolumeNode)
        self.floPath = self.logic.getNodeFilepath(self.floatingVolumeNode)

        refName = self.referenceVolumeNode.GetName()
        floName = self.floatingVolumeNode.GetName()

        dateTime = datetime.datetime.now()

        # We make sure they are in the disk
        if not self.refPath or not self.logic.hasNiftiExtension(self.refPath):
            self.refPath = self.logic.getTempPath(self.tempDir,
                                                  '.nii',
                                                  filename=refName,
                                                  dateTime=dateTime)
            slicer.util.saveNode(self.referenceVolumeNode, self.refPath)
        if not self.floPath or not self.logic.hasNiftiExtension(self.floPath):
            self.floPath = self.logic.getTempPath(self.tempDir,
                                                  '.nii',
                                                  filename=floName,
                                                  dateTime=dateTime)
            slicer.util.saveNode(self.floatingVolumeNode, self.floPath)


        self.resPath = self.logic.getTempPath(self.tempDir,
                                              '.nii',
                                              filename='{}_on_{}'.format(floName, refName),
                                              dateTime=dateTime)
        self.resultTransformPath = self.logic.getTempPath(self.tempDir,
                                                          '.trsf',
                                                          filename='t_ref-{}_flo-{}'.format(refName, floName),
                                                          dateTime=dateTime)

        trsfType = self.getSelectedTransformationType()

        # Save the command line for debugging
        self.cmdPath = self.logic.getTempPath(self.tempDir,
                                              '.txt',
                                              filename='cmd_ref-{}_flo-{}_{}'.format(refName, floName, trsfType),
                                              dateTime=dateTime)
        self.logPath = self.logic.getTempPath(self.tempDir,
                                              '.txt',
                                              filename='log_ref-{}_flo-{}_{}'.format(refName, floName, trsfType),
                                              dateTime=dateTime)

        cmd = [BLOCKMATCHING_PATH]
        cmd += ['-reference', self.refPath]
        cmd += ['-floating', self.floPath]
        cmd += ['-result', self.resPath]
        cmd += ['-result-transformation', self.resultTransformPath]
        cmd += ['-pyramid-highest-level', str(self.pyramidHighestSpinBox.value)]
        cmd += ['-pyramid-lowest-level', str(self.pyramidLowestSpinBox.value)]
        cmd += ['-transformation-type', trsfType]
        cmd += ['-command-line', self.cmdPath]
        cmd += ['-logfile', self.logPath]

        if self.pyramidGaussianFilteringCheckBox.isChecked():
            cmd += ['-pyramid-gaussian-filtering']

        if self.initialTransformNode:
            self.initialTransformPath = str(self.logic.getTempPath(self.tempDir, '.trsf', dateTime=dateTime))
            self.logic.writeBaladinMatrix(self.initialTransformNode, self.initialTransformPath)
            cmd += ['-initial-transformation', self.initialTransformPath]
            cmd += ['-composition-with-initial']

        self.commandLineList = cmd


    def printCommandLine(self):
        """
        Pretty-prints the command line so that it can be copied from the Python
        console and pasted on a terminal.
        """
        prettyCmd = []
        for s in self.commandLineList:
            if s.startswith('-'):
                prettyCmd.append('\\\n')
            prettyCmd.append(s)
        print ' '.join(prettyCmd)


    def repareResults(self):
        """
        This is used to convert output .hdr Analyze into NIfTI
        """

        if self.resPath.endswith('.hdr'):
            print 'Correcting result .hdr image'
            shutil.copy(self.refPath, self.resPath)


    def loadResults(self):
        # Remove transform from reference
        self.referenceVolumeNode.SetAndObserveTransformNodeID(None)

        # Load the result node
        if self.resultVolumeNode is not None:
            # Remove result node
            resultName = self.resultVolumeNode.GetName()
            slicer.mrmlScene.RemoveNode(self.resultVolumeNode)

            # Load the new one
            # When loading a 2D image with slicer.util, there is a bug that
            # keeps stacking the output result instead of creating a 2D image
            if self.logic.is2D(self.referenceVolumeNode):  # load using SimpleITK
                resultImage = sitk.ReadImage(self.resPath)
                su.PushToSlicer(resultImage, resultName, overwrite=True)
                self.resultVolumeNode = slicer.util.getNode(resultName)
            else:  # load using slicer.util.loadVolume()
                self.resultVolumeNode = slicer.util.loadVolume(self.resPath, returnNode=True)[1]
            self.resultVolumeNode.SetName(resultName)
            self.resultVolumeSelector.setCurrentNode(self.resultVolumeNode)
            fgVolume = self.resultVolumeNode

        # If a transform was given, copy the result in it and apply it to the floating image
        trsfType = self.getSelectedTransformationType()

        if self.resultTransformNode is not None:
            if trsfType != 'vectorfield':  # linear
                matrix = self.logic.readBaladinMatrix(self.resultTransformPath)
                vtkMatrix = self.logic.getVTKMatrixFromNumpyMatrix(matrix)
                self.resultTransformNode.SetMatrixTransformFromParent(vtkMatrix)
            else:  # non-linear
                # Remove result transform node from scene
                resultTransformName = self.resultTransformNode.GetName()
                slicer.mrmlScene.RemoveNode(self.resultTransformNode)

                # Load the generated transform node
                self.displacementFieldPath = self.resultTransformPath.replace('.trsf', '.nii')
                self.resultTransformNode = self.logic.vectorfieldToDisplacementField(
                    self.resultTransformPath,
                    self.referenceVolumeNode,
                    self.displacementFieldPath)
                self.resultTransformNode.SetName(resultTransformName)
                self.resultTransformSelector.setCurrentNode(self.resultTransformNode)

            # Apply transform to floating if no result volume node was selected
            if self.resultVolumeNode is None:
                self.floatingVolumeNode.SetAndObserveTransformNodeID(self.resultTransformNode.GetID())
                fgVolume = self.floatingVolumeNode

        self.logic.setSlicesBackAndForeground(bgVolume=self.referenceVolumeNode,
                                              fgVolume=fgVolume,
                                              opacity=0.5,
                                              colors=True)

        self.logic.centerViews()


    def outputsExist(self):
        """
        We need this because it's not clear that blockmatching returns non-zero
        when failed
        """
        if self.resultVolumeNode is not None:
            if not os.path.isfile(self.resPath):
                return False

        if self.resultTransformNode is not None:
            if not os.path.isfile(self.resultTransformPath):
                return False

        return True


    def validateMatrices(self):
        refQFormCode, refSFormCode = self.logic.getQFormAndSFormCodes(self.referenceVolumeNode)
        floQFormCode, floSFormCode = self.logic.getQFormAndSFormCodes(self.floatingVolumeNode)
        if refQFormCode != 0 and floQFormCode != 0: return
        messages = ['Registration results might be unexpected:', '\n']
        if refQFormCode == 0:
            messages.append('Reference image does not have a valid qform_code')
        if floQFormCode == 0:
            messages.append('Floating image does not have a valid qform_code')
        message = '\n'.join(messages)
        slicer.util.warningDisplay(message)


    def validateRefIsFloating(self):
        if self.referenceVolumeNode is self.floatingVolumeNode:
            slicer.util.warningDisplay('Reference and floating images are the same')


    def showWarnings(self):
        self.validateRefIsFloating()
        self.validateMatrices()


    def readParameters(self):
        self.referenceVolumeNode = self.referenceSelector.currentNode()
        self.floatingVolumeNode = self.floatingSelector.currentNode()
        self.initialTransformNode = self.initialTransformSelector.currentNode()

        self.resultVolumeNode = self.resultVolumeSelector.currentNode()
        self.resultTransformNode = self.resultTransformSelector.currentNode()


    ### Signals ###
    def onInputModified(self):
        self.readParameters()
        validMinimumInputs = self.referenceVolumeNode and \
                             self.floatingVolumeNode and \
                             (self.resultVolumeNode or self.resultTransformNode)
        self.applyButton.setEnabled(validMinimumInputs)

        self.referencePyramidMap = self.logic.getPyramidShapesMap(self.referenceVolumeNode)
        if self.referencePyramidMap is None:
            self.pyramidHighestSpinBox.setDisabled(True)
            self.pyramidLowestSpinBox.setDisabled(True)
        else:
            self.pyramidHighestSpinBox.setEnabled(True)
            self.pyramidLowestSpinBox.setEnabled(True)
            self.pyramidHighestSpinBox.maximum = max(self.referencePyramidMap.keys())
        self.onPyramidLevelsChanged()


    def onTransformationTypeChanged(self):
        trsf = self.getSelectedTransformationType()
        self.resultTransformSelector.baseName = 'Output %s transform' % trsf
        self.resultVolumeSelector.baseName = 'Output %s volume' % trsf


    def onPyramidLevelsChanged(self):
        self.pyramidLowestSpinBox.maximum = self.pyramidHighestSpinBox.value
        self.pyramidHighestSpinBox.minimum = self.pyramidLowestSpinBox.value

        if self.referencePyramidMap is None:
            self.pyramidHighestLabel.text = ''
            self.pyramidLowestLabel.text = ''
        else:
            self.pyramidHighestLabel.text = self.referencePyramidMap[self.pyramidHighestSpinBox.value]
            self.pyramidLowestLabel.text = self.referencePyramidMap[self.pyramidLowestSpinBox.value]


    def onApply(self):
        self.readParameters()
        self.getCommandLineList()
        self.showWarnings()
        print '\n\n'
        self.printCommandLine()
        tIni = time.time()
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            p = subprocess.Popen(self.commandLineList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = p.communicate()
            print '\nBlockmatching returned {}'.format(p.returncode)
            if p.returncode != 0 or not self.outputsExist():
                # Newer versions of blockmatching return 0
                # Apparently it always returns 0 :(
                qt.QApplication.restoreOverrideCursor()
                errorMessage = ''
                if not self.outputsExist():
                    errorMessage += 'Output volume not written on the disk\n\n'
                errorMessage += output[1]
                slicer.util.errorDisplay(errorMessage, windowTitle="Registration error")
            else:
                tFin = time.time()
                print '\nRegistration completed in {:.2f} seconds'.format(tFin - tIni)
                self.repareResults()
                self.loadResults()
        except OSError as e:
            print e
            print 'Is blockmatching correctly installed?'
        finally:
            qt.QApplication.restoreOverrideCursor()



class BlockmatchingLogic(ScriptedLoadableModuleLogic):

    def getNodeFilepath(self, node):
        storageNode = node.GetStorageNode()
        if storageNode is None:
            return None
        else:
            return storageNode.GetFileName()


    def getTempPath(self, directory, ext, length=10, filename=None, dateTime=None):
        if filename is None:
            filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
        filename = filename.replace(' ', '_')  # avoid errors when running a command with spaces
        filename += ext
        if dateTime is not None:
            filename = '{}_{}'.format(dateTime.strftime("%Y%m%d_%H%M%S"), filename)
        return os.path.join(directory, filename)


    def centerViews(self):
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()

        for color in 'Red', 'Yellow', 'Green':
            sliceLogic = slicer.app.layoutManager().sliceWidget(color).sliceLogic()
            sliceLogic.FitSliceToAll()


    def setSlicesBackAndForeground(self, bgVolume=None, fgVolume=None, opacity=None, colors=False, link=True):
        for color in 'Red', 'Yellow', 'Green':
            sliceLogic = slicer.app.layoutManager().sliceWidget(color).sliceLogic()
            compositeNode = sliceLogic.GetSliceCompositeNode()
            if fgVolume:
                compositeNode.SetForegroundVolumeID(fgVolume.GetID())
            if bgVolume:
                compositeNode.SetBackgroundVolumeID(bgVolume.GetID())
            if opacity is not None:
                compositeNode.SetForegroundOpacity(opacity)
            if link:
                compositeNode.SetLinkedControl(True)

        if colors:
            GREEN = 'vtkMRMLColorTableNodeGreen'
            MAGENTA = 'vtkMRMLColorTableNodeMagenta'

            bgImageDisplayNode = slicer.util.getNode(compositeNode.GetBackgroundVolumeID()).GetDisplayNode()
            fgImageDisplayNode = slicer.util.getNode(compositeNode.GetForegroundVolumeID()).GetDisplayNode()

            compositeNode.SetForegroundOpacity(.5)
            bgImageDisplayNode.SetAndObserveColorNodeID(GREEN)
            fgImageDisplayNode.SetAndObserveColorNodeID(MAGENTA)


    def getNumpyMatrixFromVTKMatrix(self, vtkMatrix):
        matrix = np.identity(4, np.float)
        for row in xrange(4):
            for col in xrange(4):
                matrix[row,col] = vtkMatrix.GetElement(row,col)
        return matrix


    def getVTKMatrixFromNumpyMatrix(self, numpyMatrix):
        dimensions = len(numpyMatrix) - 1
        if dimensions == 2:
            vtkMatrix = vtk.vtkMatrix3x3()
        elif dimensions == 3:
            vtkMatrix = vtk.vtkMatrix4x4()
        else:
            raise ValueError('Unknown matrix dimensions.')

        for row in xrange(dimensions + 1):
            for col in xrange(dimensions + 1):
                vtkMatrix.SetElement(row, col, numpyMatrix[row,col])
        return vtkMatrix


    def readBaladinMatrix(self, trsfPath):
        with open(trsfPath) as f:
            lines = f.readlines()
            numbersLines = lines[2:6]
            matrix = np.loadtxt(numbersLines)
            return matrix


    def writeBaladinMatrix(self, transformNode, trsfPath):
        vtkMatrix = vtk.vtkMatrix4x4()
        transformNode.GetMatrixTransformFromParent(vtkMatrix)
        matrix = self.getNumpyMatrixFromVTKMatrix(vtkMatrix)
        lines = []
        lines.append('(')
        lines.append('08')
        for row in matrix:
            line = []
            for n in row:
                line.append('{:13.8f}'.format(n))
            lines.append(''.join(line))
        lines.append(')')
        line = '\n'.join(lines)
        with open(trsfPath, 'w') as f:
            f.write(line)


    def vectorfieldToDisplacementField(self, vectorfieldPath, referenceNode, displacementFieldPath):
        stream = self.getDataStreamFromVectorField(vectorfieldPath)
        referenceImage = su.PullFromSlicer(referenceNode.GetID())
        shape = list(referenceImage.GetSize())
        shape.reverse()

        # Example of 2D shape at this point: [1, 540, 940]

        # Blockmatching output might be 2D
        is2D = shape[0] == 1
        componentsPerVector = 2 if is2D else 3
        shape.append(componentsPerVector)
        reshaped = stream.reshape(shape)

        # Force the output to be 3D
        if is2D:
            zeros = np.zeros_like(reshaped[..., :1])  # z component of the vectors
            reshaped = np.concatenate((reshaped, zeros), axis=3)

        reshaped[..., :2] *= -1  # RAS to LPS
        displacementImage = sitk.GetImageFromArray(reshaped)
        displacementImage.SetOrigin(referenceImage.GetOrigin())
        displacementImage.SetDirection(referenceImage.GetDirection())
        displacementImage.SetSpacing(referenceImage.GetSpacing())

        # TODO: convert the image directly into a transform to save space and time
        sitk.WriteImage(displacementImage, displacementFieldPath)
        transformNode = slicer.util.loadTransform(displacementFieldPath, returnNode=True)[1]
        return transformNode


    def getDataStreamFromVectorField(self, vectorfieldPath):
        HEADER_SIZE = 256
        with open(vectorfieldPath, mode='rb') as f:  # b is important -> binary
            f.seek(HEADER_SIZE)
            imageData = f.read()
        imageData = np.fromstring(imageData, dtype=np.float32)
        return imageData


    def getQFormAndSFormCodes(self, volumeNode):
        reader = vtk.vtkNIFTIImageReader()
        filepath = self.getNodeFilepath(volumeNode)
        reader.SetFileName(filepath)
        reader.Update()
        header = reader.GetNIFTIHeader()
        qform_code = header.GetQFormCode()
        sform_code = header.GetSFormCode()
        return qform_code, sform_code


    def getPyramidShapesMap(self, volumeNode):

        def closestPowerofTwo(n):
            """
            f(513) = 512
            f(512) = 256
            """
            p = np.log(n) / np.log(2)
            if p % 1 == 0:
                result = 2 ** (p-1)
            else:
                result = 2 ** np.floor(p)
            return int(result)

        if volumeNode is None: return None

        imageData = volumeNode.GetImageData()
        shape = list(imageData.GetDimensions())

        level = 0
        shapesMap = {level: shape}

        lastLevel = False
        while not lastLevel:
            oldShape = shapesMap[level]
            maxDim = max(oldShape)
            closestPower = closestPowerofTwo(maxDim)
            newShape = [min(closestPower, n) for n in oldShape]
            level += 1
            shapesMap[level] = newShape

            if max(newShape) == 32:
                lastLevel = True

        return shapesMap


    def hasNiftiExtension(self, path):
        for ext in '.hdr', '.img', '.img.gz', '.nii', '.nii.gz':
            if path.endswith(ext):
                return True
        return False


    def is2D(self, volumeNode):
        if volumeNode is None: return
        imageData = volumeNode.GetImageData()
        if imageData is None: return
        dimensions = imageData.GetDimensions()
        thirdDimension = dimensions[2]
        is2D = thirdDimension == 1
        return is2D

import os
import imp
import time
import shutil
import random
import string
import subprocess
import collections

import numpy as np
import sitkUtils as su
import SimpleITK as sitk
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import sys


# BLOCKMATCHING_PATH = '/home/fernando/git/morpheme-privat/vt/build/bin/blockmatching'
BLOCKMATCHING_PATH = os.path.expanduser('~/bin/blockmatching')
RESULT_NAME = 'Blockmatching result'

TRANSFORMATIONS_MAP = collections.OrderedDict([
                                               ('Rigid', 'rigid'),
                                               ('Similitude', 'similitude'),
                                               ('Affine', 'affine'),
                                               ('Vectorfield', 'vectorfield')
                                              ])


class Blockmatching(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Blockmatching"
        self.parent.categories = ["Registration"]
        self.parent.dependencies = []
        self.parent.contributors = ["Fernando Perez-Garcia (fepegar@gmail.com - Institute of the Brain and Spine - Paris)"]
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
        self.onInputVolumeChanged()
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
        self.inputsCollapsibleButton.text = 'Volumes'
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
        # self.referenceSelector.setToolTip( "Pick the input to the algorithm." )
        self.referenceSelector.currentNodeChanged.connect(self.onInputVolumeChanged)
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
        # self.floatingSelector.setToolTip( "Pick the input to the algorithm." )
        self.floatingSelector.currentNodeChanged.connect(self.onInputVolumeChanged)
        self.inputsLayout.addRow("Floating: ", self.floatingSelector)


        # Initial transform
        self.initialTransformSelector = slicer.qMRMLNodeComboBox()
        self.initialTransformSelector.nodeTypes = ["vtkMRMLTransformNode"]
        self.initialTransformSelector.selectNodeUponCreation = True
        self.initialTransformSelector.addEnabled = False
        self.initialTransformSelector.removeEnabled = True
        self.initialTransformSelector.noneEnabled = True
        self.initialTransformSelector.showHidden = True
        self.initialTransformSelector.showChildNodeTypes = True
        self.initialTransformSelector.setMRMLScene(slicer.mrmlScene)
        self.initialTransformSelector.baseName = 'Initial transform'
        # self.initialTransformSelector.setToolTip( "Pick the input to the algorithm." )
        self.initialTransformSelector.currentNodeChanged.connect(self.onInputVolumeChanged)
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
        # self.resultTransformSelector.baseName = 'Output transform'
        # self.resultTransformSelector.setToolTip( "Pick the input to the algorithm." )
        self.resultTransformSelector.currentNodeChanged.connect(self.onInputVolumeChanged)
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
        self.resultVolumeSelector.baseName = RESULT_NAME
        # self.resultVolumeSelector.setToolTip( "Pick the input to the algorithm." )
        self.resultVolumeSelector.currentNodeChanged.connect(self.onInputVolumeChanged)
        self.outputsLayout.addRow("Result volume: ", self.resultVolumeSelector)


    def makeParametersButton(self):
        self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.parametersCollapsibleButton.text = 'Parameters'
        self.layout.addWidget(self.parametersCollapsibleButton)
        self.parametersLayout = qt.QFormLayout(self.parametersCollapsibleButton)

        self.makeTransformationTypeWidgets()

        self.pyramidHighestSpinBox = qt.QSpinBox()
        self.parametersLayout.addRow('Highest pyramid level:', self.pyramidHighestSpinBox)
        self.pyramidHighestSpinBox.value = 3

        self.pyramidLowestSpinBox = qt.QSpinBox()
        self.parametersLayout.addRow('Lowest pyramid level:', self.pyramidLowestSpinBox)
        self.pyramidLowestSpinBox.value = 2 #0


    def makeTransformationTypeWidgets(self):
        self.trsfTypeGroupBox = qt.QGroupBox()
        self.parametersLayout.addRow('Transformation type:', self.trsfTypeGroupBox)
        trsfTypeLayout = qt.QHBoxLayout(self.trsfTypeGroupBox)

        self.trsfTypeRadioButtons = []
        for t in TRANSFORMATIONS_MAP:
            radioButton = qt.QRadioButton(t)
            radioButton.clicked.connect(self.onTransformationTypeChanged)
            self.trsfTypeRadioButtons.append(radioButton)
            trsfTypeLayout.addWidget(radioButton)

        self.trsfTypeRadioButtons[0].setChecked(True)


    def printCommandLine(self):
        print ' '.join(self.commandLineList)


    def onInputVolumeChanged(self):
        self.readParameters()

        validMinimumInputs = self.referenceVolumeNode and self.floatingVolumeNode and (self.resultVolumeNode or self.resultTransformNode)

        self.applyButton.setEnabled(validMinimumInputs)


    def onTransformationTypeChanged(self):
        trsf = self.getSelectedTransformationType()
        self.resultTransformSelector.baseName = 'Output %s transform' % trsf
        self.resultVolumeSelector.baseName = 'Output %s volume' % trsf


    def getSelectedTransformationType(self):
        for b in self.trsfTypeRadioButtons:
            if b.isChecked():
                trsfType = TRANSFORMATIONS_MAP[str(b.text)]
        return trsfType


    def validateImagesDirections(self):
        same, m1, m2 = self.logic.haveSameDirections(self.referenceVolumeNode, self.floatingVolumeNode)
        if same:
            return True
        else:
            slicer.util.delayDisplay('Images do not have the same orientation')
            print 'Images do not have the same orientation'
            print 'Reference:', m1
            print 'Floating:', m2
            return False


    def validatePyramidLevels(self):
        if self.pyramidHighestSpinBox.value >= self.pyramidLowestSpinBox.value:
            return True
        else:
            slicer.util.delayDisplay('Invalid pyramid values')
            print 'Invalid pyramid values'
            return False


    def readParameters(self):
        self.referenceVolumeNode = self.referenceSelector.currentNode()
        self.floatingVolumeNode = self.floatingSelector.currentNode()
        self.initialTransformNode = self.initialTransformSelector.currentNode()

        self.resultVolumeNode = self.resultVolumeSelector.currentNode()
        self.resultTransformNode = self.resultTransformSelector.currentNode()


    def getCommandLineList(self):
        cmd = [BLOCKMATCHING_PATH]

        self.tempDir = str(slicer.util.tempDirectory())

        self.refPath = self.logic.getNodeFilepath(self.referenceVolumeNode)
        self.floPath = self.logic.getNodeFilepath(self.floatingVolumeNode)

        # We make sure they are in the disk
        if not self.refPath:
            self.refPath = self.logic.getTempPath(self.tempDir, '.nii')
            slicer.util.saveNode(self.referenceVolumeNode, self.refPath)
        if not self.floPath:
            self.floPath = self.logic.getTempPath(self.tempDir, '.nii')
            slicer.util.saveNode(self.floatingVolumeNode, self.floPath)

        # Deprecated, kept for now
        if '.nii' in self.refPath:
            self.resPath = self.logic.getTempPath(self.tempDir, '.nii.gz')
        elif '.hdr' in self.refPath:
            self.resPath = self.logic.getTempPath(self.tempDir, '.hdr')
        self.resultTransformPath = self.logic.getTempPath(self.tempDir, '.trsf')

        # Save the command line for debugging
        self.cmdPath = self.logic.getTempPath(self.tempDir, '.txt')

        trsfType = self.getSelectedTransformationType()

        cmd += ['-ref', self.refPath]
        cmd += ['-flo', self.floPath]
        cmd += ['-res', self.resPath]
        cmd += ['-res-trsf', self.resultTransformPath]
        cmd += ['-py-hl', str(self.pyramidHighestSpinBox.value)]
        cmd += ['-py-ll', str(self.pyramidLowestSpinBox.value)]
        cmd += ['-trsf-type', trsfType]
        cmd += ['-composition-with-initial']
        cmd += ['-command-line', self.cmdPath]

        if self.initialTransformNode:
            self.initialTransformPath = str(self.logic.getTempPath(self.tempDir, '.trsf'))
            self.logic.writeBaladinTransform(self.initialTransformNode, self.initialTransformPath)
            cmd += ['-init-trsf', self.initialTransformPath]

        self.commandLineList = cmd


    def onApply(self):
        self.readParameters()
        self.getCommandLineList()
        self.printCommandLine()
        tIni = time.time()
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            p = subprocess.Popen(self.commandLineList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = p.communicate()
            if p.returncode != 1:
                raise ValueError(output[1])  # is this bad python?
            else:
                tFin = time.time()
                print 'Registration completed in %d seconds.' % (tFin - tIni)
                self.loadResults()
        except OSError as e:
            print e
            print 'Is blockmatching installed?'
        finally:
            qt.QApplication.restoreOverrideCursor()


    def repareResults(self):
        """
        Deprecated
        """

        if '.nii' in self.refPath:
            resultImage = sitk.ReadImage(self.resPath)
            refDirection = self.logic.getDirection(self.referenceVolumeNode)
            refOrigin = list(self.referenceVolumeNode.GetOrigin())

            # LPS (ITK) to RAS (Slicer)
            for i in range(6):
                refDirection[i] *= -1
            for i in range(2):
                refOrigin[i] *= -1

            resultImage.SetDirection(refDirection)
            resultImage.SetOrigin(refOrigin)

            sitk.WriteImage(resultImage, self.resPath)

        elif '.hdr' in self.refPath:
            shutil.copy(self.refPath, self.resPath)


    def loadResults(self):
        if self.resultVolumeNode:
            # Remove result node
            resultName = self.resultVolumeNode.GetName()
            slicer.mrmlScene.RemoveNode(self.resultVolumeNode)

            # Load the new one
            self.resultVolumeNode = slicer.util.loadVolume(self.resPath, returnNode=True)[1]
            self.resultVolumeNode.SetName(resultName)
            self.resultVolumeSelector.setCurrentNode(self.resultVolumeNode)
            fgVolume = self.resultVolumeNode

        # If a transform was given, copy the result in it and apply it to the floating image
        trsfType = self.getSelectedTransformationType()

        if self.resultTransformNode is not None:
            if trsfType is not 'vectorfield':
                matrix = self.logic.readBaladinTransform(self.resultTransformPath)
                vtkMatrix = self.logic.getVTKMatrixFromNumpyMatrix(matrix)

                self.resultTransformNode.SetMatrixTransformFromParent(vtkMatrix)
            else:
                # Remove result transform node
                resultTransformName = self.resultTransformNode.GetName()
                slicer.mrmlScene.RemoveNode(self.resultTransformNode)

                # Load the new one
                self.displacementFieldPath = self.resultTransformPath.replace('.trsf', '.nii')
                self.resultTransformNode = self.logic.vectorfieldToDisplacementField(
                    self.resultTransformPath,
                    self.referenceVolumeNode,
                    self.displacementFieldPath)
                self.resultTransformNode.SetName(resultTransformName)
                self.resultTransformSelector.setCurrentNode(self.resultTransformNode)

                # For debugging
                self.resultDisplacementFieldVolumeNode = slicer.util.loadVolume(self.displacementFieldPath, returnNode=True)[1]
                self.resultDisplacementFieldVolumeNode.SetName(resultTransformName)

            self.floatingVolumeNode.SetAndObserveTransformNodeID(self.resultTransformNode.GetID())
            fgVolume = self.floatingVolumeNode

        self.logic.setSlicesBackAndForeground(
            bgVolume=self.referenceVolumeNode,
            fgVolume=fgVolume,
            opacity=0.5,
            colors=True)

        self.logic.centerViews()



class BlockmatchingLogic(ScriptedLoadableModuleLogic):

    def getNodeFilepath(self, node):
        storageNode = node.GetStorageNode()
        return storageNode.GetFileName()


    def getDirections(self, node):
        d = [3*[0] for x in xrange(3)]
        node.GetIJKToRASDirections(d)
        return np.array(d)  # 3x3


    def getDirection(self, node):
        ds = self.getDirections(node)
        d = [n for sublist in ds for n in sublist]  # http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
        return d


    def getTempPath(self, directory, ext):
        filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)) + ext
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


    def haveSameDirections(self, volumeNode1, volumeNode2):
        m1, m2 = np.zeros((2,3,3))
        volumeNode1.GetIJKToRASDirections(m1)
        volumeNode2.GetIJKToRASDirections(m2)
        return np.array_equal(m1, m2), m1, m2


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


    def readBaladinTransform(self, trsfPath):
        with open(trsfPath, 'r') as f:
            firstLine = f.readline()

        vectorfield = 'INRIMAGE' in firstLine

        if vectorfield:
            pass  # TODO
        else:
            with open(trsfPath) as f:
                lines = f.readlines()
                numbersLines = lines[2:6]
                matrix = np.loadtxt(numbersLines)
                return matrix


    def writeBaladinTransform(self, transformNode, trsfPath):
        vtkMatrix = vtk.vtkMatrix4x4()
        transformNode.GetMatrixTransformFromParent(vtkMatrix)
        matrix = self.getNumpyMatrixFromVTKMatrix(vtkMatrix)
        lines = []
        lines.append('(')
        lines.append('08')
        for i in range(4):
            lines.append(' '.join(map(str, matrix[i])))
        lines.append(')')
        line = '\n'.join(lines)
        with open(trsfPath, 'w') as f:
            f.write(line)


    def vectorfieldToDisplacementField(self, vectorfieldPath, referenceNode, displacementFieldPath):
        stream = self.getDataStreamFromVectorField(vectorfieldPath)
        referenceImage = su.PullFromSlicer(referenceNode.GetID())
        shape = list(referenceImage.GetSize())
        shape.reverse()
        shape.append(3)
        reshaped = stream.reshape(shape)
        reshaped[..., :2] *= -1  # RAS to LPS
        displacementImage = sitk.GetImageFromArray(reshaped)
        displacementImage.SetOrigin(referenceImage.GetOrigin())
        displacementImage.SetDirection(referenceImage.GetDirection())
        displacementImage.SetSpacing(referenceImage.GetSpacing())

        # Temporary, it would be better to convert the image directly
        # into a transform to save space and time
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

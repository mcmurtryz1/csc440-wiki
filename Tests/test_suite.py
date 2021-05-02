"""test_suite.py"""

import pathlib
import shutil
import unittest
from os.path import exists

from wiki.web.routes import *
from wiki.core import *
from flask_testing import *

TESTFILES = ['testdata.txt', 'testdata1.txt',
             'testdata3.txt', 'upload2/testdata2.txt']


class IndexUploads(unittest.TestCase):

    def testIndexUploads(self):
        uploads = Wiki.indexUploads(self)
        for idx, upload in enumerate(uploads):
            assert upload == TESTFILES[idx]


class DeleteUpload(unittest.TestCase):
    def setUp(self):
        # add file
        self.file = open("delete.txt", "w+")

    def testDeleteUpload(self):
        # delete upload
        filePath = path.join(getcwd(), self.file.name)
        Wiki.deleteUpload(self, filePath)

        assert not exists('delete.txt')

    def tearDown(self) -> None:
        self.file.close()

class ClearEmptyDirectories(unittest.TestCase):

    def testClearLayeredDirectory(self):
        # test clearEmptyDirectories with multiple folders
        delete1 = path.join(getcwd(), 'upload', 'delete1')
        os.mkdir(delete1)
        deletePath = path.join(delete1, 'delete2')
        os.mkdir(deletePath)
        clearEmptyDirectories()
        assert not exists(delete1)
        assert not exists(deletePath)

    def testClearEmptySingleDirectories(self):
        # test clearEmptyDirectories with one folder
        deletePath = path.join(getcwd(), 'upload', 'delete')
        os.mkdir(deletePath)
        clearEmptyDirectories()
        assert not exists(deletePath)

    def testClearNonEmptyDirectory(self):
        # test clearEmptyDirectories when a directory contains a file
        # directories should not be deleted
        uploadPath = path.join(getcwd(), 'upload')
        upload2Path = path.join(getcwd(), 'upload')
        clearEmptyDirectories()
        assert exists(uploadPath)
        assert exists(upload2Path)


def suite(self):
    suite.addTest(unittest.makeSuite(IndexUploads))
    suite.addTest(unittest.makeSuite(DeleteUpload))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

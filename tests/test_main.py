#!/usr/bin/env python3


from pyfyzz.analyzer import PythonPackageAnalyzer
from pyfyzz.logger import PyFyzzLogger

logger = PyFyzzLogger()


class TestPyFyzz:
    def test_verify_importable_package(self):
        analyzer = PythonPackageAnalyzer(logger=logger)

        assert analyzer.verify_importable_package(pkg_name="os") == True
        assert (
            analyzer.verify_importable_package(pkg_name="non_existent_module") == False
        )

    def test_list_package_contents(self):
        analyzer = PythonPackageAnalyzer(logger=logger)

        import os
        package_info = analyzer.enumerate_package_contents("os", os)

        assert package_info.name == "os"
        assert len(package_info.modules) > 0

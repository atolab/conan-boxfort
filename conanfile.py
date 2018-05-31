#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class BoxFortConan(ConanFile):
    name = "boxfort"
    version = "05312018"
    description = "Convenient & cross-platform sandboxing C library"
    url = "https://github.com/k0ekk0ek/conan-boxfort"
    homepage = "https://github.com/diacritic/BoxFort"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_qemu": [True, False],
        "arena_reopen_shm": [True, False],
        "arena_file_backed": [True, False],
        "samples": [True, False],
        "tests": [True, False],
        "fork_resilience": [True, False]
    }
    default_options = (
        "shared=False",
        "fPIC=True",
        "use_qemu=False",
        "arena_reopen_shm=False",
        "arena_file_backed=False",
        "samples=False",
        "tests=False",
        "fork_resilience=True"
    )
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    branch = "master"
    commit = "4bac60bf13a49eadb76f55343164cbe8199b8d66"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        self.run("git clone --branch={0} {1}.git {2}"
            .format(self.branch, self.homepage, self.source_subfolder))
        self.run("git -C {0} checkout {1}"
            .format(self.source_subfolder, self.commit))

    def configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['USE_QEMU'] = self.options.use_qemu
        cmake.definitions['BXF_STATIC_LIB'] = self.options.shared == False
        cmake.definitions['BXF_SAMPLES'] = self.options.samples
        cmake.definitions['BXF_TESTS'] = self.options.tests
        cmake.definitions['BXF_FORK_RESILIENCE'] = self.options.fork_resilience
        if self.settings.os != 'Windows':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
            cmake.definitions['BXF_ARENA_REOPEN_SHM'] = self.options.arena_reopen_shm
            cmake.definitions['BXF_ARENA_FILE_BACKED'] = self.options.arena_file_backed
        cmake.configure(build_folder=self.build_subfolder)
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self.source_subfolder)
        cmake = self.configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)


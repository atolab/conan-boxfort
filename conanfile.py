#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import re


class BoxFortConan(ConanFile):
    name = "boxfort"
    version = "12122016"
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

    # Version used by Criterion 2.3.2
    branch = "master"
    commit = "7ed0cf2120926935bfd1b24e3fdfd63d70b1999c"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.arena_reopen_shm
            del self.options.arena_file_backed

    def source(self):
        self.run("git clone --branch={0} {1}.git {2}"
            .format(self.branch, self.homepage, self.source_subfolder))
        self.run("git -C {0} checkout {1}"
            .format(self.source_subfolder, self.commit))

    def configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['USE_QEMU'] = self.options.use_qemu
        cmake.definitions['BXF_STATIC_LIB'] = not self.options.shared
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
        # The BoxFort CMake files use CMAKE_SYSTEM_PROCESSOR to decide which
        # trampoline-x.S file should be added to the sources. This is a problem
        # on systems that cross-compile for a different architecture. E.g. the
        # Docker images used by the automatic builds are still 64-bit, but
        # build for 32-bit.
        build_arch = self.settings.get_safe('arch_build') or tools.detected_architecture()
        target_arch = self.settings.get_safe('target_arch') or self.settings.get_safe('arch')
        if (build_arch != target_arch and
            not (os.getenv('CONAN_CMAKE_SYSTEM_PROCESSOR', False)) or
                 os.getenv('CMAKE_SYSTEM_PROCESSOR', False)):
            path = '{0}/CMakeLists.txt'.format(self.source_subfolder)
            search = 'set (_ARCH "${CMAKE_SYSTEM_PROCESSOR}")'
            replace = 'set (_ARCH "{0}")'.format(target_arch)
            tools.replace_in_file(path, search, replace)

        cmake = self.configure_cmake()
        cmake.build()
        # Whether or not the package consumer should link against rt (only
        # applicable to static builds), depends on whether or not
        # CMakeLists.txt sets HAVE_LIBRT.
        if not self.options.shared and self.settings.os == 'Linux':
            build_folder = "{0}/{1}".format(self.build_folder, self.build_subfolder)
            have_librt_re = re.compile('^HAVE_(SHM|[A-Z_]+_RT):INTERNAL=1$')
            have_librt = False
            with open("{0}/CMakeCache.txt".format(build_folder)) as f:
                for line in f:
                    if have_librt_re.match(line):
                        have_librt = True
                        break
            if have_librt:
                with open("{0}/static.dependencies".format(build_folder), "w") as f:
                    f.write("pthread\n")
                    f.write("rt\n")

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self.source_subfolder)
        build_folder = "{0}/{1}".format(self.build_folder, self.build_subfolder)
        self.copy(pattern="static.dependencies", dst="lib", src=build_folder)
        cmake = self.configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if not self.options.shared and self.settings.os == 'Linux':
            with open("{0}/lib/{1}".format(self.package_folder, "static.dependencies")) as f:
                for line in f:
                    self.cpp_info.libs.append(line)
        if not self.options.shared and self.settings.os == 'Windows':
            # Pass BXF_STATIC_LIB for static builds on Windows otherwise the
            # boxfort.h file will define BXF_API to __declspec(...) causing a
            # linker error.
            self.cpp_info.defines.append('BXF_STATIC_LIB')


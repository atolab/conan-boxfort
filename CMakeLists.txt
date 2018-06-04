cmake_minimum_required(VERSION 2.8.11)
project(cmake_wrapper)

include(conanbuildinfo.cmake)
conan_basic_setup()

set(CMAKE_ASM_FLAGS ${CMAKE_C_FLAGS})

add_subdirectory("source_subfolder")

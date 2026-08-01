include(CMakeFindDependencyMacro)

# Add this directory to the end of the module search path in order to leverage
# Legion's installed Find* modules
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

# GASNet is a private dependency and only needs to be pulled in for static
# builds
set(Legion_NETWORKS gasnetex)
set(Legion_EMBED_GASNet OFF)
if("gasnetex" MATCHES ".*gasnet(1|ex).*")
  if (Legion_EMBED_GASNet AND NOT DEFINED GASNet_ROOT_DIR)
    if (DEFINED Legion_ROOT)
      set(GASNet_ROOT_DIR ${Legion_ROOT})
    endif()
  endif()
  find_package(GASNet REQUIRED)
endif()

# LLVM is a private dependency and only needs to be pulled in for static
# builds
set(Legion_USE_LLVM OFF)
if((NOT OFF) AND Legion_USE_LLVM)
  set(Legion_LLVM_COMPONENTS )
  set(LLVM_CONFIG_EXECUTABLE )
  find_package(LLVM REQUIRED COMPONENTS ${Legion_LLVM_COMPONENTS})
endif()

# Find the CUDA Toolkit here
set(Legion_USE_CUDA ON)
if(Legion_USE_CUDA)
  set(Legion_CUDA_ARCH 80)
  set(CMAKE_CUDA_RUNTIME_LIBRARY "STATIC")
  find_package(CUDAToolkit REQUIRED)
  if("${CUDA_cuda_driver_LIBRARY}" MATCHES ".*stubs.*")
    get_filename_component(_cuda_stubs_path "${CUDA_cuda_driver_LIBRARY}" DIRECTORY)
    list(APPEND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${_cuda_stubs_path}")
    unset(_cuda_stubs_path)
  endif()
endif()

find_dependency(Realm)

include(${CMAKE_CURRENT_LIST_DIR}/LegionTargets.cmake)

# HIP is only a private dependency of Legion but has a few usage requirements
# so we add it in here
set(Legion_USE_HIP OFF)
if(Legion_USE_HIP)
  set(Legion_HIP_TARGET ROCM)
  find_package(HIP REQUIRED)
endif()

if(Legion_USE_HIP AND Legion_HIP_TARGET STREQUAL "ROCM" AND NOT Legion_HIP_HIPCC_FLAGS_SET)
  # flags
  set(HIP_HIPCC_FLAGS "${HIP_HIPCC_FLAGS}  ")

  # Make sure we don't get duplicates
  set(Legion_HIP_HIPCC_FLAGS_SET ON)
endif()

# HWLOC is a private dependency and only needs to be pulled in for static
# builds
set(Legion_USE_HWLOC OFF)
if((NOT OFF) AND Legion_USE_HWLOC)
  set(HWLOC_INCLUDE_DIR )
  set(HWLOC_LIBRARY )
  find_package(HWLOC REQUIRED)
endif()

# ZLIB is a private dependency and only needs to be pulled in for static
# builds
set(Legion_USE_ZLIB ON)
if((NOT OFF) AND Legion_USE_ZLIB)
  set(ZLIB_INCLUDE_DIRS /usr/include)
  set(ZLIB_LIBRARIES /usr/lib64/libz.so)
  find_package(ZLIB REQUIRED)
endif()

# OpenMP is an internal dependency, only needed so that users can key off of it
set(Legion_USE_OpenMP ON)

# Python is an internal dependency, only needed so that users can key off of it
set(Legion_USE_Python OFF)

# bring in Kokkos if needed
set(Legion_USE_Kokkos OFF)
if(Legion_USE_Kokkos)
  find_package(Kokkos REQUIRED OPTIONAL_COMPONENTS separable_compilation)

  # in order to build using Kokkos' exported compile options, we need to use
  #  the same compiler - newer versions of Kokkos will tell us, but for older
  #  versions, we need it from the configuration or the environment
  if(Kokkos_CXX_COMPILER)
    set(KOKKOS_CXX_COMPILER ${Kokkos_CXX_COMPILER})
  elseif(DEFINED ENV{KOKKOS_CXX_COMPILER})
    set(KOKKOS_CXX_COMPILER $ENV{KOKKOS_CXX_COMPILER})
  endif()
  if(NOT KOKKOS_CXX_COMPILER)
    message(FATAL_ERROR "to build correctly with Kokkos, the exact compiler used in the Kokkos build (typically set via CXX=... or -DCMAKE_CXX_COMPILER=...) must be provided in KOKKOS_CXX_COMPILER (either on the command line or from the environment)")
  endif()
endif()

# task registration across nodes often relies on being able to map function
#  pointers back to symbol names, so ask cmake to export symbols in binaries
set(CMAKE_ENABLE_EXPORTS ON)

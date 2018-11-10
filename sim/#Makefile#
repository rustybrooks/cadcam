SUFFIXES += .d

CFLAGS=-D__LOCALBUILD

STATIC_LIBS=
LIBS=

CFLAGS+=-DAA -DBB -DCC
CFLAGS+=-Wall


# glfw
CFLAGS+=-I ../../../lib/glfw/glfw-3.1.1/include

# glew
#STATIC_LIBS += ../../../lib/glew/glew-1.10.0/lib/libGLEW.a
CFLAGS+=-I ../../../lib/glew/glew-1.10.0/include
CFLAGS+=-I ../../../lib/glew/glew-1.10.0/src
CFLAGS += -DGLEW_STATIC

# soil
CFLAGS+=-I ../../../lib/soil/SOIL/src
#STATIC_LIBS += ../../../lib/soil/SOIL/lib/libSOIL.a
#CFLAGS += ../../../lib/soil/SOIL/src/

CFLAGS+=-I ../../../lib/assimp/assimp-3.1.1/include
CFLAGS+=-I ../../../lib/mygl

# boost
BOOST_VERSION=1_58_0
CFLAGS+=-I ../../../lib/boost/boost_$(BOOST_VERSION)/installed/include/
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_program_options.a
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_thread.a
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_system.a
STATIC_LIBS += ../../../lib/assimp/assimp-3.1.1/build/installed/lib/libassimp.a
# gason
#CFLAGS+=-I ../../../lib/gason/src
#STATIC_LIBS += ../../../lib/gason/libgason.a

# cpptk
CFLAGS += -I ../../../lib/tcltk/installed/include/
CFLAGS += -I ../../../lib/cpptk/cpptk-1.0.2/

ifeq ($(OS), Windows_NT)
	CC=gcc
	LINK=$(CC)
	CFLAGS+= -static
	LDFLAGS+= -static 
	CFLAGS += -std=c++11

	CFLAGS += -Wno-write-strings -Wno-strict-aliasing -Wno-unused-variable -Wno-deprecated-declarations
	CFLAGS += -Wno-parentheses

	# otherwise we get complaints about %lu and size_t, FU windows
	CFLAGS += -Wno-format

	# not sure if I need these
	CFLAGS+=-march=x86-64
	LDLAGS+=-march=x86-64
	CFLAGS += -m64
	LDFLAGS += -m64

#	CFLAGS += -DSTATIC_BUILD

        LIBS += -lglu32 -lopengl32 -lgdi32 -lstdc++
	LIBS += -lcomdlg32 -limm32 -lcomctl32 -lshell32 -luuid -lole32 -loleaut32
	LIBS += -lWs2_32

#	CFLAGS+=-I ../../../lib/assimp/assimp-3.1.1-win-binaries/include/
#	LIBS+="../../../lib/assimp/assimp-3.1.1-win-binaries/lib64/assimp.lib"

	STATIC_LIBS += ../../../lib/glfw/glfw-3.1.1.bin.WIN64/lib-mingw/libglfw3.a

#	for windows only, we're going to try the shared lib route
	STATIC_LIBS += ../../../lib/tcltk/installed/lib/libtclstub85.a ../../../lib/tcltk/installed/lib/libtcl85.a
	STATIC_LIBS += ../../../lib/tcltk/installed/lib/libtkstub85.a ../../../lib/tcltk/installed/lib/libtk85.a


else
	STATIC_LIBS += ../../../lib/tcltk/installed/lib/libtcl8.5.a
	STATIC_LIBS += ../../../lib/tcltk/installed/lib/libtk8.5.a

	LINK=$(CC)

        STATIC_LIBS += ../../../lib/glfw/glfw-3.1.1/build/installed/lib/libglfw3.a

	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		CC=g++
		CFLAGS += -std=c++11
		LDFLAGS += -L/usr/X11/lib -L/usr/lib/i386-linux-gnu/
		#LDFLAGS += -L/usr/local/lib

		CFLAGS += -Wno-write-strings 
#-Wno-parenthesis

		LIBS+=-lGL -lGLU -lX11 -lXrandr -lXi -lXxf86vm -lXinerama -lXcursor -lpthread -ldl -lXft -lfontconfig -lXss
#		LIBS += -lassimp


	endif

	ifeq ($(UNAME_S),Darwin)
		CC=g++
		CLANG_CXX_LANGUAGE_STANDARD = gnu++11
		LDFLAGS+= -stdlib=libc++
		CFLAGS+=-std=c++11 -stdlib=libc++

		CFLAGS += -Wno-deprecated-declarations
		CFLAGS += -Wno-deprecated-writable-strings -Wno-writable-strings
		CFLAGS += -Wno-unused-private-field
		CFLAGS += -I/opt/X11/include/

		LIBS += -lz
		LIBS += -framework openGL -framework Cocoa 
		LIBS += -framework IOKit 
		LIBS += -framework CoreVideo
		LIBS += -framework Carbon

#		LIBS += -lassimp
	endif


endif

SOURCES1=sim.cpp
SOURCES1+=mymath.cpp
SOURCES1+=path.cpp
SOURCES1+=rs274ngc_pre.cpp
SOURCES1+=canon.cpp
SOURCES1+=interface.cpp
SOURCES1+=grid_volume.cpp
SOURCES1+=../../../lib/mygl/log.cpp
SOURCES1+=../../../lib/mygl/math_funcs.cpp 
SOURCES1a+=../../../lib/cpptk/cpptk-1.0.2/cpptk.cc
SOURCES1a+=../../../lib/cpptk/cpptk-1.0.2/base/cpptkbase.cc

EXECUTABLE=sim 

#CFLAGS += -ggdb -O0
#CFLAGS += -O
#CFLAGS += -O2
CFLAGS += -O3

OBJECTS1=$(SOURCES1:.cpp=.o) $(SOURCES1a:.cc=.o)

#These are the dependency files, which make will clean up after it creates them
DEPFILES=$(SOURCES1:.cpp=.d) 

all: $(EXECUTABLE) 

clean:
	rm -f *.o *.obj *.d $(EXECUTABLE) 

-include $(DEPFILES)

sim: $(OBJECTS1) 
	$(LINK) $(LDFLAGS) $(OBJECTS1) $(STATIC_LIBS) $(LIBS) -o $@


#This is the rule for creating the dependency files
%.d: %.cpp
	$(CC) $(CFLAGS) -MM -MT '$(patsubst src/%,obj/%,$(patsubst %.cpp,%.o,$<))' $< > $@


%.o: %.cpp %.h
	$(CC) $(CFLAGS) -c $< -o $@

%.d: %.cc
	$(CC) $(CFLAGS) -MM -MT '$(patsubst src/%,obj/%,$(patsubst %.cpp,%.o,$<))' $< > $@


%.o: %.cc %.h
	$(CC) $(CFLAGS) -c $< -o $@




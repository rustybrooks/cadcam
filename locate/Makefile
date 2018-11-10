SUFFIXES += .d

CFLAGS=-Wall 

STATIC_LIBS=
LIBS=

LDFLAGS=

SOURCES=locate.cpp

CFLAGS += -I/usr/local/include -I /usr/X11/include 
CC=g++

LIBS=
LIBS += -L/usr/local/lib 

# opencv
LIBS += -lopencv_core -lopencv_imgproc -lopencv_highgui -lopencv_video -lopencv_videoio

# boost
BOOST_VERSION=1_58_0
CFLAGS+=-I ../../../lib/boost/boost_$(BOOST_VERSION)/installed/include/
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_program_options.a
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_thread.a
STATIC_LIBS += ../../../lib/boost/boost_$(BOOST_VERSION)/installed/lib/libboost_system.a



ifeq ($(OS), Windows_NT)
	CC=gcc
	LINK=$(CC)
	LDFLAGS+= -static 
	CFLAGS += -std=c++11

	CFLAGS += -Wno-write-strings -Wno-strict-aliasing -Wno-unused-variable -Wno-deprecated-declarations

	CFLAGS += -I e:/dev/opencv/build/include
	LDFLAGS += -L e:/dev/opencv/build/lib

	# otherwise we get complaints about %lu and size_t, FU windows
	CFLAGS += -Wno-format
else
	LINK=$(CC)

	UNAME_S := $(shell uname -s)
    	ifeq ($(UNAME_S),Linux)
		CC=g++
		CFLAGS += -std=c++11
		LDFLAGS += -L/usr/X11/lib -L/usr/lib/i386-linux-gnu/

		CFLAGS += -Wno-write-strings
	endif

	ifeq ($(UNAME_S),Darwin)
		CC=clang++
        	CLANG_CXX_LANGUAGE_STANDARD = gnu++11
        	LDFLAGS+= -stdlib=libc++
 		CFLAGS+=-std=c++11 -stdlib=libc++

		CFLAGS += -Wno-deprecated-declarations
		CFLAGS += -Wno-deprecated-writable-strings -Wno-writable-strings

        	LIBS += -framework openGL -framework Cocoa 
		LIBS += -framework IOKit 
		LIBS += -framework CoreVideo
		LIBS += -framework Carbon
    	endif


endif


EXECUTABLE=locate
LINK=$(CC)

#CFLAGS += -g
#CFLAGS += -O
CFLAGS += -O2
#CFLAGS += -O3

OBJECTS=$(SOURCES:.cpp=.o)	

#These are the dependency files, which make will clean up after it creates them
DEPFILES=$(SOURCES:.cpp=.d)

all: locate

clean:
	rm -f *.o *.obj *.d $(EXECUTABLE) 

-include $(DEPFILES)

locate: $(OBJECTS) 
	$(LINK) $(LDFLAGS) $(OBJECTS) $(STATIC_LIBS) $(LIBS) -o $@


#This is the rule for creating the dependency files
%.d: %.cpp
	$(CC) $(CFLAGS) -MM -MT '$(patsubst src/%,obj/%,$(patsubst %.cpp,%.o,$<))' $< > $@


# %.d
%.o: %.cpp %.h
	$(CC) $(CFLAGS) -c $< -o $@



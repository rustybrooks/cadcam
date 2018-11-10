// copied from dktd, not sure if works yet
#include <GL/glew.h>
//#include <glew.c>
#include <GLFW/glfw3.h>

#if defined _WIN32
#include "windows.h"
#include <gl/glu.h>
//#include <gl/glut.h>
#elif defined __gnu_linux__
#include <GL/gl.h>
//#include <GL/glut.h>
#else
#include <OpenGL/OpenGL.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#include "AGL/agl.h"
//#include <GLUT/glut.h>
#endif


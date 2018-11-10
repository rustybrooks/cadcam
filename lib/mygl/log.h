// Maybe it's dumb to have all the code as a header file.  It definitely simplifies things, though, so...

#pragma once

#include "mygl.h"

#include <stdio.h>
#include <time.h>
#include <stdarg.h> 

#define GL_LOG_FILE "gl.log"



#define gldebug(x) gl_log(__FILE__, __LINE__, "%s", x); 

#ifdef _WIN32
#define gldebugf(x, ...) gl_log(__FILE__, __LINE__, x, __VA_ARGS__); 
#else
#define gldebugf(x, args...) gl_log(__FILE__, __LINE__, x, ## args); 
#endif


// make this more errory later
#define xerror(x) gl_log(__FILE__, __LINE__, "%s", x); 

#ifdef _WIN32
#define errorf(x, ...) gl_log(__FILE__, __LINE__, x, __VA_ARGS__); 
#else
#define errorf(x, args...) gl_log(__FILE__, __LINE__, x, ## args); 
#endif

extern GLFWwindow* g_window;

bool start_gl(int gl_width, int gl_height);
void glfw_error_callback (int error, const char* description);
//extern void glfw_window_size_callback (GLFWwindow* window, int width, int height);
void _update_fps_counter (GLFWwindow* window);
bool restart_gl_log ();
bool gl_log(const char* filename, int line, const char* format, ...);
void log_gl_params ();
const char* GL_type_to_string (unsigned int type);

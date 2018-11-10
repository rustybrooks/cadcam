#include "log.h"

#include <stdio.h>
#include <time.h>
#include <string.h>
#include <assert.h>

#include <boost/unordered_map.hpp>

GLFWwindow* g_window;

boost::unordered_map<int, bool> gl_keyStates;
boost::unordered_map<int, bool> gl_mouseStates;

void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods) {
//    if (key == GLFW_KEY_E && action == GLFW_PRESS)
    gl_keyStates[key] = (action == GLFW_PRESS or action == GLFW_REPEAT);
}

void mouse_button_callback(GLFWwindow* window, int button, int action, int mods) {
    gl_mouseStates[button] = (action == GLFW_PRESS);
}

static void cursor_position_callback(GLFWwindow* window, double xpos, double ypos) {
}

/*--------------------------------GLFW3 and GLEW------------------------------*/
bool start_gl(int gl_width, int gl_height) {
    gldebugf("starting GLFW %s", glfwGetVersionString ());
    
    glfwSetErrorCallback (glfw_error_callback);
    if (!glfwInit()) {
        fprintf (stderr, "ERROR: could not start GLFW3\n");
        return false;
    }
    
    /* We must specify 3.2 core if on Apple OS X -- other O/S can specify
       anything here. I defined 'APPLE' in the makefile for OS X */
#ifdef __APPLE__
    glfwWindowHint (GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint (GLFW_CONTEXT_VERSION_MINOR, 1);
    glfwWindowHint (GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
    glfwWindowHint (GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#else
    glfwWindowHint (GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint (GLFW_CONTEXT_VERSION_MINOR, 3);
#endif

    
    /*GLFWmonitor* mon = glfwGetPrimaryMonitor ();
      const GLFWvidmode* vmode = glfwGetVideoMode (mon);
      g_window = glfwCreateWindow (
      vmode->width, vmode->height, "Extended GL Init", mon, NULL
      );*/
    
    gldebugf("Creating window %dx%d", gl_width, gl_height);
    g_window = glfwCreateWindow (
        gl_width, gl_height, "Extended Init.", NULL, NULL
	);
    if (!g_window) {
        fprintf (stderr, "ERROR: could not open window with GLFW3\n");
        glfwTerminate();
        return false;
    }
    glfwMakeContextCurrent(g_window);
    glfwSetInputMode(g_window, GLFW_CURSOR, GLFW_CURSOR_HIDDEN);
    
    glfwWindowHint(GLFW_SAMPLES, 4);
    
    glfwSetKeyCallback(g_window, key_callback);
    glfwSetMouseButtonCallback(g_window, mouse_button_callback);
    glfwSetCursorPosCallback(g_window, cursor_position_callback);

    // start GLEW extension handler
    glewExperimental = GL_TRUE;
    glewInit();
    
    // get version info
    const GLubyte* renderer = glGetString(GL_RENDERER); // get renderer string
    const GLubyte* version = glGetString(GL_VERSION); // version as a string
    printf ("OpenGL version supported %s\n", version);
    printf ("Renderer: %s\n", renderer);
	
    return true;
}

void glfw_error_callback (int error, const char* description) {
	fputs (description, stderr);
	errorf("%s\n", description);
}

// a call-back function
/*
void glfw_window_size_callback (GLFWwindow* window, int width, int height) {
	gl_width = width;
	gl_height = height;
	fprintf (stderr, "width=%i, height=%i\n", width, height);
}
*/

void _update_fps_counter (GLFWwindow* window) {
	static double previous_seconds = glfwGetTime();
	static int frame_count;
	double current_seconds = glfwGetTime ();
	double elapsed_seconds = current_seconds - previous_seconds;
	if (elapsed_seconds > 1) {
		previous_seconds = current_seconds;
		double fps = (double)frame_count / elapsed_seconds;
		char tmp[128];
		 sprintf (tmp, "opengl @ fps: %.2f", fps);
		 glfwSetWindowTitle (window, tmp);
		 frame_count = 0;
	}
	frame_count++;
}

bool restart_gl_log () {
  FILE* file = fopen (GL_LOG_FILE, "w+");
  if (!file) {
    fprintf (stderr, "ERROR: could not open %s log file for writing\n", GL_LOG_FILE);
    return false;
  }
  time_t now = time (NULL);
  char* date = ctime (&now);
  fprintf (file, "%s log. local time %s\n", GL_LOG_FILE, date);
  fclose (file);
  return true;
}

bool gl_log(const char* filename, int line, const char* format, ...) {
  FILE* file = fopen (GL_LOG_FILE, "a+");
  if (!file) {
    fprintf (stderr, "ERROR: could not open %s for writing\n", GL_LOG_FILE);
    return false;
  }

  va_list argptr;
  va_start(argptr, format);
  fprintf (file, "%s:%i ", filename, line);
  vfprintf(file, format, argptr);
  va_end(argptr);
  fprintf (file, "\n");

  fclose (file);
  return true;
}

void log_gl_params () {
    GLenum params[] = {
        GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
        GL_MAX_CUBE_MAP_TEXTURE_SIZE,
        GL_MAX_DRAW_BUFFERS,
        GL_MAX_FRAGMENT_UNIFORM_COMPONENTS,
        GL_MAX_TEXTURE_IMAGE_UNITS,
        GL_MAX_TEXTURE_SIZE,
        GL_MAX_VARYING_FLOATS,
        GL_MAX_VERTEX_ATTRIBS,
        GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS,
        GL_MAX_VERTEX_UNIFORM_COMPONENTS,
        GL_MAX_VIEWPORT_DIMS,
        GL_STEREO,
    };
    const char* names[] = {
        "GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
        "GL_MAX_CUBE_MAP_TEXTURE_SIZE",
        "GL_MAX_DRAW_BUFFERS",
        "GL_MAX_FRAGMENT_UNIFORM_COMPONENTS",
        "GL_MAX_TEXTURE_IMAGE_UNITS",
        "GL_MAX_TEXTURE_SIZE",
        "GL_MAX_VARYING_FLOATS",
        "GL_MAX_VERTEX_ATTRIBS",
        "GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
        "GL_MAX_VERTEX_UNIFORM_COMPONENTS",
        "GL_MAX_VIEWPORT_DIMS",
        "GL_STEREO",
    };
    gldebug("GL Context Params:");
    // integers - only works if the order is 0-10 integer return types
    for (int i = 0; i < 10; i++) {
        int v = 0;
        glGetIntegerv (params[i], &v);
        gldebugf("%s %i", names[i], v);
    }
    // others
    int v[2];
    v[0] = v[1] = 0;
    glGetIntegerv (params[10], v);
    gldebugf("%s %i %i", names[10], v[0], v[1]);
    unsigned char s = 0;
    glGetBooleanv (params[11], &s);
    gldebugf("%s %i", names[11], (unsigned int)s);
    gldebug("-----------------------------");
}

const char* GL_type_to_string (unsigned int type) {
  if (GL_FLOAT == type) {
    return "GL_FLOAT";
  }
  if (GL_FLOAT_VEC2 == type) {
    return "GL_FLOAT_VEC2";
  }
  if (GL_FLOAT_VEC3 == type) {
    return "GL_FLOAT_VEC3";
  }
  if (GL_FLOAT_VEC4 == type) {
    return "GL_FLOAT_VEC4";
  }
  if (GL_FLOAT_MAT2 == type) {
    return "GL_FLOAT_MAT2";
  }
  if (GL_FLOAT_MAT3 == type) {
    return "GL_FLOAT_MAT3";
  }
  if ( GL_FLOAT_MAT4 == type) {
    return "GL_FLOAT_MAT4";
  }
  if (GL_INT == type) {
    return "GL_INT";
  }
  if (GL_BOOL == type) {
    return "GL_BOOL";
  }
  if (GL_SAMPLER_2D == type) {
    return "GL_SAMPLER_2D";
  }
  if (GL_SAMPLER_3D == type) {
    return "GL_SAMPLER_3D";
  }
  if (GL_SAMPLER_CUBE == type) {
    return "GL_SAMPLER_CUBE";
  }
  if (GL_SAMPLER_2D_SHADOW == type) {
    return "GL_SAMPLER_2D_SHADOW";
  }
  return "OTHER";
}

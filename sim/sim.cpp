#ifdef __LOCALBUILD
#include <glew.c>
#endif

#include <GL/glew.h>

#include "sim.h"

#include "background.h"
#include "canon.h"
#include "drawings.h"
#include "interface.h"
#include "mygl.h"
#include "mymath.h"
#include "shader.h"
//#include "sim_time.h"

#include <iostream>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <vector>

#include <boost/program_options.hpp>
#include <boost/thread/thread.hpp>
#include <boost/thread/mutex.hpp>

#include <tcl.h>
#include <tk.h>

namespace po = boost::program_options;

Camera camera(1280, 1024, 35.0);
void glfw_window_size_callback (GLFWwindow* window, int width, int height) {
	fprintf (stderr, "width=%i, height=%i\n", width, height);
    //    camera.set_dimensions(width, height);
}


// uh, do something here to signal exit
void safe_exit() {
    fprintf(stderr, "Starting to exit\n");
    exit(0);
}

int main(int argc, char **argv) {
    putenv("TCL_LIBRARY=./lib/tcl8.5");

    po::options_description desc("Allowed options");
    desc.add_options()
        ("help,h", "produce help message")
        ("input-file,i", po::value< vector<string> >(&idata.input_file), "")
        ("draw-file,d", po::value<string>(&idata.draw_file), "File containing stuff to 'draw'")
        ("obj-file,o", po::value<string>(&idata.obj_file), "File containing wavefront OBJ data")
        ("save-grid", po::value<string>(&idata.save_grid), "File to save grid into")
        ("load-grid", po::value<string>(&idata.load_grid), "File to load grid from")

        ("tool,t", po::value<int>(&idata.tool_index), "Which tool index to use from tool csv file")
        ("tool-file,c", po::value<string>(&idata.tool_file), "Path to tool csv file")

        (",x", po::value<double>(&idata.gridx)->default_value(0))
        (",y", po::value<double>(&idata.gridy)->default_value(0))
        (",z", po::value<double>(&idata.gridz)->default_value(0))

        (",X", po::value<double>(&idata.sizex)->default_value(1))
        (",Y", po::value<double>(&idata.sizey)->default_value(1))
        (",Z", po::value<double>(&idata.sizez)->default_value(1))

        ("resolution,r", po::value<double>(&idata.res)->default_value(0.01))

        ("sim-only", po::value<bool>(&idata.sim_only)->default_value(false), "Only run sim, no display")
        ("quit-after", po::value<bool>(&idata.quit_after)->default_value(false), "Quit after simulation is complete")
        ;

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    if (vm.count("help")) {
        std::cout << desc << "\n";
        return 1;
    }

    gui_interface::setup(argv[0]);

    assert(restart_gl_log());
    assert(start_gl(camera.get_width(), camera.get_height()));
    glfwSetWindowSizeCallback(g_window, glfw_window_size_callback);

    BackgroundContext context;
    gui_interface::add_context(context);

    camera.bind();
    camera.set_position(vec3ff(2, 6, 6));
    camera.rotate_yaw(0);
    camera.rotate_pitch(-35);

    if (vm.count("draw-file")) {
        context.drawables.load(idata.draw_file);
    }


    if (vm.count("obj-file")) {
        fprintf(stderr, "Loading obj file... %s\n", idata.obj_file.c_str());

        World::Mesh *thing = new World::Mesh(idata.obj_file, camera, SPECTRUM);
        context.world_objects.push_back(thing);

        /*
        World::Mesh *thing = new World::Mesh(idata.obj_file, camera, PHONG);
        vec3ff spec(1.0, 1.0, 1.0), ambient(1.0, 1.0, 1.0), col1(0.5, 0.5, 0.0);
        thing->set_shader(camera, PHONG);
        thing->setUniformVector3f("color_specular", spec); 
        thing->setUniformVector3f("color_ambient", ambient); 
        thing->setUniformVector3f("color_diffuse", col1);
        */


    }

    // tell GL to only draw onto a pixel if the shape is closer to the viewer
    glEnable(GL_DEPTH_TEST); // enable depth-testing
    glDepthFunc(GL_LESS); // depth-testing interprets a smaller value as "closer"

    //glEnable(GL_CULL_FACE); // cull face
    //glCullFace(GL_BACK); // cull back face
    //glFrontFace(GL_CCW); // GL_CCW for counter clock-wise

    //glPolygonMode(GL_FRONT, GL_LINE);

    //glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
    //glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);


#ifdef _WIN32
    float cam_speed = 2*0.002f;
#else
    float cam_speed = 4.f;
#endif

    float cam_heading_speed = 20.0f; 



    //    Tools *tools;
    fprintf(stderr, "Setting default tool\n");
    vec3ff loc(-1, -1, -1);
    Bit *b1 = new Bit(loc);
    //b1->add(new BitCylinder(0, 2, 1/8.));
    
    if (0) {
	    double rad = 1/16.;
	    b1->add(new BitCylinder(rad, 4, rad));
	    b1->add(new BitSphere(rad, rad));
    } else {
           double rad = 1/16.;
           double height = rad / tan(DEG2RAD * 30.0);
           b1->add(new BitCylinder(height, 1, rad));
	   b1->add(new BitCone(0, height, 5/1000., rad));
    }
    b1->set_shader(camera, SPECTRUM);
    context.bit = b1;

    if (vm.count("tool-file")) {
        //tools = new Tools(idata.tool_file);
        //context.paths.set_tools(tools);

        if (vm.count("tool")) {
            //context.paths.set_bit(tools->get_tool(idata.tool_index));
        }
    }
    
    context.camera = &camera;

    World::Axes axes(camera, SPECTRUM);

    glClearColor(.5, .66, .9, 1);

    gui_interface::load_gcode_file();

    bool saved = false;
    while (!glfwWindowShouldClose(g_window)) {
      _update_fps_counter(g_window);

      // add a timer for doing animation
      static double previous_seconds = glfwGetTime();
      double current_seconds = glfwGetTime();
      double elapsed_seconds = current_seconds - previous_seconds;
      previous_seconds = current_seconds;
      
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
      
      /*********************************************************************************/
      axes.render();
      context.render();
      /*********************************************************************************/

      glfwPollEvents();
      glfwSwapBuffers(g_window);
      
      if (gl_keyStates[GLFW_KEY_ESCAPE]) {
          glfwSetWindowShouldClose(g_window, 1);
          break;
      }

      if (gl_keyStates[GLFW_KEY_N]) {
          context.paused = 0;
          gl_keyStates[GLFW_KEY_N] = false;
      }

      // control keys
      camera.process_controls_standard(cam_speed, cam_heading_speed, elapsed_seconds);

      if (camera.is_dirty()) {
          camera.update_uniform_block();
      }

      gui_interface::update_gcode_selection();

      if (context.sim_done) {
          if (vm.count("save-grid") && !saved) {
              fprintf(stderr, "Saving grid to %s\n", idata.save_grid.c_str());
              context.grid->save(idata.save_grid);
              saved = true;
          }

          if (idata.quit_after) {
              break;
          }
      }

      Tcl_DoOneEvent(TCL_ALL_EVENTS | TCL_DONT_WAIT);
    }

    glfwTerminate();

    return 0;
}

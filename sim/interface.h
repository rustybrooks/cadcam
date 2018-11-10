#pragma once

#include "background.h"
#include "path.h"

struct InterfaceData {
    std::vector<std::string> input_file;
    std::string draw_file, tool_file, obj_file, save_grid, load_grid;
    double gridx, gridy, gridz, sizex, sizey, sizez;
    double res;
    int tool_index;
    bool sim_only, quit_after;
};

extern InterfaceData idata;

namespace gui_interface {
    void setup_gcode(std::string parent);
    void setup(char *argv0, std::string parent="");

    void tk_update();
    void reset_system();
    void load_gcode_file();

    void add_gcode_line(GcodeLine &line);

    void add_context(BackgroundContext &context);
    void update_gcode_selection();
}

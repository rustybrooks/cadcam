#include <cpptk.h>

#include "interface.h"

using namespace Tk;

BackgroundContext *saved_context;
BackgroundSim bgobj_sim;
InterfaceData idata;
boost::thread thread_bgsim;

// defined in sim.cpp
extern void safe_exit();


namespace gui_interface {


    void cmd_next() {
        saved_context->paused = 0;
        update();
    }

    void cmd_openFile() {
        idata.input_file.clear();
        idata.input_file.push_back(std::string(tk_getOpenFile()));
        reset_system();
        load_gcode_file();
    }

    void cmd_reopenFile() {
        reset_system();
        load_gcode_file();
    }

    void cmd_exit() {
        safe_exit();
    }

    // This is so other modules can call update without having to import cpptk
    void tk_update() {
        Tk::update();
    }

    void reset_system() {
        saved_context->do_exit = 1;
        thread_bgsim.join();
        saved_context->clear();

        ".f.textf.text" << configure() -state(Tk::normal);
        ".f.textf.text" << deletetext(txt(1, 0), end);
        ".f.textf.text" << configure() -state(Tk::disabled);
        update();
    }

    void load_gcode_file() {
        if (idata.input_file.size()) {
            vector<double> stock_args;
            if (extract_gcode_args(idata.input_file[0], stock_args, saved_context->bit) && !idata.load_grid.size()) {
                idata.sizex = stock_args[0];
                idata.sizez = stock_args[1];
                idata.sizey = stock_args[2];
                
                idata.gridx = stock_args[3];
                idata.gridy = stock_args[4];
                idata.gridz = stock_args[5];
            }
            saved_context->bit->set_shader(*(saved_context->camera), SPECTRUM);

            BOOST_FOREACH(std::string fname, idata.input_file) {
                GcodeFile *f = process_gcode_file(fname);
                f->dumbass_shader_shit(*(saved_context->camera));
                saved_context->files.add(f);
            }
        }

        saved_context->new_grid(vec3f(idata.gridx, idata.gridy, idata.gridz), vec3f(idata.sizex, idata.sizey, idata.sizez), idata.res);
        if (idata.load_grid.size()) {
            saved_context->grid->load(idata.load_grid, true); // bool is "flipx or no"
        } else {
        }

        vec3ff spec(1.0, 1.0, 1.0), ambient(1.0, 1.0, 1.0), col1(1.0, 0.5, 0.0);
        saved_context->grid->set_shader(*(saved_context->camera), PHONG);
        saved_context->grid->setUniformVector3f("color_specular", spec); 
        saved_context->grid->setUniformVector3f("color_ambient", ambient); 
        saved_context->grid->setUniformVector3f("color_diffuse", col1);

        saved_context->grid->marching_cubes();

        thread_bgsim = boost::thread(bgobj_sim, saved_context);
    }

    void setup_gcode(std::string parent) {
        frame(parent + ".butf");
        pack(parent + ".butf") -side(top) -fill(x) -expand(0);
        frame(parent + ".textf");
        pack(parent + ".textf") -side(top) -fill(both) -expand(1);

        textw(parent + ".textf.text") -yscrollcommand(parent + ".textf.scroll set") -height(25) -state(Tk::disabled);
//-selectmode("single")
//;
        pack(parent + ".textf.text") -side(left) -fill(both) -expand(1);
        scrollbar(parent + ".textf.scroll") -command(parent + ".textf.text yview");
        pack(parent + ".textf.scroll") -side(left) -fill(y) -expand(0);

//        button(parent + ".butf.play") -text("Play");
        button(parent + ".butf.next") -text("Next") -command(cmd_next);
        checkbutton(parent + ".butf.cplot") -text("Backplot");
        checkbutton(parent + ".butf.cmat") -text("Material");
        checkbutton(parent + ".butf.cbit") -text("Bit");
        checkbutton(parent + ".butf.cpause1") -text("Pause after line");
        checkbutton(parent + ".butf.cpause2") -text("Pause after cmt");

//        pack(parent + ".butf.play") -side(left);
        pack(parent + ".butf.next") -side(left);
        pack(parent + ".butf.cplot") -side(left);
        pack(parent + ".butf.cmat") -side(left);
        pack(parent + ".butf.cbit") -side(left);
        pack(parent + ".butf.cpause1") -side(left);
        pack(parent + ".butf.cpause2") -side(left);
    }

    void setup(char *argv0, std::string parent) {
        init(argv0);
           
          // create the menubar
          frame(parent + ".mbar") -borderwidth(1) -relief(raised);
          pack(parent + ".mbar") -Tk::fill(x) -side(top);
          
          // create the menu File entry
          menubutton(parent + ".mbar.file") -text("File") -submenu(".mbar.file.m");
          pack(parent + ".mbar.file") -side(Tk::left);
          
          // create the drop-down menu
          string drop(menu(parent + ".mbar.file.m"));
          drop << add(command) -menulabel("Open") -command(cmd_openFile);
          drop << add(command) -menulabel("Re-Open") -command(cmd_reopenFile);
//          drop << add(command) -menulabel("Save") -command(saveFile);
          drop << add(command) -menulabel("Exit") -command(cmd_exit);

 
        std::string gcode_frame(parent + ".f");
        frame(gcode_frame);
        pack(gcode_frame) -side(left) -fill(both) -expand(1);

        setup_gcode(gcode_frame);
        update();

        Tk::setupEventLoop();
    }

    void add_gcode_line(GcodeLine &line) {
        ".f.textf.text" << configure() -state(Tk::normal);
        ".f.textf.text" << insert(end, line.get_line());
        ".f.textf.text" << insert(end, "\n");
        ".f.textf.text" << configure() -state(Tk::disabled);
    }

    void add_context(BackgroundContext &context) {
        saved_context = &context;
        ".f.butf.cplot" << configure() -variable(context.show_backplot);
        ".f.butf.cmat"  << configure() -variable(context.show_grid);
        ".f.butf.cbit"  << configure() -variable(context.show_bit);
        ".f.butf.cpause1" << configure() -variable(context.stop_at_path);
        ".f.butf.cpause2" << configure() -variable(context.stop_at_comment);
    }

    void update_gcode_selection() {
        static int current_selection = -1;
        int new_selection = saved_context->files.last_line()+1;
        if (new_selection != current_selection) {
//            fprintf(stderr, "gcode selection = %d\n", new_selection);
            ".f.textf.text" << configure() -state(Tk::normal);
            ".f.textf.text" << tag(Tk::remove, "current_line", txt(0,0), end);
            ".f.textf.text" << tag(add, "current_line", txt(new_selection, 0), txt(new_selection, "end"));
            ".f.textf.text" << tag(configure, "current_line")  -background("#0000FF") -foreground("#ffffff");
            ".f.textf.text" << see(txt(new_selection, 0));
            ".f.textf.text" << configure() -state(disabled);
            update();
            current_selection = new_selection;
        }
    }

}

#pragma once

#include "bit.h"
#include "drawings.h"
#include "grid_volume.h"
#include "mymath.h"
#include "path.h"
#include "sim.h"
#include "sim_time.h"
#include "world.h"

#include <boost/thread/thread.hpp>

using Drawings::Drawables;

class BackgroundContext {
public:
    BackgroundContext() 
        : do_exit(false)
        , sim_done(false)
        , files()
        , bit(NULL)
        , backplot(SPECTRUM)
        , drawables(SPECTRUM)
        , world_objects()
        , show_grid(1)
        , show_backplot(1)
        , show_drawables(1)
        , show_bit(1)
        , paused(1)
        , stop_at_path(1)
        , stop_at_comment(0)
        , est_run_time()
    {}

    void new_grid(vec3ff _start, vec3ff _bounds, double _res) {
        if (grid) {
            // delete grid;  // FIXME make deleting actually work (borked in winders)
        }
        grid = new GridVolume(_start, _bounds, _res);
    }

    void render() {
        if (show_grid) grid->render();
        if (show_backplot) backplot.render();
        if (show_drawables) drawables.render();
        if (show_bit && bit) {
            //bit->maybe_set_shader(*camera, SPECTRUM);
            bit->render();
        }
        drawables.render();
        BOOST_FOREACH(World::Drawable *d, world_objects) {
            d->render();
        }
    }

    void clear() {
        files.clear();
        do_exit = 0;
        sim_done = 0;
        paused = 1;
        backplot.clear();
    }

    bool do_exit, sim_done;
    GridVolume *grid;
    GcodeFileSet files;
    Bit *bit;
    BackPlot backplot;
    Drawables drawables;
    vector<World::Drawable *> world_objects;
    Camera *camera;

    // these are actually bools but tcl interface doesn't do bools
    int show_grid, show_backplot, show_drawables, show_bit, paused, stop_at_path, stop_at_comment;  
    std::string est_run_time;

    int current_gcode_line;
};

class BackgroundSim {
public:
    BackgroundSim() 
    {};

    bool simulation_step(BackgroundContext *context) {
        boost::optional<pointf> loc = context->files.next_step(context->bit, context->stop_at_path, context->stop_at_comment);
        
        if (loc == boost::none) {
            return false;
        }

        context->grid->set_rotation(loc->angles.x);
        context->bit->set_position_rotation(loc->point, -(loc->angles.x), 0, 0);
        context->grid->remove_intersection(*(context->bit));
        context->backplot.incr_steps();
        
        return true;
    }

    void operator()(BackgroundContext *context) {
        context->do_exit=0;
        context->paused=0;
        fprintf(stderr, "Starting background calculation thread\n");
        SimTime last_march = SimTime::now();

        // let's start by generating the entire toolpath as a backplot
        boost::optional<pointf> loc;
        vec3ff tmppoint;
        while (true) {
            loc = context->files.next_step(context->bit, false, false);
            if (loc == boost::none) break;
            tmppoint = loc->point;
            rotate3x(tmppoint, -loc->angles.x);
            context->backplot.add(tmppoint, vec3ff(.1, 1, .1));
        }
        context->backplot.schedule_bind();
        context->files.reset();
        
        bool done = false;
        while (true) {
            if (context->do_exit) break;
            if (done) break;
            
            if (context->paused) {
                boost::this_thread::sleep(boost::posix_time::milliseconds(50));
            } else {
                do {
                    if (!simulation_step(context)) {
                        context->paused = 1;
                        if (!context->files.have_more()) done = true;
                        break;
                    }
                } while ((SimTime::now() - last_march).toDouble() < .5);
                context->grid->marching_cubes();
                last_march = SimTime::now();
            }
        }

        context->grid->marching_cubes();

        fprintf(stderr, "Background sim thread finished\n");
        context->sim_done = 1;
    }
};

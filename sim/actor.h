#pragma once

#include "mygl.h"
#include "sim_time.h"

enum movemode_t {
    MOVEMODE_FLY, MOVEMODE_WALK,
    MOVEMODE_MAX
};

class Actor {
public:
    Actor(double _x=0, double _y=0, double _z=0, double _az=0, double _zen=90.0, double _zrot=0) :
        x(_x), y(_y), z(_z), az(_az), zen(_zen), zrot(_zrot),
        velocity_fb(0), velocity_lr(0), velocity_ud(0),
        jumping(false), fov(60),
        last_act(-1), last_move(-1),
        move_mode(MOVEMODE_FLY),
        height(1.7),
        near_dist(.2), far_dist(200)
    {
    }

    virtual ~Actor() {};

    void set_position(double _x, double _y, double _z) {
        x=_x; y=_y, z=_z;
    }

    void set_velocity(double _fb, double _lr, double _ud) {
        velocity_fb=_fb; velocity_lr=_lr; velocity_ud=_ud;
    }

    void set_movemode(movemode_t _move_mode) { move_mode = _move_mode; }
    void set_move_dt(double _move_dt) { move_dt = _move_dt; }
    void set_act_dt(double _act_dt) { act_dt = _act_dt; }
    void set_last_move(SimTime _last_move) { last_move = _last_move; }
    void set_last_act(SimTime _last_act) { last_act = _last_act; }

    double get_act_dt() { return act_dt; }

    double delta_time_act() {
        if (last_act < 0) last_act = SimTime::now();
        return (SimTime::now() - last_act).toDouble();
    }

    double delta_time_move() {
        if (last_move < 0) last_move = SimTime::now();
        return (SimTime::now() - last_move).toDouble();
    }

    double get_fov() { return fov; }
    void set_fov(double val) { fov = val; }

    virtual void move() {
        const double gravity = 15;

        std::pair<int,int> bound;

        double zenr=zen/180.0*PI;
        double azr=az/180.0*PI;
        double zens=sin(zenr);
        double zenc=cos(zenr);
        double azs=sin(azr);
        double azc=cos(azr);

        double newx, newy, newz;

        if (move_mode == MOVEMODE_WALK) {
            //double projdfb = velocity_fb==0 ? 0 : 0.15*velocity_fb/abs(velocity_fb);
            //double projdlr = velocity_lr==0 ? 0 : 0.15*velocity_lr/abs(velocity_lr);
            newx = x + -1*velocity_lr*move_dt*zens + velocity_fb*move_dt*zenc;
            newz = z + 1*velocity_lr*move_dt*zenc + velocity_fb*move_dt*zens;
            //double projx = newx + -1*projdlr*zens + projdfb*zenc;
            //double projz = newz + projdlr*zenc + projdfb*zens;

            if (jumping) {
                newy = y + (velocity_ud*move_dt - 0.5*gravity*move_dt*move_dt);
                velocity_ud -= gravity*move_dt;
            } else {
                newy = y;
            }

            bound = std::pair<int, int>(0,0);
            //bound = game.land.height_bound(projx, y, projz);

            if (abs(bound.first - newy) < 0.01) {
                jumping=false;
                velocity_ud = 0;

                y = bound.first;
                x=newx;
                z=newz;
            } else if (bound.first < newy) {
                jumping=true;

                if (newy <= bound.first) {
                    newy = bound.first;
                    velocity_ud = 0;
                    jumping=false;
                }

                x=newx;
                z=newz;
                y=newy;
            } else {

                //bound = game.land.height_bound(x, y, z);

                if (newy <= bound.first) {
                    newy = bound.first;
                    velocity_ud = 0;
                    jumping=false;
                }

                y=newy;
            }
        } else if (move_mode == MOVEMODE_FLY) {

            vec3f s = sightline(velocity_fb*move_dt);

            x += s.x + -1*velocity_lr*move_dt*azc;
            y += velocity_ud*move_dt + s.y;
            z += s.z + 1*velocity_lr*move_dt*azs;

        }
    }

  /*
    vec3f sightline(double distance) {
        return projection(az, zen, distance);
    }
  */

    virtual void rotate(double az_amt, double zen_amt) {
        zen += zen_amt;
        az = normalize_angle(az + az_amt, 360);

        if (zen>=180)
            zen=180;
        else if (zen<=0)
            zen=0.00001;

        //fprintf(stderr, "zen=%f, az=%f\n", zen, az);
    }

    virtual void focus() {


        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        // window_perspective() - hard coded persp for now
        gluPerspective(fov, 800.0/600, near_dist, far_dist);
        glMatrixMode(GL_MODELVIEW);

        //print self.x, self.y, self.z, self.az, self.zen
        glLoadIdentity();
        //glTranslatef(-0.4,0,-0.4);
        //glRotatef(-90,0.0,1.0,0.0);
        //glRotatef(-zen-90,0.0,1.0,0.0);

        vec3f s = sightline(1.0);

        //fprintf(stderr, "Looking at %f,%f,%f (%f, %f)\n", s.x, s.y, s.z, az, zen);
        gluLookAt(x, y+height, z,
                  x+s.x, y+s.y+height, z+s.z,
                  0.0, 0.1, 0.0);

        // This specicically assumes your eye is at a height of 1.7
        //glTranslatef(-x,-y-1.7,-z);
    }

public:
    double x, y, z;
    double az, zen, zrot;
    double velocity_fb, velocity_lr, velocity_ud;
    bool jumping;
    double fov;

protected:
    SimTime last_act, last_move;
    double act_dt, move_dt;
    movemode_t move_mode;
    double height;
    double near_dist, far_dist;
};

 

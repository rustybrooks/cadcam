#pragma once

#include "mymath.h"
#include "world.h"
#include "bit.h"

#include <boost/optional.hpp>
#include <boost/foreach.hpp>

#include <vector>
#include <string>   
#include <map>


extern char _parameter_file_name[];               /* in canon.cc */

using std::map;
using std::vector;

class GcodeFile;

void report_error(int error_code, /* the code number of the error message */
                  int print_stack); /* print stack if ON, otherwise not     */
GcodeFile *process_gcode_file(std::string filename);
bool extract_gcode_args(std::string filename, std::vector<double> &stock_args, Bit *b);
bool parse_gcode_comment(std::string line, vector<double> &stock_args, Bit *b);

class Path {
public:

    Path(pointf _start, pointf _end, int _steps=-1, double min_step=0.01)
        : start(_start)
        , end(_end)
        , _location(_start)
        , steps(_steps)
    {

        if (steps == -1) {
            pointf diff = end - start;

            double length;

            if (end.angles.x == start.angles.x) {
                length = xlength(diff.point);
                steps = int(ceil(length/min_step));
            } else {
                length = calc_path_length(100);
                steps = int(ceil(length/min_step));

                while (subdivide(min_step)) {
                    //printf("Subdividing %lu\n", curve.size());
                }
            }
        }
    }

    pointf &location() { return _location; }

    pointf value_at(double pct) {
        return start + (end - start)*pct;
    }

    inline pointf& coords_at(pointf &v) {
        double x, y, z, sa, ca;
        
        ca = cos(v.angles.x*DEG2RAD);
        sa = sin(v.angles.x*DEG2RAD);
            
        x = v.point.x;
        y = v.point.y*ca - v.point.z*sa;
        z = v.point.y*sa + v.point.z*ca;
        tmpv.point.x = x;
        tmpv.point.y = y;
        tmpv.point.z = z;
        return tmpv;
    }

    inline pointf coords_at(double pct) {
        pointf x = value_at(pct);
        return coords_at(x);
    }

    virtual pointf &step(int step, bool abs=false) {
        if (steps == 0) return start;

        if (abs)
            _location = start + (end - start)*(double(step)/steps);
        else
            _location += (end - start)*(double(step)/steps);

        return _location;
    }

    double segment_length(double start_val, double end_val) {
        pointf v1 = coords_at(start_val);
        pointf v2 = coords_at(end_val);
        //printf("coords_at() (%f, %f, %f), (%f, %f,%f)\n", v1[0], v1[1], v1[2], v2[0], v2[1], v2[2]);
        vec3ff tmp = v2.point - v1.point;
        return xlength(tmp);  // is this right?
    }


    bool subdivide(double maxlen) {
        map<double, double> newcurve;
        map<double, double>::iterator it, begin=curve.begin(), end=curve.end();
        double lastlen=0;
        double laststep=0;
        double substep;
        bool swapped=false;

        int count=0;
        for (it=begin; it!=end; it++) {
            newcurve[it->first] = it->second;

            if (it->second - lastlen > maxlen) {
                //printf("(%d) %f - %f (%f) > %f\n", count, it->second, lastlen, it->second-lastlen, maxlen);
                substep = (it->first + laststep)/2.0;
                if (substep - laststep > 1e-9) {
                    newcurve[substep] = it->second - segment_length(laststep, substep);
                //printf("Adding substep %0.9f between %0.9f and %0.9f, oldlen=%f, newlen=%f\n", substep, it->first, laststep, newcurve[substep], it->second - lastlen);
                    swapped=true;
                }
            }

            laststep = it->first;
            lastlen = it->second;
            count++;
        }

        if (swapped) {
            curve.swap(newcurve);
            //subdivide(maxlen);
        }

        return swapped;
    }

    double binary_search(double start_pct, double end_pct, double maxlen, double epsilon=-.01) {
        if (epsilon < 0) epsilon = maxlen*-1*epsilon;

        double trial = (end_pct-start_pct)/2.0;
        double len = segment_length(start_pct, trial);
        if (len - maxlen < epsilon) {
            return trial;
        } else if (len > maxlen) {
            return binary_search(start_pct, trial, maxlen, epsilon);
        } else {
            return binary_search(trial, end_pct, maxlen, epsilon);
        }
    }

    double calc_path_length(int num_steps=1000) {
        curve.clear();

        const double d = 1.0/num_steps;

        double len=0, this_len;
        double last_t=0;
        for (double t=d; t<=1; t+=d) {

            this_len=segment_length(last_t, t);
            len+=this_len;
            curve[t] = len;
            last_t = t;
        }

        if (last_t < 1) {
            this_len=segment_length(last_t, 1.0);
            curve[1.0] = len;
            len+=this_len;
        }

        return len;
    }

protected:
    pointf start;
    pointf end;
    pointf _location;
    pointf tmpv;  // FIXME maybe can get rid of
    map<double, double> curve;

public:
    int steps;
};


enum ArcPlaneEnum { XY, XZ, YZ };

class ArcPath : public Path {
public:

    ArcPath(pointf _start, pointf _end, pointf _center, ArcPlaneEnum _plane, bool _clockwise=true, int _steps=-1, double _min_step=0.01)
        : Path(_start, _end, _steps, _min_step)
        , center(_center)
        , clockwise(_clockwise)
        , plane(_plane)
    {
        if (_steps == -1) {
            steps = 200;
        }
    }

    virtual pointf &step(int step, bool abs=false) {
        if (steps == 0) return start;

        vec3ff tx1(start.point);
        vec3ff tx2(end.point);
        vec3ff cen(center.point);
        vec3ff x1 = tx1 - cen;
        vec3ff x2 = tx2 - cen;
        if (plane == XY) {
            double angle;
            if (start.point.x == end.point.x and start.point.z == end.point.z) {
                if (clockwise)
                    angle = 360;
                else
                    angle = -360;
            } else {
                if (clockwise) {
                    angle = -1*angle_between(x1, x2);
                    //print(cen, "center");
                    //print(tx1, "tx1");
                    //print(tx2, "tx2");
                    //print(x1, "x1");
                    //print(x2, "x2");
                    //fprintf(stderr, "angle between = %f\n", angle);
                } else {
                    angle = 1*(360-angle_between(x1, x2));
                    //print(cen, "center");
                    //print(tx1, "tx1");
                    //print(tx2, "tx2");
                    //print(x1, "x1");
                    //print(x2, "x2");
                    //fprintf(stderr, "angle between = %f\n", angle);
                }
/*
                if (clockwise) {
                    angle = angle_between(x1, x2);
                } else {
                    angle = -1*(360-angle_between(x1, x2));
                }
*/
            }
            vec3ff newv(x1);
            rotate3y(newv, angle*step/steps);
            _location.point = newv + cen;
            _location.point.y = tx1.y + (tx2.y - tx1.y)*step/steps;
        } else if (plane == YZ) {
            fprintf(stderr, "unhandled plane 1\n");
        } else if (plane == XZ) {
            fprintf(stderr, "unhandled plane 2\n");
        } else {
            fprintf(stderr, "unhandled plane 3\n");
        }

        return _location;
    }

private:
    pointf center;
    bool clockwise;
    ArcPlaneEnum plane;
};


class GcodeLine {
public:
    GcodeLine(std::string _line, Path *_path=NULL)
        : line(_line)
        , path(_path)
        , current_step(0)
        , bit(NULL)
    {
        //fprintf(stderr, "Adding line %s\n", _line.c_str());
        if (_line.find("(") != std::string::npos) {
            vec3ff loc(-1, -1, -1);
            bit = new Bit(loc);
            vector<double> foo;
            fprintf(stderr, "Adding bit\n");
            parse_gcode_comment(_line, foo, bit);
            if (!bit->has_parts()) {
                fprintf(stderr, "But then removing bit\n");
                delete bit;
                bit = NULL;
            }
        }
    }

    bool is_comment() {
        if (line.find("(") != std::string::npos) {
            return true;
        }

        return false;
    }

    bool parse_comment(Bit *b) {
        if (!is_comment()) return false;

        vector<double> foo;
        parse_gcode_comment(line, foo, b);
        return true;
    }

    std::string &get_line() { 
        return line;
    }

    void set_path(Path *_path) {
        path = _path;
    }

    Path *get_path() { return path; }

    void reset() {
        current_step = 0;
    }

    boost::optional<pointf> next_step(Bit *b) {
        if (!path) {
            /*
            fprintf(stderr, "current_step = %d, is_comment=%d, line=%s\n", current_step, is_comment()?1:0, line.c_str()); 
            if (current_step == 0 and is_comment()) {
                parse_comment(b);
            }
            */
            return boost::none;
        }

        if (current_step > path->steps) {
            return boost::none;
        }

        boost::optional<pointf> l = path->step(current_step, true);
        current_step++;

        return l;
    }

    bool have_more() {
        if (!path) return false;
        if (current_step > path->steps) return false;
        return true;
    }

    Bit *get_bit() {
        return bit;
    }


private:
    std::string line;
    Path *path;
    int current_step;
    Bit *bit;
};

class GcodeFile {
public:
    GcodeFile(std::string _filename)
        : filename(_filename)
        , current_line(0)
        , last_line(-1)
        , status(-1)
    {}

    void add(std::string _line, Path *_path=NULL) {
        lines.push_back(GcodeLine(_line, _path));
    }

    void set_status(int _status) { status = _status; }
    std::string &get_filename() { return filename; }
    
    size_t get_current_line() { return current_line; }
    size_t get_last_line() { return last_line; }

    size_t get_num_lines() {
        return lines.size();
    }

    GcodeLine &current() {
        return lines.back();
    }

    void reset() {
        last_line = -1;
        current_line = 0;

        BOOST_FOREACH(GcodeLine &line, lines) {
            line.reset();
        }
    }

    boost::optional<pointf> next_step(Bit *b, bool stop_at_path, bool stop_at_comment) {
        boost::optional<pointf> l = lines[current_line].next_step(b);
        if (l == boost::none) {
            // advance to next line that has a path
            last_line = current_line;
            while (++current_line < lines.size()) {
                if (lines[current_line].get_bit() != NULL) {
                    fprintf(stderr, "ready to switch bits...\n");
                    b->replace(lines[current_line].get_bit());
                }
                if (lines[current_line].get_path()) {
                    break;
                }
            }
            if (!stop_at_path && current_line < lines.size()) {
                l = lines[current_line].next_step(b);
            }
        } 

        return l;
    }

    bool have_more() {
        if (current_line < lines.size()-1) return true;
        if (current_line >= lines.size()) return false;
        return lines[current_line].have_more();
    }

    void dumbass_shader_shit(Camera &c) {
        BOOST_FOREACH(GcodeLine &l, lines) {
            if (l.get_bit() != NULL) {
                l.get_bit()->set_shader(c, SPECTRUM);
            }
        }
    }


private:
    std::string filename;
    vector<GcodeLine> lines;
    size_t current_line, last_line;
    int status;
};


class GcodeFileSet {
public:
    GcodeFileSet() 
        : current_file(0)
    {}

    void add(GcodeFile *file) {
        files.push_back(file);
    }

    size_t current_line() { 
        size_t num = 0;

        for (size_t i=0; i<std::min(current_file, files.size()-1); i++) {
            num += files[i]->get_num_lines();
        }
        if (current_file < files.size()) {
            num += files[current_file]->get_current_line();
        }

        return num;
    }

    size_t last_line() {
        size_t num = 0;

        for (size_t i=0; i<std::min(current_file, files.size()-1); i++) {
            num += files[i]->get_num_lines();
        }
        if (current_file < files.size()) {
            num += files[current_file]->get_last_line();
        }

        return num;
    }

    void clear() {
        files.clear();  // should dealloc?
    }

    void reset() {
        current_file = 0;
        BOOST_FOREACH(GcodeFile *f, files) {
            f->reset();
        }
    }

    bool have_more() {
        if (current_file < files.size()-1) return true;
        if (current_file >= files.size()) return false;
        return files[current_file]->have_more();
    }

    boost::optional<pointf> next_step(Bit *b, bool stop_at_path, bool stop_at_comment) {
        if (!files.size()) return boost::none;
        if (current_file >= files.size()) return boost::none;

        boost::optional<pointf> l = files[current_file]->next_step(b, stop_at_path, stop_at_comment);
        if (l == boost::none && !files[current_file]->have_more()) {
            if (++current_file >= files.size()) return boost::none;
            fprintf(stderr, "incr file!!\n");
            return files[current_file]->next_step(b, stop_at_path, stop_at_comment);
        } else {
            return l;
        }
    }


private:
    vector<GcodeFile *> files;
    size_t current_file;
};

class BackPlot : public World::Drawable {
public:
    BackPlot(ShaderEnum shader_type=NOSHADER, std::string base=std::string())
        : World::Drawable(shader_type, base)
        , bind_size(0)
        , needs_bind(false)
        , steps(0)
    {
        _points.reserve(1024);
        _colors.reserve(1024);
    }

    void clear() {
        steps = 0;
        _points.clear(); _colors.clear();
        needs_bind = true;
    }

    void reset() {
        steps = 0;
    }

    virtual void render() {
        glBindVertexArray(vao());

        if (needs_bind || _points.size() > bind_size) {
            bind();
        }

        _shader->use();
        glLineWidth(2.0);
        if (_points.size() && steps) 
            glDrawArrays(GL_LINE_STRIP, 0, steps);
    }

    void add(vec3ff point, vec3ff color) {
        _points.push_back(point);
        _colors.push_back(color);

        if (_points.size() >= _points.capacity()) {
            fprintf(stderr, "Reserving %lu points\n", _points.capacity()*2);
            _points.reserve(_points.capacity()*2);
            _colors.reserve(_colors.capacity()*2);
        }
    }
    
    void schedule_bind() {
        needs_bind = true;
    }

    void bind() {
        bind_size = _points.size();
	if (bind_size == 0) return;

        fprintf(stderr, "Binding %lu points\n", bind_size);
        vbo_num = 0;
        if (_shader->requires_positions()) {
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, bind_size*sizeof(GLfloat)*3, _points.data(), GL_DYNAMIC_DRAW);
            
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }
            
        if (_shader->requires_colors()) {
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, bind_size*sizeof(GLfloat)*3, _colors.data(), GL_DYNAMIC_DRAW);
            
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        needs_bind = false;
    }

    void set_steps(size_t _steps) {
        steps = _steps;
    }

    void incr_steps() {
        steps++;
        if (steps > _points.size()) { steps = _points.size(); }
        //        fprintf(stderr, "Steps set to %lu / %lu (%lu)\n", steps, bind_size, _points.size());
    }

private:
    vector<vec3ff> _points, _colors;
    size_t bind_size;
    bool needs_bind;
    size_t steps;
};

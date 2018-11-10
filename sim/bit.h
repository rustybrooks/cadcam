#ifndef __bit_h
#define __bit_h

#include "mymath.h"
#include "mygl.h"
#include "world.h"

#include <algorithm> 
#include <iostream>     
#include <fstream>      
#include <vector>
#include <map>
#include <string>

#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>
#include <boost/tokenizer.hpp>

//using namespace std;
using std::map;
using std::ifstream;
using std::ofstream;

class Bit;

class BitPart : public World::Drawable {
public:
    BitPart(double _start)
        : World::Drawable()
	, bit(NULL)
        , start(_start)
        , color(3, .75)
        , _vertices()
        , _normals()
        , _colors()
        , dirty(true)
    {
    }

    void set_bit(Bit *b) { bit = b; }

    virtual bool point_in(vec3ff const &v) const = 0;
    virtual void bounding_box(vec3ff &bb_start, vec3ff &bb_end) const = 0;

    void set_color(vector<float> const &_color) {
        color = _color;
    }

    int mymod(int num, int modulo) {
        int result = num % modulo;
        while (result < 0)
            result += modulo;

        return result;
    }

    void setup_vbo() {
        fprintf(stderr, "Setting up vbo for bitparts %p %lu\n", _shader, _vertices.size());
        glBindVertexArray(vao());

        while (_colors.size() < _vertices.size()) {
            _colors.push_back(vec3ff(1, 0, 0));
        }

        vbo_num = 0;
        if (_shader->requires_positions()) {
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (_vertices.size()) 
                glBufferData(GL_ARRAY_BUFFER, _vertices.size()*sizeof(GLfloat)*3, _vertices.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (_colors.size()) 
                glBufferData(GL_ARRAY_BUFFER, _colors.size()*sizeof(GLfloat)*3, _colors.data(), GL_STATIC_DRAW);
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_normals()) {
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (_normals.size()) 
                glBufferData(GL_ARRAY_BUFFER, _normals.size()*sizeof(GLfloat)*3, _normals.data(), GL_STATIC_DRAW);
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }        
    }

    virtual void render() {
        if (_vertices.size()) {
            if (dirty) {
                setup_vbo();
                dirty = false;
            }

            _shader->use();
            render_location();
            glBindVertexArray(vao());
            glDrawArrays(GL_TRIANGLES, 0, _vertices.size());
        }
 
    }

protected:
    Bit *bit;
    double start;
    vector<float> color;
    vector<vec3ff> _vertices, _normals, _colors;
    size_t num_vertices;
    bool dirty;
};

class Bit {
public:
    Bit(vec3ff &_start, double _rotx=0, double _roty=0, double _rotz=0)
        : start(_start)
//        , bb_valid(false)
        , rotx(_rotx)
        , roty(_roty)
        , rotz(_rotz)
        , bits_end(parts.end())
    {}

    void clear() {
        parts.clear();
    }

    void add(BitPart *part) {
        part->set_bit(this);
        parts.push_back(part);
        bits_end = parts.end();
    }

    vec3ff get_start(bool _rotate=false) const {
        vec3ff x = start;
        if (_rotate) rotate3x(x, rotx);
        return x;
    }

    void set_position_rotation(vec3ff _start, double _rotx, double _roty, double _rotz) {
        set_position(_start);
        set_rotation(_rotx, _roty, _rotz);
    }

    void set_position(vec3ff _start) {
        //_start.z = -1*_start.z;
        for (vector<BitPart *>::iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->set_location(_start);
        }
        start = _start;
    }

    void set_rotation(double _rotx, double _roty, double _rotz) {
        rotx = _rotx;
        roty = _roty;
        rotz = _rotz;

        cosx = cos(DEG2RAD*rotx);
        sinx = sin(DEG2RAD*rotx);
        cosmx = cos(-1*DEG2RAD*rotx);
        sinmx = sin(-1*DEG2RAD*rotx);
      }


    void render() {
        for (vector<BitPart *>::iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->render();
        }
    }

    void set_shader(Camera &c, ShaderEnum shader_type, std::string base=std::string()) {
        for (vector<BitPart *>::iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->set_shader(c, shader_type, base);
        }
    }

    void maybe_set_shader(Camera &c, ShaderEnum shader_type, std::string base=std::string()) {
        for (vector<BitPart *>::iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->maybe_set_shader(c, shader_type, base);
        }
    }

    void set_color(vector<float> _color) {
        for (vector<BitPart *>::iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->set_color(_color);
        }
    }


    void bounding_box(vec3ff &bb_start, vec3ff &bb_end) const {
        for (vector<BitPart *>::const_iterator it=parts.begin(); it!=bits_end; it++) {
            (*it)->bounding_box(bb_start, bb_end);
        }
    }

    bool point_in(vec3ff const &v) const {

        for (vector<BitPart *>::const_iterator it=parts.begin(); it!=bits_end; it++) {
            if ((*it)->point_in(v)) return true;
        }

        return false;
    }

    bool has_parts() {
        fprintf(stderr, "Bit has %lu parts\n", parts.size());
        return (parts.size() > 0);
    }

    void replace(Bit *newb) {
        fprintf(stderr, "Before replace %lu (%lu)\n", parts.size(), newb->parts.size());
        clear();
        BOOST_FOREACH(BitPart *p, newb->parts) {
            add(p);
        }
        fprintf(stderr, "After replace %lu\n", parts.size());
    }

    friend class BitCylinder;
    friend class BitSphere;
    friend class BitCone;

private:
    vector<BitPart *> parts;
    vec3ff start;
//    bool bb_valid;
    double rotx, roty, rotz;
    double cosx, sinx, cosy, siny, cosz, sinz;
    double cosmx, sinmx, cosmy, sinmy, cosmz, sinmz;
    vector<BitPart *>::iterator bits_end;
};

class BitCylinder : public BitPart {
public:
    BitCylinder(double _start, double _len, double _radius)
        : BitPart(_start)
        , len(_len)
        , radius(_radius)
    {
        const int pts = 25;

        vector<vec3ff> vpts1 = calculate_points(pts, start, false, false);
        vector<vec3ff> vpts2 = calculate_points(pts, start+len, false, false);

        for (int i=0; i<pts; i++) {
            _vertices.push_back(vec3ff(0, start, 0));
            _vertices.push_back(vpts1[i]);
            _vertices.push_back(vpts1[(i+1) % pts]);

            _normals.push_back(vec3ff(0, -1, 0));
            _normals.push_back(vec3ff(0, -1, 0));
            _normals.push_back(vec3ff(0, -1, 0));
        }

        for (int i=pts-1; i>=0; i--) {
            _vertices.push_back(vec3ff(0, start, 0));
            _vertices.push_back(vpts1[i]);
            _vertices.push_back(vpts1[mymod(i-1, pts)]);

            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
        }

        for (int i=0; i<pts; i++) {
            _vertices.push_back(vpts2[i]);
            _vertices.push_back(vpts2[(i+1) % pts]);
            _vertices.push_back(vpts1[(i+1) % pts]);

            _vertices.push_back(vpts2[i]);
            _vertices.push_back(vpts1[(i+1) % pts]);
            _vertices.push_back(vpts1[i]);

            // FIXME These are bogus, fix later via calc
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
            _normals.push_back(vec3ff(0, 1, 0));
        }

        dirty = true;
    }

    virtual void bounding_box(vec3ff &bb_start, vec3ff &bb_end) const {
//        fprintf(stderr, "angle = %f\n", bit->rotx);

        vector<vec3ff> pts1 = calculate_points(4, 0, true, true);
        vector<vec3ff> pts2 = calculate_points(4, len, true, true);

         for (size_t i = 0; i<pts1.size(); i++) {
            if (pts1[i].x < bb_start.x) bb_start.x = pts1[i].x;
            if (pts1[i].y < bb_start.y) bb_start.y = pts1[i].y;
            if (pts1[i].z < bb_start.z) bb_start.z = pts1[i].z;

            if (pts1[i].x > bb_end.x) bb_end.x = pts1[i].x;
            if (pts1[i].y > bb_end.y) bb_end.y = pts1[i].y;
            if (pts1[i].z > bb_end.z) bb_end.z = pts1[i].z;

            if (pts2[i].x < bb_start.x) bb_start.x = pts2[i].x;
            if (pts2[i].y < bb_start.y) bb_start.y = pts2[i].y;
            if (pts2[i].z < bb_start.z) bb_start.z = pts2[i].z;

            if (pts2[i].x > bb_end.x) bb_end.x = pts2[i].x;
            if (pts2[i].y > bb_end.y) bb_end.y = pts2[i].y;
            if (pts2[i].z > bb_end.z) bb_end.z = pts2[i].z;
        }

    }

/*
    virtual bool point_in(vec3ff const &v) const {
        double y = (v.y*bit->cosmx - v.z*bit->sinmx) - bit->start.y;
        if (y > len || y < 0) return false;

        double x = v.x - bit->start.x;
        //if (fabs(x) > radius) return false;

        double z = (v.y*bit->sinmx + v.z*bit->cosmx) - bit->start.z;
        if (x*x + z*z > radius*radius) return false;

        return true;
    }
*/

    virtual bool point_in(vec3ff const &v) const {
        double x = v.x - bit->start.x;
        double y = (v.y*bit->cosmx - v.z*bit->sinmx) - bit->start.y - start;
        double z = (v.y*bit->sinmx + v.z*bit->cosmx) - bit->start.z;

        if (y > len || y < 0) return false;
        if (x*x + z*z > radius*radius) return false;

        return true;
    }

private:
   // probably would be best to use precalced cos/sin
    virtual vector<vec3ff> calculate_points(int num_points, double height, bool _rotate, bool _translate) const {
        vector<vec3ff> pts(num_points, vec3ff());

        double angle = 0;
        double tmp = TWO_PI/num_points;
        for (int i=0; i<num_points; i++) {
            angle += tmp;

            pts[i] = vec3ff(cos(angle)*radius, height, sin(angle)*radius);

            if (_translate) translate(pts[i], bit->start);
            if (_rotate) rotate3x(pts[i], bit->rotx);
        }

        return pts;
    }

private:
    double len;
    double radius;
};

class BitSphere : public BitPart {
public:
    BitSphere(double _start, double _radius)
        : BitPart(_start)
        , radius(_radius)
    {

       
        //        dirty = true;

    }

    bool point_in(vec3ff const &v) const {
        double x = v.x - bit->start.x;
        double y = (v.y*bit->cosmx - v.z*bit->sinmx) - bit->start.y - start;
        double z = (v.y*bit->sinmx + v.z*bit->cosmx) - bit->start.z;

        if (x*x + z*z + y*y > radius*radius) return false;

        return true;
    }

    void bounding_box(vec3ff &bb_start, vec3ff &bb_end) const {
        vector<vec3ff> pts1 = calculate_points(true, true);

        for (size_t i = 0; i<pts1.size(); i++) {
            if (pts1[i].x < bb_start.x) bb_start.x = pts1[i].x;
            if (pts1[i].y < bb_start.y) bb_start.y = pts1[i].y;
            if (pts1[i].z < bb_start.z) bb_start.z = pts1[i].z;

            if (pts1[i].x > bb_end.x) bb_end.x = pts1[i].x;
            if (pts1[i].y > bb_end.y) bb_end.y = pts1[i].y;
            if (pts1[i].z > bb_end.z) bb_end.z = pts1[i].z;
        }
    }

private:
    vector<vec3ff> calculate_points(bool _rotate, bool _translate) const {
        vector<vec3ff> pts(6, vec3ff());

        int i=0;

        pts[i].x = -radius;
        pts[i].y = 0;
        pts[i].z = 0;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        pts[++i].x = radius;
        pts[i].y = 0;
        pts[i].z = 0;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        pts[++i].x = 0;
        pts[i].y = -radius;
        pts[i].z = 0;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        pts[++i].x = 0;
        pts[i].y = radius;
        pts[i].z = 0;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        pts[++i].x = 0;
        pts[i].y = 0;
        pts[i].z = -radius;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        pts[++i].x = 0;
        pts[i].y = 0;
        pts[i].z = radius;
        if (_translate) translate(pts[i], bit->start);
        if (_rotate) rotate3x(pts[i], bit->rotx);

        return pts;
    }

private:
    double radius;
};


class BitCone : public BitPart {
public:
    BitCone(double _start, double _height, double _radius1, double _radius2)
        : BitPart(_start)
        , radius1(_radius1)
        , radius2(_radius2)
        , height(_height)
    {

        const int pts = 25;

        vector<vec3ff> vpts1 = calculate_points(pts, 0, false, false);
        vector<vec3ff> vpts2 = calculate_points(pts, height, false, false);

        _vertices.clear();
        _normals.clear();
        _colors.clear();

        for (int i=0; i<pts; i++) {
            _vertices.push_back(vec3ff(0, 0, 0));
            _vertices.push_back(vpts1[i]);
            _vertices.push_back(vpts1[(i+1) % pts]);
        }

        for (int i=pts-1; i>=0; i--) {
            _vertices.push_back(vec3ff(0, height, 0));
            _vertices.push_back(vpts2[i]);
            _vertices.push_back(vpts2[mymod(i-1, pts)]);
        }

        for (int i=0; i<pts; i++) {
            _vertices.push_back(vpts2[i]);
            _vertices.push_back(vpts2[(i+1) % pts]);
            _vertices.push_back(vpts1[(i+1) % pts]);

            _vertices.push_back(vpts2[i]);
            _vertices.push_back(vpts1[(i+1) % pts]);
            _vertices.push_back(vpts1[i]);
        }

        dirty = true;
    }

    bool point_in(vec3ff const &v) const {
        double y = (v.y*bit->cosmx - v.z*bit->sinmx) - bit->start.y;
        if (y > height || y < 0) return false;

        double x = v.x - bit->start.x;

        double z = (v.y*bit->sinmx + v.z*bit->cosmx) - bit->start.z;
        double radius = (radius2 - radius1)*y/height + radius1;
        if (x*x + z*z > radius*radius) return false;

        return true;
    }

    void bounding_box(vec3ff &bb_start, vec3ff &bb_end) const {
        vector<vec3ff> pts1 = calculate_points(4, 0, true, true);
        vector<vec3ff> pts2 = calculate_points(4, height, true, true);

         for (size_t i = 0; i<pts1.size(); i++) {
            if (pts1[i].x < bb_start.x) bb_start.x = pts1[i].x;
            if (pts1[i].y < bb_start.y) bb_start.y = pts1[i].y;
            if (pts1[i].z < bb_start.z) bb_start.z = pts1[i].z;

            if (pts1[i].x > bb_end.x) bb_end.x = pts1[i].x;
            if (pts1[i].y > bb_end.y) bb_end.y = pts1[i].y;
            if (pts1[i].z > bb_end.z) bb_end.z = pts1[i].z;

            if (pts2[i].x < bb_start.x) bb_start.x = pts2[i].x;
            if (pts2[i].y < bb_start.y) bb_start.y = pts2[i].y;
            if (pts2[i].z < bb_start.z) bb_start.z = pts2[i].z;

            if (pts2[i].x > bb_end.x) bb_end.x = pts2[i].x;
            if (pts2[i].y > bb_end.y) bb_end.y = pts2[i].y;
            if (pts2[i].z > bb_end.z) bb_end.z = pts2[i].z;
        }
    }

private:
    vector<vec3ff> calculate_points(int num_points, double cheight, bool _rotate, bool _translate) const {
        vector<vec3ff> pts(num_points, vec3ff());

        double radius = (radius2 - radius1)*cheight/height + radius1;

        double angle = 0;
        double tmp = TWO_PI/num_points;
        for (int i=0; i<num_points; i++) {
            angle += tmp;

            pts[i] = vec3ff(cos(angle)*radius, cheight, sin(angle)*radius);

            if (_translate) translate(pts[i], bit->start);
            if (_rotate) {
                rotate3x(pts[i], bit->rotx);
            }
        }

        return pts;
    }

private:
    double radius1, radius2, height;
};





enum ToolType { SQUARE, BALL, VEE, DOVETAIL };

// Columns are:
// 0 ** ToolType
// 1 Name
// 2 Type
// 3 Holder Diameter
// 4 Holder Length
// 5 Shank Diameter
// 6 ** Diameter
// 7 ** Corner Radius
// 8 Thread Pitch
// 9 ** Taper Angle
// 10 Tip Angle
// 11 Tip Length
// 13 12 Tip Diameter
// 14 ** Flute Length
// 15 Total Length
// 16 Tool #
// 17 Adjust Reg
// 18 CutCom Reg
// 19 Z Offset
// 20 Direction
// 21 # of Flutes
// 22 Material
// 23 Inserts
// 24 Insert Width
// 25 Coolant
// 26 Comments

struct Tool {
    ToolType tool_type;
    double diameter, corner_radius, taper_angle, flute_length;
};

class Tools {
public:
    Tools(string file) {
        ifstream in(file.c_str());
        if (!in.is_open()) {
            printf("Could not open tool file '%s'\n", file.c_str());
            return;
        }

        typedef boost::tokenizer< boost::escaped_list_separator<char> > Tokenizer;

        vector< string > vec;
        string line;

        while (getline(in,line)) {
            Tokenizer tok(line);
            vec.assign(tok.begin(),tok.end());

            if (vec.size() == 1) continue;

            Tool t;
            if (vec[0] == "SQUARE") {
                t.tool_type = SQUARE;
            } else if (vec[0] == "BALL") {
                t.tool_type = BALL;
            } else if (vec[1] == "VEE") {
                t.tool_type = VEE;
            } else if (vec[1] == "DOVETAIL") {
                t.tool_type = DOVETAIL;
            } else {
                printf("Unhandled tool type: %s\n", vec[16].c_str());
                continue;
            }

            t.diameter = boost::lexical_cast<double>(vec[6]);
            t.corner_radius = boost::lexical_cast<double>(vec[7]);
            t.taper_angle = boost::lexical_cast<double>(vec[9]);
            t.flute_length = boost::lexical_cast<double>(vec[14]);

            tools[boost::lexical_cast<int>(vec[16])] = t;
        }
    }

    Bit *create_tool(int index) const {
        vec3ff v(0, 0, 0);
        Bit *b1 = new Bit(v, 0.0, 0.0, 0.0);
        b1->add(new BitCylinder(0, .5, 1/8.));
        return b1;
    }

    Bit *get_tool(int index) {
        map<int, Bit*>::const_iterator it = bits.find(index);
        if (it == bits.end()) {
            Bit *b = create_tool(index);
            bits[index] = b;
            return b;
        } else {
            return it->second;
        }
    }

private:
    map<int, Tool> tools;
    map<int, Bit*> bits;
};

#endif // __bit_h

#pragma once

#include <assimp/cimport.h> // C importer
#include <assimp/scene.h> // collects data
#include <assimp/postprocess.h> // various extra operations
#include <stdlib.h> // memory management
#include <vector>

#include "mygl.h"
#include "shader.h"
#include "texture.h"
#include "math_funcs.h"
#include "camera.h"

namespace World {
using std::vector;

class Drawable {
public:
    Drawable(Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string()) 
        : location(0, 0, 0)
        , model(identity_mat4())
        , _shader(shader_factory.get(shader_type, base))
        , vbo_num(0)
        , vao_active_index(0)
        , model_location(-1)
    {
        _vao[0] = 0;
        _vao[1] = 1;

        glGenVertexArrays(1, &_vao[0]);
        glGenVertexArrays(1, &_vao[1]);
        glBindVertexArray(_vao[0]);


        for (int i=0; i<4; i++) {
            vbo[i] = 0;
        }

        c.register_shader(*_shader);
    }

    // FIXME copy of above with no camera.  Phase this out
    Drawable(ShaderEnum shader_type=NOSHADER, std::string base=std::string()) 
        : location(0, 0, 0)
        , model(identity_mat4())        
        , _shader(shader_factory.get(shader_type, base))
        , vbo_num(0)
        , vao_active_index(0)
        , model_location(-1)
    {
        _vao[0] = 0;
        _vao[1] = 1;

        glGenVertexArrays(1, &_vao[0]);
        glGenVertexArrays(1, &_vao[1]);
        glBindVertexArray(vao());

        for (int i=0; i<4; i++) {
            vbo[i] = 0;
        }
    }

    void set_shader(Camera &c, ShaderEnum shader_type, std::string base=std::string()) {
        _shader = shader_factory.get(shader_type, base);
        c.register_shader(*_shader);
    }

    void maybe_set_shader(Camera &c, ShaderEnum shader_type, std::string base=std::string()) {
        if (_shader) return;
        set_shader(c, shader_type, base);
    }

    GLuint vao(bool active=true) {
        if (active) {
            return _vao[vao_active_index];
        } else {
            return _vao[(vao_active_index + 1) % 2];
        }
    }

    void swap_vao() {
        vao_active_index = (vao_active_index + 1) % 2;
    }

    void set_location(vec3ff _location) {
        location = _location;
        model = translate(identity_mat4(), location);
        //printf("Setting world position to (%f, %f, %f)\n", location.x, location.y, location.z);
    }

    void render_location() {
        if (model_location < 0) {
            model_location = glGetUniformLocation(_shader->program(), "model");
//            fprintf(stderr, "Found model location at %d\n", model_location);
        }
        glUniformMatrix4fv(model_location, 1, GL_FALSE, model.m);
    }

    void setUniformMatrix4f(const char *name, mat4 &value) { 
        int location = glGetUniformLocation(_shader->program(), name);  // save and factor this out later
        glUniformMatrix4fv(location, 1, GL_FALSE, value.m);
    }

    void setUniformVector3f(const char *name, vec3ff &value) {
        int location = glGetUniformLocation(_shader->program(), name);  // save and factor this out later
        //fprintf(stderr, "set uniform 3f %s loc=%d\n", name, location);
        glUniform3fv(location, 1, value.v);
    }

    virtual void render() = 0;


// FIXME change back to protected once you fix the need to use _shader->program()
public:
    vec3ff location;
    mat4 model;
    ShaderProgram *_shader;
    GLuint _vao[2];
    GLuint vbo[4] = {0, 0, 0};
    size_t vbo_num = 0;
    int vao_active_index;
    int model_location;
};

class World {
};

class Triangle : public Drawable {
public:
    Triangle(ShaderEnum shader_type=NOSHADER, std::string base=std::string()) 
        : Drawable(shader_type, base)
    {
        float points[] = {
            0.0f,  0.5f,  0.0f,
            0.5f, -0.5f,  0.0f,
            -0.5f, -0.5f,  0.0f
        };

        float colors[] = {
            1.0f, 0.0f,  0.0f,
            0.0f, 1.0f,  0.0f,
            0.0f, 0.0f,  1.0f
        };

        float texcoords[] = {
            0.0f, 1.0f,
            1.0f, 0.0f,
            0.0f, 0.0f,
        };

        gldebugf("Requires positions: %d, Requires colors: %d", _shader->requires_positions(), _shader->requires_colors());
        if (_shader->requires_positions()) {
            gldebug("Binding position array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 9 * sizeof(float), points, GL_STATIC_DRAW);

            glEnableVertexAttribArray(vbo_num);
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            gldebug("Binding color array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 9 * sizeof(float), colors, GL_STATIC_DRAW);

            glEnableVertexAttribArray(vbo_num);
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            vbo_num++;
        }

        if (_shader->requires_texcoords()) {
            gldebug("Binding color array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 6 * sizeof(float), texcoords, GL_STATIC_DRAW);

            glEnableVertexAttribArray(vbo_num);
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            vbo_num++;
        }
    }

    virtual void render() {
        _shader->use();
        glBindVertexArray(vao());
        glDrawArrays(GL_TRIANGLES, 0, 3);
    }
};

class Landscape : public Drawable {
public:
    Landscape(string file, float xmin, float ymin, float xmax, float ymax, int xdiv, int ydiv, Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string())
        : Drawable(c, shader_type, base)
        , _xmin(xmin)
        , _ymin(ymin)
        , _xmax(xmax)
        , _ymax(ymax)
        , _xdiv(xdiv)
        , _ydiv(ydiv)
        , _tex(file)
    {
        fprintf(stderr, "Calculate points...\n");
        calculate_points();

        gldebugf("Requires positions: %d, Requires colors: %d", _shader->requires_positions(), _shader->requires_colors());

        if (_shader->requires_positions()) {
            gldebugf("Binding position array, %lu points", _points.size());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _points.size()*sizeof(GLfloat)*3, _points.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            gldebug("Binding color array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _colors.size()*sizeof(GLfloat)*3, _colors.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_texcoords()) {
            gldebug("Binding texcoord array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _texcoords.size()*sizeof(GLfloat)*2, _texcoords.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 2, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        _tex.load();
    }
    
    float get_height(int x, int y) {
        size_t gpi;
        gpi = y*_xdiv+x;
        if (gpi >= _grid_points.size())
            return 0.0;
        else
            return _grid_points[gpi];
    }

    void calculate_points() {
        _points.resize(_xdiv*_ydiv*2*3);
        _texcoords.resize(_xdiv*_ydiv*2*3);
        
        double xinc = double(_xmax-_xmin)/_xdiv;
        double yinc = double(_ymax-_ymin)/_ydiv;
        double rx=_xmin, ry=_ymin;
        int ptctr=0;
        
        for (int y=0; y<_ydiv; y++) {
            for (int x=0; x<_xdiv; x++) {
                printf("---- x=%d, y=%d xinc=%f, yinc=%f\n", x, y, xinc, yinc);
                
                // triangle 1
                _points[ptctr] = vec3ff(rx, get_height(x, y), ry);
                _texcoords[ptctr] = vec2(double(x)/_xdiv, double(y)/_ydiv);
                ptctr++;
                
                _points[ptctr] = vec3ff(rx+xinc, get_height(x+1, y+1), ry+yinc);
                _texcoords[ptctr] = vec2(double(x+1)/_xdiv,  double(y+1)/_ydiv);
                ptctr++;
                
                _points[ptctr] = vec3ff(rx+xinc, get_height(x+1, y), ry);
                _texcoords[ptctr] = vec2(double(x+1)/_xdiv, double(y)/_ydiv);
                
                ptctr++;
                
                // triangle 2
                _points[ptctr] = vec3ff(rx, get_height(x, y), ry);
                _texcoords[ptctr] = vec2(double(x)/_xdiv, double(y)/_ydiv);
                ptctr++;
                
                _points[ptctr] = vec3ff(rx, get_height(x, y+1), ry+yinc);
                _texcoords[ptctr] = vec2(double(x)/_xdiv, double(y+1)/_ydiv);
                ptctr++;
                
                _points[ptctr] = vec3ff(rx+xinc, get_height(x+1, y+1), ry+yinc);
                _texcoords[ptctr] = vec2(double(x+1)/_xdiv, double(y+1)/_ydiv);
                ptctr++;
                
                rx += xinc;
            }
            
            rx = _xmin;
            ry += yinc;
        }
    }
    
    void render() {
        _shader->use();
        glBindVertexArray(vao());
        glDrawArrays(GL_TRIANGLES, 0, _points.size());
    }
    
public:
    vector<float> _grid_points;
    float _xmin, _ymin, _xmax, _ymax;
    int _xdiv, _ydiv;
    vector<vec3ff> _points, _colors;
    vector<vec2> _texcoords;
    SOILTexture _tex;
};

class ColorCube : public Drawable {
public:
    unsigned int program() { return _shader->program(); }
    
    ColorCube(vec3ff origin, float size, Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string())
        : Drawable(c, shader_type, base)
        , _origin(origin)
        , _size(size)
    {

        calculate_points();

        gldebugf("Requires positions: %d, Requires colors: %d", _shader->requires_positions(), _shader->requires_colors());
        if (_shader->requires_positions()) {
            gldebug("Binding position array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _points.size()*sizeof(GLfloat)*3, _points.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            gldebug("Binding position array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _colors.size()*sizeof(GLfloat)*3, _colors.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_texcoords()) {
            gldebug("Binding texcoord array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _texcoords.size()*sizeof(GLfloat)*2, _texcoords.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 2, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }
    }

    void calculate_points() {
        _points.clear();
        _colors.clear();
        
        vec3ff corners[8] = {
            _origin + vec3ff(0,     0,     0),
            _origin + vec3ff(0,     _size, 0),
            _origin + vec3ff(_size, _size, 0),
            _origin + vec3ff(_size, 0,     0),
            
            _origin + vec3ff(0    , 0    , _size),
            _origin + vec3ff(0    , _size, _size),
            _origin + vec3ff(_size, _size, _size),
            _origin + vec3ff(_size, 0    , _size)
        };
        
        vec3ff colors[8] = {
            vec3ff(1.,0,0),
            vec3ff(0,1.,0),
            vec3ff(0,0,1.),
            vec3ff(1.,1.,0),
            vec3ff(1.,0,1.),
            vec3ff(0,1.,1.),
            vec3ff(1.,1.,1.),
            vec3ff(0,0,0)
        };

        //fprintf(stderr, "%f, %f, %f\n", corners[0].v[0], corners[0].v[1], corners[0].v[2]);
        
        // front
        _points.push_back(corners[2]);
        _points.push_back(corners[1]);
        _points.push_back(corners[0]);
        
        _points.push_back(corners[3]);
        _points.push_back(corners[2]);
        _points.push_back(corners[0]);

        // back
        _points.push_back(corners[6]);
        _points.push_back(corners[5]);
        _points.push_back(corners[4]);
        
        _points.push_back(corners[6]);
        _points.push_back(corners[4]);
        _points.push_back(corners[7]);

        // top
        _points.push_back(corners[6]);
        _points.push_back(corners[5]);
        _points.push_back(corners[1]);
        
        _points.push_back(corners[2]);
        _points.push_back(corners[6]);
        _points.push_back(corners[1]);
        
        // bottom
        _points.push_back(corners[0]);
        _points.push_back(corners[4]);
        _points.push_back(corners[7]);
        
        _points.push_back(corners[0]);
        _points.push_back(corners[7]);
        _points.push_back(corners[3]);

        // left
        _points.push_back(corners[1]);
        _points.push_back(corners[5]);
        _points.push_back(corners[0]);
        
        _points.push_back(corners[0]);
        _points.push_back(corners[5]);
        _points.push_back(corners[4]);
        
        // right
        _points.push_back(corners[3]);
        _points.push_back(corners[7]);
        _points.push_back(corners[2]);
        
        _points.push_back(corners[7]);
        _points.push_back(corners[6]);
        _points.push_back(corners[2]);

        // front
        _colors.push_back(colors[2]);
        _colors.push_back(colors[1]);
        _colors.push_back(colors[0]);
        
        _colors.push_back(colors[3]);
        _colors.push_back(colors[2]);
        _colors.push_back(colors[0]);
        
        // back
        _colors.push_back(colors[6]);
        _colors.push_back(colors[5]);
        _colors.push_back(colors[4]);
        
        _colors.push_back(colors[6]);
        _colors.push_back(colors[4]);
        _colors.push_back(colors[7]);

        // top
        _colors.push_back(colors[6]);
        _colors.push_back(colors[5]);
        _colors.push_back(colors[1]);
        
        _colors.push_back(colors[2]);
        _colors.push_back(colors[6]);
        _colors.push_back(colors[1]);
        
        // bottom
        _colors.push_back(colors[0]);
        _colors.push_back(colors[4]);
        _colors.push_back(colors[7]);
        
        _colors.push_back(colors[0]);
        _colors.push_back(colors[7]);
        _colors.push_back(colors[3]);

        // left
        _colors.push_back(colors[1]);
        _colors.push_back(colors[5]);
        _colors.push_back(colors[0]);
        
        _colors.push_back(colors[0]);
        _colors.push_back(colors[5]);
        _colors.push_back(colors[4]);
        
        // right
        _colors.push_back(colors[2]);
        _colors.push_back(colors[7]);
        _colors.push_back(colors[3]);
        
        _colors.push_back(colors[7]);
        _colors.push_back(colors[6]);
        _colors.push_back(colors[2]);

        printf("# points = %lu, # colors = %lu\n", _points.size(), _colors.size());
    }

    void render() {
        _shader->use();
        glBindVertexArray(vao());
        glDrawArrays(GL_TRIANGLES, 0, _points.size());
    }


public:
    vec3ff _origin;
    float _size;
    vector<vec3ff> _points;
    vector<vec3ff> _colors;
    vector<vec2> _texcoords;
};


// probably we can just make this part of "mesh" using assimp, but for example purposes, inlining it here
class ObjFile : public Drawable {
public:
    ObjFile(std::string filename, Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string()) 
        : Drawable(c, shader_type, base)
    {
        load_obj_file(filename.c_str());
        
        gldebugf("Requires positions: %d, Requires colors: %d", _shader->requires_positions(), _shader->requires_colors());
        if (_shader->requires_positions()) {
            gldebug("Binding position array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 3*_point_count*sizeof(GLfloat), _points, GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

    }

    virtual void render() {
        //fprintf(stderr, "Rendering objfile\n");
        _shader->use(); 
        glBindVertexArray(vao());
        glDrawArrays(GL_TRIANGLES, 0, _point_count);
    }

    bool load_obj_file(const char* file_name) {

	float* unsorted_vp_array = NULL;
	float* unsorted_vt_array = NULL;
	float* unsorted_vn_array = NULL;
	int current_unsorted_vp = 0;
	int current_unsorted_vt = 0;
	int current_unsorted_vn = 0;

	FILE* fp = fopen (file_name, "r");
	if (!fp) {
            fprintf (stderr, "ERROR: could not find file %s\n", file_name);
            return false;
	}
	
	// first count points in file so we know how much mem to allocate
	_point_count = 0;
	int unsorted_vp_count = 0;
	int unsorted_vt_count = 0;
	int unsorted_vn_count = 0;
	int face_count = 0;
	char line[1024];
	while (fgets (line, 1024, fp)) {
            if (line[0] == 'v') {
                if (line[1] == ' ') {
                    unsorted_vp_count++;
                } else if (line[1] == 't') {
                    unsorted_vt_count++;
                } else if (line[1] == 'n') {
                    unsorted_vn_count++;
                }
            } else if (line[0] == 'f') {
                face_count++;
            }
	}
	printf (
            "found %i vp %i vt %i vn unique in obj. allocating memory...\n",
            unsorted_vp_count, unsorted_vt_count, unsorted_vn_count
            );
	unsorted_vp_array = (float*)malloc (unsorted_vp_count * 3 * sizeof (float));
	unsorted_vt_array = (float*)malloc (unsorted_vt_count * 2 * sizeof (float));
	unsorted_vn_array = (float*)malloc (unsorted_vn_count * 3 * sizeof (float));
	_points =     (float*) malloc (3 * face_count * 3 * sizeof (float));
	_tex_coords = (float*) malloc (3 * face_count * 2 * sizeof (float));
	_normals =    (float*) malloc (3 * face_count * 3 * sizeof (float));
	printf (
            "allocated %i bytes for mesh\n",
            (int)(3 * face_count * 8 * sizeof (float))
            );
	
	rewind (fp);
	while (fgets (line, 1024, fp)) {
            // vertex
            if (line[0] == 'v') {
		
                // vertex point
                if (line[1] == ' ') {
                    float x, y, z;
                    x = y = z = 0.0f;
                    sscanf (line, "v %f %f %f", &x, &y, &z);
                    unsorted_vp_array[current_unsorted_vp * 3] = x;
                    unsorted_vp_array[current_unsorted_vp * 3 + 1] = y;
                    unsorted_vp_array[current_unsorted_vp * 3 + 2] = z;
                    current_unsorted_vp++;
				
                    // vertex texture coordinate
                } else if (line[1] == 't') {
                    float s, t;
                    s = t = 0.0f;
                    sscanf (line, "vt %f %f", &s, &t);
                    unsorted_vt_array[current_unsorted_vt * 2] = s;
                    unsorted_vt_array[current_unsorted_vt * 2 + 1] = t;
                    current_unsorted_vt++;
				
                    // vertex normal
                } else if (line[1] == 'n') {
                    float x, y, z;
                    x = y = z = 0.0f;
                    sscanf (line, "vn %f %f %f", &x, &y, &z);
                    unsorted_vn_array[current_unsorted_vn * 3] = x;
                    unsorted_vn_array[current_unsorted_vn * 3 + 1] = y;
                    unsorted_vn_array[current_unsorted_vn * 3 + 2] = z;
                    current_unsorted_vn++;
                }
			
		// faces
            } else if (line[0] == 'f') {
                // work out if using quads instead of triangles and print a warning
                int slashCount = 0;
                int len = strlen (line);
                for (int i = 0; i < len; i++) {
                    if (line[i] == '/') {
                        slashCount++;
                    }
                }
                if (slashCount != 6) {
                    fprintf (
                        stderr,
                        "ERROR: file contains quads or does not match v vp/vt/vn layout - \
					make sure exported mesh is triangulated and contains vertex points, \
					texture coordinates, and normals\n"
                        );
                    return false;
                }

                int vp[3], vt[3], vn[3];
                sscanf (
                    line,
                    "f %i/%i/%i %i/%i/%i %i/%i/%i",
                    &vp[0], &vt[0], &vn[0], &vp[1], &vt[1], &vn[1], &vp[2], &vt[2], &vn[2]
                    );

                /* start reading points into a buffer. order is -1 because obj starts from
                   1, not 0 */
                // NB: assuming all indices are valid
                for (int i = 0; i < 3; i++) {
                    if ((vp[i] - 1 < 0) || (vp[i] - 1 >= unsorted_vp_count)) {
                        fprintf (stderr, "ERROR: invalid vertex position index in face\n");
                        return false;
                    }
                    if ((vt[i] - 1 < 0) || (vt[i] - 1 >= unsorted_vt_count)) {
                        fprintf (stderr, "ERROR: invalid texture coord index %i in face.\n", vt[i]);
                        return false;
                    }
                    if ((vn[i] - 1 < 0) || (vn[i] - 1 >= unsorted_vn_count)) {
                        printf ("ERROR: invalid vertex normal index in face\n");
                        return false;
                    }
                    _points[_point_count * 3] = unsorted_vp_array[(vp[i] - 1) * 3];
                    _points[_point_count * 3 + 1] = unsorted_vp_array[(vp[i] - 1) * 3 + 1];
                    _points[_point_count * 3 + 2] = unsorted_vp_array[(vp[i] - 1) * 3 + 2];
                    _tex_coords[_point_count * 2] = unsorted_vt_array[(vt[i] - 1) * 2];
                    _tex_coords[_point_count * 2 + 1] = unsorted_vt_array[(vt[i] - 1) * 2 + 1];
                    _normals[_point_count * 3] = unsorted_vn_array[(vn[i] - 1) * 3];
                    _normals[_point_count * 3 + 1] = unsorted_vn_array[(vn[i] - 1) * 3 + 1];
                    _normals[_point_count * 3 + 2] = unsorted_vn_array[(vn[i] - 1) * 3 + 2];
                    _point_count++;
                }
            }
	}
	fclose (fp);
	free (unsorted_vp_array);
	free (unsorted_vn_array);
	free (unsorted_vt_array);
	printf (
            "allocated %i points\n",
            _point_count
            );
	return true;
    }
    
private:
    GLfloat *_points, *_tex_coords, *_normals;
    int _point_count;
};

class Mesh : public Drawable {
public:
    Mesh(std::string file_name, Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string()) 
        : Drawable(c, shader_type, base)
    {
        load(file_name, true);
        
        if (_shader->requires_positions()) {
            gldebugf("(%s) Binding position array", file_name.c_str());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 3*_point_count*sizeof(GLfloat), _points, GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }
        
        if (_shader->requires_colors()) {
            gldebugf("(%s) Binding color array", file_name.c_str());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 3*_point_count*sizeof(GLfloat), _colors, GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_texcoords()) {
            gldebugf("(%s) Binding texcoords array", file_name.c_str());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 2*_point_count*sizeof(GLfloat), _texcoords, GL_STATIC_DRAW);
            
            glVertexAttribPointer(vbo_num, 2, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }
        
        if (_shader->requires_normals()) {
            gldebugf("(%s) Binding normal array", file_name.c_str());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, 3*_point_count*sizeof(GLfloat), _normals, GL_STATIC_DRAW);
            
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }
    }

    bool load(std::string file_name, bool color_from_angle=false) {
        /* load file with assimp and print some stats */
        const aiScene* scene = aiImportFile (file_name.c_str(), aiProcess_Triangulate);
        if (!scene) {
            fprintf (stderr, "ERROR: reading mesh %s\n", file_name.c_str());
            return false;
        }
        // printf("  %i animations\n", scene->mNumAnimations);
        // printf("  %i cameras\n", scene->mNumCameras);
        // printf("  %i lights\n", scene->mNumLights);
        // printf("  %i materials\n", scene->mNumMaterials);
        // printf("  %i meshes\n", scene->mNumMeshes);
        // printf("  %i textures\n", scene->mNumTextures);
  
        /* get first mesh in file only */
        const aiMesh* mesh = scene->mMeshes[0];
        printf("    %i vertices in mesh[0]\n", mesh->mNumVertices);
  
        /* pass back number of vertex points in mesh */
        _point_count = mesh->mNumVertices;
  
        /* we really need to copy out all the data from AssImp's funny little data
           structures into pure contiguous arrays before we copy it into data buffers
           because assimp's texture coordinates are not really contiguous in memory.
           i allocate some dynamic memory to do this. */
        if (mesh->HasPositions()) {
            fprintf(stderr, "(%s) has positions\n", file_name.c_str());
            _points = (GLfloat*)malloc(_point_count * 3 * sizeof(GLfloat));
            for (int i = 0; i < _point_count; i++) {
                const aiVector3D* vp = &(mesh->mVertices[i]);
                _points[i * 3] = (GLfloat)vp->x;
                _points[i * 3 + 1] = (GLfloat)vp->y;
                _points[i * 3 + 2] = (GLfloat)vp->z;
            }
        }
        if (mesh->HasNormals()) {
            fprintf(stderr, "(%s) has normals\n", file_name.c_str());
            _normals = (GLfloat*)malloc(_point_count * 3 * sizeof(GLfloat));
            _colors = (GLfloat*)malloc(_point_count * 3 * sizeof(GLfloat));

            if (color_from_angle) {
               vec3ff axis(0, 1, 0);
               double angle;
	       GLfloat color;
               print(axis, "axis");
               for (int i=0; i<_point_count; i++) {
                   const aiVector3D* vn = &(mesh->mNormals[i]);
                   //fprintf(stderr, "------------\n");
                   vec3ff normal(vn->x, vn->y, vn->z);
                   //print(normal, "normal");
                   angle = RAD2DEG * asin(std::abs(dot(normal, axis)) / (length(normal) * length(axis)));
                   //color = (angle*2)/(M_PI);
                   fprintf(stderr, "angle=%f, color=%f\n", angle, color);

                   color = ((int) angle*10/90)/10.0;

                   _colors[i * 3] = color;
                   _colors[i * 3 + 1] = color;
                   _colors[i * 3 + 2] = color;
               }


            } else {
                for (int i = 0; i < _point_count; i++) {
                    const aiVector3D* vn = &(mesh->mNormals[i]);
                    _colors[i * 3] = (GLfloat)vn->x;
                    _colors[i * 3 + 1] = (GLfloat)vn->y;
                    _colors[i * 3 + 2] = (GLfloat)vn->z;
                }
            }
        }
        if (mesh->HasTextureCoords(0)) {
            fprintf(stderr, "(%s) has texcoords\n", file_name.c_str());
            _texcoords = (GLfloat*)malloc(_point_count * 2 * sizeof(GLfloat));
            for (int i = 0; i < _point_count; i++) {
                const aiVector3D* vt = &(mesh->mTextureCoords[0][i]);
                _texcoords[i * 2] = (GLfloat)vt->x;
                _texcoords[i * 2 + 1] = (GLfloat)vt->y;
            }
        }

         if (mesh->HasTangentsAndBitangents ()) {
             fprintf(stderr, "(%s) has tangents\n", file_name.c_str());
            // NB: could store/print tangents here
        }
  
        /* free assimp's copy of memory */
        aiReleaseImport(scene);
        printf ("(%s) loaded\n", file_name.c_str());
  
        return true;
    }

    void render() {
        _shader->use();
        render_location();
        glBindVertexArray(vao());
        glDrawArrays(GL_TRIANGLES, 0, _point_count);
    }

public:
    int _point_count;
    GLfloat* _points; // array of vertex points
    GLfloat* _normals; // array of vertex normals
    GLfloat* _texcoords; // array of texture coordinates
    GLfloat* _colors; // array of texture coordinates
};


class Axes : public Drawable {
public:
    Axes(Camera &c, ShaderEnum shader_type=NOSHADER, std::string base=std::string())
        : Drawable(c, shader_type, base)
    {
        calculate_points();

        if (_shader->requires_positions()) {
            gldebugf("Binding position array, %lu points", _points.size());
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _points.size()*sizeof(GLfloat)*3, _points.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            gldebug("Binding color array");
            glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            glBufferData(GL_ARRAY_BUFFER, _colors.size()*sizeof(GLfloat)*3, _colors.data(), GL_STATIC_DRAW);

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

    }

    void calculate_points() {
        // +X
        _points.push_back(vec3ff(0, 0, 0));
        _points.push_back(vec3ff(1000, 0, 0));
        _colors.push_back(vec3ff(0, 1, 0));
        _colors.push_back(vec3ff(0, 1, 0));

        // +Y
        _points.push_back(vec3ff(0, 0, 0));
        _points.push_back(vec3ff(0, 1000, 0));
        _colors.push_back(vec3ff(0, 0, 1));
        _colors.push_back(vec3ff(0, 0, 1));

        // +Z
        _points.push_back(vec3ff(0, 0, 0));
        _points.push_back(vec3ff(0, 0, 1000));
        _colors.push_back(vec3ff(1, 0, 0));
        _colors.push_back(vec3ff(1, 0, 0));
    }

    void render() {
        _shader->use();
        render_location();
        glBindVertexArray(vao());
        glDrawArrays(GL_LINES, 0, _points.size());
    }

 
public:
    vector<vec3ff> _points, _colors;
};

extern ShaderFactory shader_factory;
}

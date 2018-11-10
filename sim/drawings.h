#pragma once

#include "mygl.h"
#include "world.h"

#include <fstream>      
#include <iostream>     
#include <string>
#include <vector>

#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>

//using namespace std;

namespace Drawings {

class Drawables : public World::Drawable {
public:
    Drawables(ShaderEnum shader_type=NOSHADER, std::string base=std::string())
        : World::Drawable(shader_type, base)
        , bind_size(0)
        , needs_bind(false)
    {
        _points.reserve(64);
        _colors.reserve(64);
    }
    
    void load(string file) {
        ifstream in(file.c_str());
        if (!in.is_open()) {
            printf("Could not open draw file '%s'\n", file.c_str());
            return;
        }

        typedef boost::tokenizer< boost::escaped_list_separator<char> > Tokenizer;

        vector< string > vec;
        string line;

        while (getline(in,line)) {
            Tokenizer tok(line);
            vec.assign(tok.begin(), tok.end());

            if (vec[0] == "line") {
                vec3ff start, end;
                vec3ff color;
                
                start.x = boost::lexical_cast<double>(vec[1]);
                start.y = boost::lexical_cast<double>(vec[2]);
                start.z = boost::lexical_cast<double>(vec[3]);

                end.x = boost::lexical_cast<double>(vec[4]);
                end.y = boost::lexical_cast<double>(vec[5]);
                end.z = boost::lexical_cast<double>(vec[6]);

                color.x = boost::lexical_cast<float>(vec[7]);
                color.y = boost::lexical_cast<float>(vec[8]);
                color.z = boost::lexical_cast<float>(vec[9]);

                _points.push_back(start);
                _points.push_back(end);
                _colors.push_back(color);

                if (_points.size() >= _points.capacity()) {
                    fprintf(stderr, "Reserving %lu points\n", _points.capacity()*2);
                    _points.reserve(_points.capacity()*2);
                    _colors.reserve(_colors.capacity()*2);
                }
            } else {
                printf("Unknown drawable type: %s\n", vec[0].c_str());
            }
        }        
    }

    virtual void render() {
        glBindVertexArray(vao());

        if (needs_bind || _points.size() > bind_size) {
            bind();
        }

        _shader->use();
        glLineWidth(2.0);
        if (_points.size()) 
            glDrawArrays(GL_LINES, 0, _points.size());
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

private:
    vector<vec3ff> _points, _colors;
    size_t bind_size;
    bool needs_bind;
};

}

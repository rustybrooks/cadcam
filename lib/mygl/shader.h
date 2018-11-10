#pragma once

#include "mygl.h"
#include "log.h"

#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <cstring>
#include <memory>

//#include <unordered_map>
#include <map>

class ShaderProgram {
public:
    ShaderProgram(std::string base, std::string default_base) 
        : _program(glCreateProgram())
        , _loaded(false)
    {
        if (_loaded) return;

        if (base.size() == 0)
            base = default_base;

        std::string version;
	const GLubyte *glsl_version = glGetString(GL_SHADING_LANGUAGE_VERSION);
//	const GLubyte *gl_version = glGetString(GL_VERSION);
	if (glsl_version[0] == '4') {
	  version = "4.0";
	} else if (glsl_version[0] == '3') {
	  version = "3.3";
	} else {
	  fprintf(stderr, "Minimum supported GLSL version is 3.3");
	  exit(1);
	}
//	fprintf(stderr, "GL version %s, GLSL version = %s, using %s\n", (char *) gl_version, (char *) glsl_version, version.c_str());

        attach_from_file(GL_VERTEX_SHADER, "shaders/" + version + "/" + base + ".vp");
        attach_from_file(GL_FRAGMENT_SHADER, "shaders/" + version + "/" + base + ".fp");
        bind_attrib(0, "vertex_position");
        link();
        print_info();
        _loaded = true;
    }

    virtual bool requires_positions() = 0;
    virtual bool requires_colors() = 0;
    virtual bool requires_normals() = 0;
    virtual bool requires_texcoords() = 0;

    bool loaded() { return _loaded; }
    unsigned int program() { return _program; }
    
    void use() {
        glUseProgram(_program);
    }

    void attach_from_file(GLenum type,  std::string filePath) {
        gldebugf("Loading shader %s", filePath.c_str());
        /* compile the shader */
        GLuint shader = compile_from_file(type, filePath.c_str());
        if(shader != 0) {
            /* attach the shader to the program */
            glAttachShader(_program, shader);
            
            /* delete the shader - it won't actually be
             * destroyed until the program that it's attached
             * to has been destroyed */
            glDeleteShader(shader);
        }
    }

    void link() {
        GLint result;

        /* link the program and make sure that there were no errors */
        glLinkProgram(_program);
        glGetProgramiv(_program, GL_LINK_STATUS, &result);
        if(result == GL_FALSE) {
            GLint length;
            char *log;
            
            /* get the program info log */
            glGetProgramiv(_program, GL_INFO_LOG_LENGTH, &length);
            log = (char *) malloc(length);
            glGetProgramInfoLog(_program, length, &result, log);
            
            /* print an error message and the info log */
            gldebugf("sceneInit(): Program linking failed: %s\n", log);
            free(log);
            
            /* delete the program */
            glDeleteProgram(_program);
            _program = 0;
        }
    }

    void bind_attrib(unsigned int index, char const *name) {
        glBindAttribLocation(_program, index, name);
    }

    bool is_valid() {
        glValidateProgram(_program);
        int params = -1;
        glGetProgramiv(_program, GL_VALIDATE_STATUS, &params);
        //char value[32];
        if (GL_TRUE != params) {
            gldebugf("program %i GL_VALIDATE_STATUS = GL_FALSE", _program);
            _print_programme_info_log();
            return false;
        }
        gldebugf("program %i GL_VALIDATE_STATUS = GL_TRUE", _program);
        return true;
    }

    /*
     * Returns a string containing the text in
     * a vertex/fragment shader source file.
     */
    static char *load_source(const char *filePath) {
        const size_t blockSize = 512;
        FILE *fp;
        char buf[blockSize];
        char *source = NULL;
        size_t tmp, sourceLength = 0;

        /* open file */
        fp = fopen(filePath, "r");
        if(!fp) {
            gldebugf("load_source(): Unable to open %s for reading", filePath);
            return NULL;
        }

        /* read the entire file into a string */
        while((tmp = fread(buf, 1, blockSize, fp)) > 0) {
            char *newSource = (char *) malloc(sourceLength + tmp + 1);
            if(!newSource) {
                gldebug("load_source(): malloc failed");
                if(source)
                    free(source);
                return NULL;
            }

            if(source) {
	      std::memcpy(newSource, source, sourceLength);
                free(source);
            }
	    std::memcpy(newSource + sourceLength, buf, tmp);

            source = newSource;
            sourceLength += tmp;
        }

        /* close the file and null terminate the string */
        fclose(fp);
        if(source)
            source[sourceLength] = '\0';

        return source;
    }

    /*
     * Returns a shader object containing a shader
     * compiled from the given GLSL shader file.
     */
    static GLuint compile_from_file(GLenum type, const char *filePath) {
        char *source;
        GLuint shader;
        GLint length, result;

        /* get shader source */
        source = load_source(filePath);
        if(!source)
            return 0;

        /* create shader object, set the source, and compile */
        shader = glCreateShader(type);
        length = strlen(source);
        glShaderSource(shader, 1, (const char **)&source, &length);
        glCompileShader(shader);
        free(source);

        /* make sure the compilation was successful */
        glGetShaderiv(shader, GL_COMPILE_STATUS, &result);
        if(result == GL_FALSE) {
            char *log;

            /* get the shader info log */
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &length);
            log = (char *) malloc(length);
            glGetShaderInfoLog(shader, length, &result, log);

            /* print an error message and the info log */
            gldebugf("compile_from_file(): Unable to compile %s: %s", filePath, log);
            free(log);

            glDeleteShader(shader);
            return 0;
        }

        return shader;
    }

    void print_info() {
        gldebugf("--------------------\nshader programme %i info:", _program);
        int params = -1;
        glGetProgramiv(_program, GL_LINK_STATUS, &params);
        char value[32];
        if (GL_TRUE == params) {
            strcpy(value, "GL_TRUE");
        } else {
            strcpy(value, "GL_FALSE");
        }
        gldebugf("GL_LINK_STATUS = %s", value);
  
        /*
        glGetProgramiv(_program, GL_ATTACHED_SHADERS, &params);
         gldebugf("GL_ATTACHED_SHADERS = %i\n", params);
         if (m_has_vertex_shader) {
             gldebugf("  vertex shader index %i. file name: %s\n", m_vertex_shader_idx, m_vertex_shader_file_name);
         }
         if (m_has_fragment_shader) {
             gldebugf("  fragment shader index %i. file name: %s\n", m_fragment_shader_idx, m_fragment_shader_file_name);
         }
        */

        glGetProgramiv(_program, GL_ACTIVE_ATTRIBUTES, &params);
        gldebugf("GL_ACTIVE_ATTRIBUTES = %i", params);
        for (int i = 0; i < params; i++) {
            char name[64];
            int max_length = 64;
            int actual_length = 0;
            int size = 0;
            GLenum type;
            //char type_name[64];
            glGetActiveAttrib(_program, i, max_length, &actual_length, &size, &type, name);
            if (size > 1) {
                for (int j = 0; j < size; j++) {
                    char long_name[64];
                    sprintf(long_name, "%s[%i]", name, j);
                    int location = glGetAttribLocation(_program, long_name);
                    gldebugf("  %i) type:%s name:%s location:%i", i, GL_type_to_string(type), long_name, location);
                }
            } else {
                int location = glGetAttribLocation(_program, name);
                gldebugf("  %i) type:%s name:%s location:%i", i, GL_type_to_string(type), name, location);
            }
        }
  
        glGetProgramiv(_program, GL_ACTIVE_UNIFORMS, &params);
        gldebugf("GL_ACTIVE_UNIFORMS = %i", params);
        for (int i = 0; i < params; i++) {
            char name[64];
            int max_length = 64;
            int actual_length = 0;
            int size = 0;
            GLenum type;
            //char type_name[64];
            glGetActiveUniform(_program, i, max_length, &actual_length, &size, &type, name);
            if (size > 1) {
                for (int j = 0; j < size; j++) {
                    char long_name[64];
                    sprintf(long_name, "%s[%i]", name, j);
                    int location = glGetUniformLocation(_program, long_name);
                    gldebugf("  %i) type:%s name:%s location:%i", i, GL_type_to_string(type), long_name, location);
                }
            } else {
                int location = glGetUniformLocation(_program, name);
                gldebugf("  %i) type:%s name:%s location:%i", i, GL_type_to_string(type), name, location);
            }
        }
  
        _print_programme_info_log();
    }

    void _print_programme_info_log() {
        int max_length = 2048;
        int actual_length = 0;
        char log[2048];
        glGetProgramInfoLog(_program, max_length, &actual_length, log);
        gldebugf("program info log for GL index %i:\n%s", _program, log);
    }

protected:
    unsigned int _program;
    bool _loaded;
};

struct FlatShader : public ShaderProgram {
    FlatShader(std::string base) 
        : ShaderProgram(base, "flat")
    {
    }

    virtual bool requires_positions() { return true; }
    virtual bool requires_colors() { return false; }
    virtual bool requires_normals() { return false; }
    virtual bool requires_texcoords() { return false; }
};

struct SpectrumShader : public ShaderProgram {
    SpectrumShader(std::string base) 
        : ShaderProgram(base, "spectrum")
    {
    }

    virtual bool requires_positions() { return true; }
    virtual bool requires_colors() { return true; }
    virtual bool requires_normals() { return false; }
    virtual bool requires_texcoords() { return false; }
};

struct LandscapeShader : public ShaderProgram {
    LandscapeShader(std::string base) 
        : ShaderProgram(base, "landscape")
    {
    }

    virtual bool requires_positions() { return true; }
    virtual bool requires_colors() { return false; }
    virtual bool requires_normals() { return false; }
    virtual bool requires_texcoords() { return true; }
};

struct PhongShader : public ShaderProgram {
    PhongShader(std::string base) 
        : ShaderProgram(base, "phong")
    {
    }

    virtual bool requires_positions() { return true; }
    virtual bool requires_colors() { return false; }
    virtual bool requires_normals() { return true; }
    virtual bool requires_texcoords() { return true; }
};

enum ShaderEnum { NOSHADER, FLAT, SPECTRUM, LANDSCAPE, PHONG };

class ShaderFactory {
public:
    ShaderFactory() {
    }

    ShaderProgram *get(ShaderEnum key, std::string base=std::string()) {
        if (key == NOSHADER) 
            return NULL;

        auto it = _shaders.find(key);
        if (it != _shaders.end()) {
            return it->second;
        }

        switch (key) {
        case FLAT: 
            _shaders.insert(std::make_pair(FLAT, new FlatShader(base)));
            break;
        case SPECTRUM: 
            _shaders.insert(std::make_pair(SPECTRUM, new SpectrumShader(base)));
            break;
        case LANDSCAPE:
            _shaders.insert(std::make_pair(LANDSCAPE, new LandscapeShader(base)));
            break;
        case PHONG:
            _shaders.insert(std::make_pair(PHONG, new PhongShader(base)));
            break;
        case NOSHADER:
            break;
        }

        return _shaders[key];
    }

private:
    std::map<ShaderEnum, ShaderProgram *> _shaders;
};

static ShaderFactory shader_factory;


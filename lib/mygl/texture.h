#pragma once

#include "mygl.h"

#include <SOIL.h>
//#include <png.h>
#include <string>
//#include <vector>
//#include <boost/unordered_map.hpp>

#define TEXTURE_LOAD_ERROR 0

//using namespace std;
using std::string;
using std::vector;

class Texture {
public:
    Texture(string _filename="") 
        : filename(_filename)
        , width(0)
        , height(0)
        , texture_id(0)
        , image_data(NULL) 
    { 
    }
        
    virtual ~Texture() {
        if (image_data != NULL)
            delete [] image_data;
    }

    virtual bool load() = 0;

    int getWidth() { return width; }
    int getHeight() { return height; }
    int getTextureID() { return texture_id; }

protected:
    string filename;
    int width, height;
    GLuint texture_id;
    unsigned char *image_data;
};

/*
class PNGTexture : public Texture {
public:
    PNGTexture(string filename="") : Texture(filename) {};
    bool load();

    // Not sure what this should do, figure out later
    ~PNGTexture() {}

    void bind(bool activate=true, bool deactivate=true) {
        //if (activate) glEnable(GL_TEXTURE_2D);
        glBindTexture(GL_TEXTURE_2D, getTextureID());    
        //if (deactivate) glDisable(GL_TEXTURE_2D);
    }

};
*/

class SOILTexture : public Texture {
public:
    SOILTexture(string filename="") : Texture(filename) {};

    bool load() {
        fprintf(stderr, "Loading texture '%s'\n", filename.c_str());

        /* load an image file directly as a new OpenGL texture */
        texture_id = SOIL_load_OGL_texture(
            filename.c_str(),
            SOIL_LOAD_AUTO,
            SOIL_CREATE_NEW_ID,
            //SOIL_FLAG_MIPMAPS | SOIL_FLAG_COMPRESS_TO_DXT
            SOIL_FLAG_INVERT_Y | SOIL_FLAG_NTSC_SAFE_RGB 
            );
        
        /* check for an error during the load process */
        if (0 == texture_id) {
            printf( "SOIL loading error: '%s'\n", SOIL_last_result() );
            return false;
        }

        return true;

    }
    
    // Not sure what this should do, figure out later
    ~SOILTexture() {}

    void bind(bool activate=true, bool deactivate=true) {
        if (activate) glEnable(GL_TEXTURE_2D);
        glBindTexture(GL_TEXTURE_2D, getTextureID());    
        if (deactivate) glDisable(GL_TEXTURE_2D);
    }
};





